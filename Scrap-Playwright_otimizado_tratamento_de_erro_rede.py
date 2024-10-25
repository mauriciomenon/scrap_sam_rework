from playwright.sync_api import sync_playwright, Page, Response, ConsoleMessage, Dialog
import os
from datetime import datetime
import time
from typing import Dict, Optional, List, Union
import logging
import json
from dataclasses import dataclass
from enum import Enum
import traceback

class ErrorSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class NetworkError:
    timestamp: str
    url: str
    status: int
    method: str
    error_type: str
    details: str
    severity: ErrorSeverity

@dataclass
class ConsoleError:
    timestamp: str
    type: str
    text: str
    location: str
    stack_trace: Optional[str]
    severity: ErrorSeverity

class ErrorTracker:
    """Sistema de monitoramento e tratamento de erros."""
    def __init__(self, page: Page):
        self.page = page
        self.network_errors: List[NetworkError] = []
        self.console_errors: List[ConsoleError] = []
        self.setup_logging()
        self.setup_error_handlers()

    def setup_logging(self):
        """Configura o sistema de logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('error_tracking.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ErrorTracker')

    def setup_error_handlers(self):
        """Configura os handlers de erro para a página."""
        self.page.on("response", self.handle_response)
        self.page.on("console", self.handle_console_message)
        self.page.on("pageerror", self.handle_page_error)
        self.page.on("dialog", self.handle_dialog)
        self.page.on("requestfailed", self.handle_request_failed)

    def handle_response(self, response: Response):
        """Processa respostas HTTP."""
        status = response.status
        url = response.url
        severity = self.get_http_severity(status)

        if status >= 400:
            error = NetworkError(
                timestamp=datetime.now().isoformat(),
                url=url,
                status=status,
                method=response.request.method,
                error_type=f"HTTP_{status}",
                details=self.get_status_description(status),
                severity=severity
            )
            self.network_errors.append(error)
            self.log_error(error)
            self.handle_specific_http_error(status, url)

    def handle_console_message(self, msg: ConsoleMessage):
        """Processa mensagens do console."""
        if msg.type in ['error', 'warning']:
            severity = ErrorSeverity.ERROR if msg.type == 'error' else ErrorSeverity.WARNING
            error = ConsoleError(
                timestamp=datetime.now().isoformat(),
                type=msg.type,
                text=msg.text,
                location=msg.location['url'] if msg.location else 'Unknown',
                stack_trace=self.get_stack_trace(msg),
                severity=severity
            )
            self.console_errors.append(error)
            self.log_error(error)

    def handle_specific_http_error(self, status: int, url: str):
        """Implementa ações específicas para diferentes códigos HTTP."""
        retry_statuses = [408, 429, 500, 502, 503, 504]
        max_retries = 3

        if status in retry_statuses:
            for attempt in range(max_retries):
                self.logger.warning(f"Tentativa {attempt + 1} de {max_retries} para URL: {url}")
                try:
                    # Espera exponencial entre tentativas
                    wait_time = (2 ** attempt) * 1000  # ms
                    self.page.wait_for_timeout(wait_time)

                    # Tenta recarregar a página
                    if url == self.page.url:
                        self.page.reload()
                    return
                except Exception as e:
                    self.logger.error(f"Erro na tentativa {attempt + 1}: {e}")

            self.logger.critical(f"Todas as tentativas falharam para URL: {url}")

    def handle_page_error(self, error):
        """Processa erros não capturados da página."""
        self.logger.error(f"Erro não capturado na página: {error}")

    def handle_dialog(self, dialog: Dialog):
        """Processa diálogos inesperados."""
        self.logger.warning(f"Diálogo detectado: {dialog.message}")
        if dialog.type in ['alert', 'confirm']:
            dialog.accept()
        elif dialog.type == 'prompt':
            dialog.dismiss()

    def handle_request_failed(self, request):
        """Processa requisições que falharam."""
        try:
            # Verifica se request é um objeto ou string
            if hasattr(request, "failure") and callable(request.failure):
                error = request.failure()
            else:
                error = str(request)  # Se for string, usa diretamente

            url = request.url if hasattr(request, "url") else "URL desconhecida"
            method = request.method if hasattr(request, "method") else "unknown"

            self.logger.error(f"Requisição falhou: {url}\nErro: {error}")

            # Registra erro na lista de network_errors
            error_entry = NetworkError(
                timestamp=datetime.now().isoformat(),
                url=url,
                status=0,  # Código 0 para falhas de rede
                method=method,
                error_type="REQUEST_FAILED",
                details=str(error),
                severity=ErrorSeverity.ERROR,
            )
            self.network_errors.append(error_entry)

        except Exception as e:
            self.logger.error(
                f"Erro ao processar falha de requisição: {e}\n{traceback.format_exc()}"
            )

    def get_http_severity(self, status: int) -> ErrorSeverity:
        """Determina a severidade baseada no código HTTP."""
        if status < 400:
            return ErrorSeverity.INFO
        elif status < 500:
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR

    def get_status_description(self, status: int) -> str:
        """Retorna descrição para códigos HTTP comuns."""
        descriptions = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            408: "Request Timeout",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return descriptions.get(status, f"Unknown Status: {status}")

    def get_stack_trace(self, msg: ConsoleMessage) -> Optional[str]:
        """Extrai stack trace de mensagens de console quando disponível."""
        try:
            if hasattr(msg, 'stack'):
                return msg.stack
            return None
        except:
            return None

    def log_error(self, error: Union[NetworkError, ConsoleError]):
        """Registra erros no log com formato apropriado."""
        if isinstance(error, NetworkError):
            self.logger.error(
                f"Network Error: {error.error_type} - {error.url} - Status: {error.status}"
            )
        else:
            self.logger.error(
                f"Console Error: {error.type} - {error.text} - Location: {error.location}"
            )

    def get_error_summary(self) -> Dict:
        """Gera um resumo dos erros encontrados."""
        return {
            "network_errors": len(self.network_errors),
            "console_errors": len(self.console_errors),
            "error_types": {
                "http_4xx": len([e for e in self.network_errors if 400 <= e.status < 500]),
                "http_5xx": len([e for e in self.network_errors if e.status >= 500]),
                "console_errors": len([e for e in self.console_errors if e.type == 'error']),
                "console_warnings": len([e for e in self.console_errors if e.type == 'warning'])
            }
        }

    def save_error_report(self, filename: str = "error_report.json"):
        """Salva um relatório detalhado dos erros em formato JSON."""

        def convert_error_to_dict(error):
            """Converte um erro em dicionário serializável."""
            error_dict = vars(error).copy()
            if "severity" in error_dict:
                error_dict["severity"] = error_dict[
                    "severity"
                ].value  # Converte Enum para string
            return error_dict

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_error_summary(),
            "network_errors": [
                convert_error_to_dict(error) for error in self.network_errors
            ],
            "console_errors": [
                convert_error_to_dict(error) for error in self.console_errors
            ],
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


    def print_error_summary(self):
        """Imprime um resumo detalhado dos erros."""
        # Combina todos os erros para análise
        all_errors = self.network_errors + self.console_errors

        # Realiza análise detalhada
        analyzer = ErrorAnalyzer()
        analysis = analyzer.analyze_errors(all_errors)

        # Imprime relatório formatado
        analyzer.print_analysis_report(analysis)

        # Salva análise detalhada junto com o relatório
        self.last_analysis = analysis  # para uso posterior se necessário


class SAMLocators:
    """Centraliza todos os seletores utilizados na aplicação."""

    LOGIN = {
        "username": "[name*='wtUsername'][name*='wtUserNameInput']",
        "password": "[name*='wtPassword'][name*='wtPasswordInput']",
        "submit": "[name*='wtAction'][type='submit']",
    }

    NAVIGATION = {
        "manutencao": "text=Manutenção Aperiódica",
        "relatorios": "text=Relatórios",
        "pendentes": "xpath=//a[text()='Pendentes']",
    }

    FILTER = {
        "setor_executor": "[id*='SectorExecutor']",
        "search_button": "a[id*='SearchButton']",
    }

    REPORT = {
        "detailed_report": "text=Relatório com Detalhes",
        "loading_bar": "#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wt31_OutSystemsUIWeb_wt2_block_RichWidgets_wt15_block_wtdivWait",
        "export_menu": "//div[contains(@id,'wtMenuDropdown')]//i",
        "export_excel": "text=Exportar para Excel",
    }

    CHECKBOXES = {
        "info_basica": "input[id*='ctl00'][id*='wtContent']",
        "programacao": "input[id*='ctl04'][id*='wtContent']",
        "documentos": "input[id*='ctl08'][id*='wtContent']",
        "planejamento": "input[id*='ctl02'][id*='wtContent']",
        "execucao": "input[id*='ctl06'][id*='wtContent']",
        "derivadas": "input[id*='ctl10'][id*='wtContent']",
        "apr": "input[id*='ctl12'][id*='wtContent']",
    }

class SAMNavigator:
    def __init__(self, page: Page):
        self.page = page
        self.locators = SAMLocators()
        self.download_path = os.path.join(os.getcwd(), "Downloads")
        os.makedirs(self.download_path, exist_ok=True)
        self.error_tracker = ErrorTracker(page)

    def _safe_action(
        self, action_fn, error_msg: str, screenshot_name: Optional[str] = None,
        retry_count: int = 3
    ):
        """Wrapper para executar ações com tratamento de erro padronizado."""
        for attempt in range(retry_count):
            try:
                return action_fn()
            except Exception as e:
                self.error_tracker.logger.error(
                    f"Tentativa {attempt + 1}/{retry_count}: {error_msg}: {e}\n{traceback.format_exc()}"
                )
                if screenshot_name:
                    self.page.screenshot(path=f"{screenshot_name}_{attempt}.png")

                if attempt == retry_count - 1:
                    raise

                # Espera exponencial entre tentativas
                wait_time = (2 ** attempt) * 1000
                self.page.wait_for_timeout(wait_time)

    def login(self, username: str, password: str):
        def _do_login():
            self.page.goto("https://apps.itaipu.gov.br/SAM/NoPermission.aspx")
            self.page.fill(self.locators.LOGIN["username"], username)
            self.page.fill(self.locators.LOGIN["password"], password)
            self.page.click(self.locators.LOGIN["submit"])
            print("Login realizado com sucesso.")

        self._safe_action(_do_login, "Erro no login", "login_error")

    def navigate_to_filter_page(self):
        def _do_navigation():
            self.page.click(self.locators.NAVIGATION["manutencao"])
            self.page.click(self.locators.NAVIGATION["relatorios"])
            self.page.click(self.locators.NAVIGATION["pendentes"])
            print("Página de filtro acessada.")

        self._safe_action(_do_navigation, "Erro na navegação", "navigation_error")

    def wait_for_filter_field(self):
        """Aguarda o campo 'Setor Executor' com retry."""
        def _wait_for_field():
            self.page.wait_for_selector(
                self.locators.FILTER["setor_executor"],
                state="visible",
                timeout=20000,
            )
            print("Campo 'Setor Executor' encontrado.")
            return True

        return self._safe_action(
            _wait_for_field,
            "Erro ao localizar campo 'Setor Executor'",
            "filter_field_error"
        )

    def fill_filter(self, executor_setor_value: str):
        def _do_fill():
            input_selector = self.locators.FILTER["setor_executor"]
            self.page.wait_for_selector(input_selector, state="visible")
            self.page.fill(input_selector, executor_setor_value)

            actual_value = self.page.evaluate(
                """(selector) => {
                    return document.querySelector(selector).value;
                }""",
                input_selector,
            )

            if actual_value != executor_setor_value:
                raise ValueError(
                    f"Valor preenchido ({actual_value}) diferente do esperado ({executor_setor_value})"
                )

            print(f"Filtro preenchido com: {executor_setor_value}")

        self._safe_action(_do_fill, "Erro ao preencher filtro", "fill_filter_error")

    def wait_for_loading_complete(
        self, timeout: int = 60000, after_checkboxes: bool = False
    ):
        """Aguarda carregamento da página com verificação adaptativa."""
        try:
            print("Verificando estado da página...")
            start_time = time.time()
            consecutive_success = 0

            while (time.time() - start_time) < (timeout / 1000):
                # Verificação específica pós-checkboxes
                if after_checkboxes:
                    loading_complete = self.page.evaluate(
                        """
                            () => {
                                // Para checkboxes, focamos apenas na barra principal
                                const loadingBar = document.querySelector('[id*="wtdivWait"]');
                                if (loadingBar && window.getComputedStyle(loadingBar).display !== 'none') {
                                    return false;
                                }
                                return true;
                            }
                        """
                    )
                else:
                    # Verificação completa normal
                    loading_complete = self.page.evaluate(
                        """
                            () => {
                                const loadingBar = document.querySelector('[id*="wtdivWait"]');
                                if (loadingBar && window.getComputedStyle(loadingBar).display !== 'none') {
                                    return false;
                                }
                                
                                const loadingIndicators = document.querySelectorAll(
                                    '.loading-indicator, .loading, [class*="loading"], .progress, .spinner'
                                );
                                for (const indicator of loadingIndicators) {
                                    if (window.getComputedStyle(indicator).display !== 'none') {
                                        return false;
                                    }
                                }
                                
                                const osAjaxElements = document.querySelectorAll('[id*="AjaxWait"]');
                                for (const element of osAjaxElements) {
                                    if (window.getComputedStyle(element).display !== 'none') {
                                        return false;
                                    }
                                }
                                
                                return true;
                            }
                        """
                    )

                if loading_complete:
                    consecutive_success += 1
                    print(f"Verificação bem-sucedida ({consecutive_success}/3)")

                    # Após checkboxes, precisamos de menos confirmações
                    required_success = 2 if after_checkboxes else 3

                    if consecutive_success >= required_success:
                        self.page.wait_for_load_state("networkidle", timeout=5000)
                        self.page.wait_for_timeout(2000)
                        print(
                            "Carregamento completo confirmado após verificações consecutivas"
                        )
                        return True
                else:
                    if consecutive_success > 0:
                        print(
                            "Resetando contador de verificações - loading detectado novamente"
                        )
                    consecutive_success = 0

                self.page.wait_for_timeout(2000)
                if consecutive_success == 0:
                    print("Ainda carregando... aguardando")

            print("Timeout ao aguardar carregamento")
            return False

        except Exception as e:
            print(f"Erro ao aguardar carregamento: {e}")
            return False

    def click_search(self):
        """Clica no botão de pesquisa e aguarda o carregamento."""

        def _do_search():
            search_button = self.locators.FILTER["search_button"]
            self.page.wait_for_selector(search_button, state="visible")
            self.page.click(search_button)
            self.wait_for_loading_complete()
            print("Pesquisa realizada com sucesso.")

        self._safe_action(_do_search, "Erro ao realizar pesquisa", "search_error")

    def select_report_options(self):
        """Seleciona opções do relatório e faz a exportação."""
        try:
            print("Selecionando 'Relatório com Detalhes'...")
            self.page.click("text=Relatório com Detalhes")

            print("Aguardando elementos carregarem...")
            self.page.wait_for_timeout(2000)
            self.page.wait_for_selector(
                "input[id*='ctl00'][id*='wtContent']", state="visible", timeout=10000
            )

            if not self.wait_for_loading_complete(timeout=90000):
                raise Exception(
                    "Timeout aguardando carregamento após selecionar relatório detalhado"
                )

            # Mantido o JavaScript original dos checkboxes (sem alteração)
            success = self.page.evaluate(
                """() => {
                    try {
                        const checkboxesToCheck = ['ctl00', 'ctl04', 'ctl08', 'ctl02', 'ctl06', 'ctl10'];
                        const checkboxesToUncheck = ['ctl12'];
                        
                        const triggerEvents = (element) => {
                            const events = ['change', 'click', 'input'];
                            events.forEach(eventType => {
                                const event = new Event(eventType, { bubbles: true, cancelable: true });
                                element.dispatchEvent(event);
                            });
                        };
                        
                        const handleCheckboxes = (idList, checked) => {
                            idList.forEach(id => {
                                const checkbox = document.querySelector(`input[id*='${id}'][id*='wtContent']`);
                                if (checkbox) {
                                    checkbox.checked = false;
                                    triggerEvents(checkbox);
                                    
                                    if (checked) {
                                        setTimeout(() => {
                                            checkbox.checked = true;
                                            triggerEvents(checkbox);
                                        }, 100);
                                    }
                                }
                            });
                        };
                        
                        handleCheckboxes([...checkboxesToCheck, ...checkboxesToUncheck], false);
                        
                        setTimeout(() => {
                            handleCheckboxes(checkboxesToCheck, true);
                        }, 200);
                        
                        return true;
                    } catch (error) {
                        console.error('Erro ao selecionar checkboxes:', error);
                        return false;
                    }
                }"""
            )

            if not success:
                raise Exception("Falha ao selecionar opções via JavaScript")

            self.page.wait_for_timeout(1000)

            # Espera completa após os checkboxes
            print("Aguardando carregamento completo após configurar checkboxes...")
            max_attempts = 5
            for attempt in range(max_attempts):
                if self.wait_for_loading_complete(timeout=90000):
                    print(
                        "Carregamento completo confirmado, prosseguindo com exportação..."
                    )
                    break
                print(
                    f"Tentativa {attempt + 1}/{max_attempts} de verificar carregamento..."
                )
                self.page.wait_for_timeout(5000)
            else:
                raise Exception(
                    "Não foi possível confirmar carregamento completo após checkboxes"
                )

            print("Todas as opções do relatório foram configuradas corretamente.")

            # Executa a exportação e retorna seu resultado
            return self.export_to_excel()

        except Exception as e:
            print(f"Erro ao configurar opções do relatório: {e}")
            self.page.screenshot(path="report_options_error.png")
            return False

    def verify_selections(self):
        """Verifica se todas as opções foram selecionadas corretamente."""
        for name, selector in self.locators.CHECKBOXES.items():
            if name != "apr":  # Não verificamos APR pois deve estar desmarcado
                try:
                    is_checked = self.page.evaluate(
                        """(selector) => {
                            const element = document.querySelector(selector);
                            return element ? element.checked : false;
                        }""",
                        selector,
                    )

                    if not is_checked:
                        raise ValueError(
                            f"Checkbox '{name}' não está selecionado como esperado"
                        )

                except Exception as e:
                    print(f"Erro ao verificar seleção de '{name}': {e}")
                    raise

    def export_to_excel(self):
        """Exporta o relatório para Excel com clique otimizado."""
        try:
            print("Iniciando processo de exportação...")

            # Primeira espera
            print("Aguardando estabilização inicial da página...")
            self.page.wait_for_timeout(3000)

            # Configura timeout maior para esta operação
            self.page.set_default_timeout(90000)

            try:
                print("Tentando exportação via clique direto...")
                with self.page.expect_download(timeout=90000) as download_promise:
                    # Verifica e clica no menu com retry
                    success = self.page.evaluate(
                        """
                        () => {
                            return new Promise((resolve) => {
                                // Função para encontrar e clicar no botão do menu
                                const clickMenuButton = () => {
                                    const menuButton = document.querySelector('[id*="wtMenuDropdown"] i');
                                    if (menuButton && window.getComputedStyle(menuButton.parentElement).display !== 'none') {
                                        // Força o menu a ficar visível
                                        const menuContainer = menuButton.closest('[id*="wtMenuDropdown"]');
                                        if (menuContainer) {
                                            menuContainer.style.display = 'block';
                                            menuContainer.style.visibility = 'visible';
                                        }
                                        menuButton.click();
                                        return true;
                                    }
                                    return false;
                                };

                                // Tenta clicar algumas vezes
                                let attempts = 0;
                                const tryClick = () => {
                                    if (attempts >= 5) {
                                        resolve(false);
                                        return;
                                    }
                                    if (clickMenuButton()) {
                                        resolve(true);
                                    } else {
                                        attempts++;
                                        setTimeout(tryClick, 1000);
                                    }
                                };
                                
                                tryClick();
                            });
                        }
                    """
                    )

                    if not success:
                        raise Exception("Não foi possível clicar no menu")

                    # Espera o menu aparecer
                    print("Aguardando menu de exportação...")
                    self.page.wait_for_timeout(2000)

                    # Verifica se o botão de exportar está visível e clicável
                    button_ready = self.page.evaluate(
                        """
                        () => {
                            const exportLinks = Array.from(document.querySelectorAll('a'))
                                .filter(a => a.textContent.includes('Exportar para Excel'));
                            
                            const isVisible = (element) => {
                                if (!element) return false;
                                const rect = element.getBoundingClientRect();
                                const style = window.getComputedStyle(element);
                                return rect.width > 0 && 
                                    rect.height > 0 && 
                                    style.display !== 'none' && 
                                    style.visibility !== 'hidden' &&
                                    element.offsetParent !== null;
                            };
                            
                            const visibleButton = exportLinks.find(isVisible);
                            if (visibleButton) {
                                // Força o botão a ficar visível e clicável
                                visibleButton.style.display = 'block';
                                visibleButton.style.visibility = 'visible';
                                visibleButton.style.opacity = '1';
                                visibleButton.style.pointerEvents = 'auto';
                                return true;
                            }
                            return false;
                        }
                    """
                    )

                    if not button_ready:
                        raise Exception("Botão de exportação não está pronto")

                    # Espera final antes do clique
                    print("Aguardando botão estabilizar...")
                    self.page.wait_for_timeout(1000)

                    # Clique via JavaScript para garantir
                    print("Clicando no botão de exportação...")
                    success = self.page.evaluate(
                        """
                        () => {
                            const exportButton = Array.from(document.querySelectorAll('a'))
                                .find(a => a.textContent.includes('Exportar para Excel'));
                            if (exportButton) {
                                exportButton.click();
                                return true;
                            }
                            return false;
                        }
                    """
                    )

                    if not success:
                        raise Exception("Falha ao clicar no botão de exportação")

                    print("Aguardando download iniciar...")
                    download = download_promise.value
                    download_file_path = os.path.join(
                        self.download_path, download.suggested_filename
                    )
                    download.save_as(download_file_path)
                    print(f"Download concluído: {download_file_path}")
                    return True

            except Exception as click_e:
                print(f"Erro no método de clique: {click_e}")
                self.page.screenshot(path="click_error.png")

                # Fallback para o método JavaScript anterior
                print("Tentando método alternativo de JavaScript...")
                return self._export_via_javascript()

        except Exception as e:
            print(f"Erro geral ao exportar o relatório: {e}")
            self.page.screenshot(path="general_error.png")
            return False

        finally:
            self.page.set_default_timeout(30000)

    def _export_via_javascript(self):
        """Método JavaScript de fallback para exportação."""
        try:
            with self.page.expect_download(timeout=90000) as download_promise:
                success = self.page.evaluate(
                    """
                    () => {
                        return new Promise((resolve) => {
                            const attemptExport = (attempt = 0) => {
                                if (attempt >= 5) {
                                    resolve(false);
                                    return;
                                }
                                
                                const menu = document.querySelector('[id*="wtMenuDropdown"]');
                                if (menu) {
                                    menu.style.display = 'block';
                                    menu.style.visibility = 'visible';
                                }
                                
                                const links = Array.from(document.querySelectorAll('a'));
                                const exportButton = links.find(link => 
                                    link.textContent.includes('Exportar para Excel')
                                );
                                
                                if (exportButton) {
                                    exportButton.click();
                                    resolve(true);
                                } else {
                                    setTimeout(() => attemptExport(attempt + 1), 1000);
                                }
                            };
                            
                            attemptExport();
                        });
                    }
                """
                )

                if success:
                    download = download_promise.value
                    download_file_path = os.path.join(
                        self.download_path, download.suggested_filename
                    )
                    download.save_as(download_file_path)
                    print(f"Download via JavaScript concluído: {download_file_path}")
                    return True
                else:
                    print("JavaScript não conseguiu completar a exportação")
                    return False

        except Exception as js_e:
            print(f"Erro no método JavaScript: {js_e}")
            self.page.screenshot(path="js_error.png")
            return False


class ErrorAnalyzer:
    """Classe para análise detalhada de erros."""

    # Erros que podem ser ignorados com segurança
    IGNORABLE_ERRORS = {
        "urls": [
            "favicon.ico",
            "/CustomInputMasks/",  # máscaras de input que não afetam funcionalidade
        ],
        "messages": [
            "Failed to load resource",  # recursos não críticos
            "undefined is not a function",  # erros JS não críticos
        ],
    }

    # Erros que requerem atenção mas não são críticos
    WARNING_PATTERNS = {
        "urls": [
            "/api/",  # endpoints de API que podem ter retry
            "/static/",  # recursos estáticos que podem ter fallback
        ],
        "messages": [
            "timeout",
            "network error",
            "request failed",
        ],
    }

    # Erros que são considerados críticos
    CRITICAL_PATTERNS = {
        "urls": [
            "/auth/",  # problemas de autenticação
            "/export/",  # problemas na exportação
            "PendingGeneralSSAs",  # problemas no relatório principal
        ],
        "messages": [
            "Authorization failed",
            "Session expired",
            "Database error",
        ],
    }

    @staticmethod
    def categorize_error(error: Union[NetworkError, ConsoleError]) -> Dict:
        """Categoriza um erro com base em seus padrões e características."""
        url = getattr(error, "url", "")
        message = getattr(error, "text", "") or getattr(error, "details", "")

        # Verifica se é um erro ignorável
        for ignore_url in ErrorAnalyzer.IGNORABLE_ERRORS["urls"]:
            if ignore_url in url:
                return {
                    "category": "IGNORABLE",
                    "reason": f"URL ignorável: {ignore_url}",
                    "impact": "Nenhum impacto na funcionalidade",
                }

        for ignore_msg in ErrorAnalyzer.IGNORABLE_ERRORS["messages"]:
            if ignore_msg in message:
                return {
                    "category": "IGNORABLE",
                    "reason": f"Mensagem ignorável: {ignore_msg}",
                    "impact": "Nenhum impacto na funcionalidade",
                }

        # Verifica se é um erro crítico
        for critical_url in ErrorAnalyzer.CRITICAL_PATTERNS["urls"]:
            if critical_url in url:
                return {
                    "category": "CRITICAL",
                    "reason": f"URL crítica afetada: {critical_url}",
                    "impact": "Possível comprometimento de funcionalidade core",
                }

        for critical_msg in ErrorAnalyzer.CRITICAL_PATTERNS["messages"]:
            if critical_msg in message:
                return {
                    "category": "CRITICAL",
                    "reason": f"Erro crítico detectado: {critical_msg}",
                    "impact": "Funcionalidade core comprometida",
                }

        # Verifica se é um aviso
        for warning_url in ErrorAnalyzer.WARNING_PATTERNS["urls"]:
            if warning_url in url:
                return {
                    "category": "WARNING",
                    "reason": f"URL com potencial impacto: {warning_url}",
                    "impact": "Possível degradação de performance ou UX",
                }

        for warning_msg in ErrorAnalyzer.WARNING_PATTERNS["messages"]:
            if warning_msg in message:
                return {
                    "category": "WARNING",
                    "reason": f"Aviso detectado: {warning_msg}",
                    "impact": "Possível instabilidade",
                }

        # Se não se encaixar em nenhuma categoria específica
        return {
            "category": "UNKNOWN",
            "reason": "Erro não categorizado",
            "impact": "Impacto desconhecido",
        }

    @staticmethod
    def analyze_errors(errors: List[Union[NetworkError, ConsoleError]]) -> Dict:
        """Analisa uma lista de erros e gera um relatório detalhado."""
        analysis = {
            "total": len(errors),
            "by_category": {
                "CRITICAL": [],
                "WARNING": [],
                "IGNORABLE": [],
                "UNKNOWN": [],
            },
            "summary": {
                "critical_count": 0,
                "warning_count": 0,
                "ignorable_count": 0,
                "unknown_count": 0,
            },
            "recommendations": [],
        }

        for error in errors:
            categorization = ErrorAnalyzer.categorize_error(error)
            category = categorization["category"]

            error_info = {
                "timestamp": error.timestamp,
                "type": error.__class__.__name__,
                "details": str(error),
                "categorization": categorization,
            }

            analysis["by_category"][category].append(error_info)
            analysis["summary"][f"{category.lower()}_count"] += 1

        # Gera recomendações baseadas na análise
        if analysis["summary"]["critical_count"] > 0:
            analysis["recommendations"].append(
                {
                    "priority": "ALTA",
                    "action": "Investigar erros críticos imediatamente",
                    "details": f"Encontrados {analysis['summary']['critical_count']} erros críticos",
                }
            )

        if analysis["summary"]["warning_count"] > 3:
            analysis["recommendations"].append(
                {
                    "priority": "MÉDIA",
                    "action": "Monitorar warnings",
                    "details": "Volume elevado de warnings pode indicar instabilidade",
                }
            )

        # Adiciona métricas de saúde
        analysis["health_metrics"] = {
            "error_rate": len(errors) / 100,  # exemplo simples
            "critical_error_percentage": (
                (analysis["summary"]["critical_count"] / len(errors)) * 100
                if errors
                else 0
            ),
            "health_score": ErrorAnalyzer._calculate_health_score(analysis),
        }

        return analysis

    @staticmethod
    def _calculate_health_score(analysis: Dict) -> float:
        """Calcula uma pontuação de saúde baseada na análise de erros."""
        total = analysis["total"]
        if total == 0:
            return 100.0

        # Pesos para diferentes tipos de erro
        weights = {"critical": 1.0, "warning": 0.3, "unknown": 0.5, "ignorable": 0.1}

        # Calcula pontuação ponderada
        weighted_sum = (
            analysis["summary"]["critical_count"] * weights["critical"]
            + analysis["summary"]["warning_count"] * weights["warning"]
            + analysis["summary"]["unknown_count"] * weights["unknown"]
            + analysis["summary"]["ignorable_count"] * weights["ignorable"]
        )

        # Normaliza para 0-100, onde 100 é perfeito
        health_score = 100 * (1 - (weighted_sum / total))
        return round(max(0, min(100, health_score)), 2)

    @staticmethod
    def print_analysis_report(analysis: Dict):
        """Imprime um relatório formatado da análise de erros."""
        print("\n=== RELATÓRIO DE ANÁLISE DE ERROS ===")
        print(f"\nPontuação Ponderada: {analysis['health_metrics']['health_score']}%")
        print("\nResumo por Categoria:")
        print(f"- Críticos: {analysis['summary']['critical_count']}")
        print(f"- Avisos: {analysis['summary']['warning_count']}")
        print(f"- Ignoráveis: {analysis['summary']['ignorable_count']}")
        print(f"- Não categorizados: {analysis['summary']['unknown_count']}")

        if analysis["recommendations"]:
            print("\nRecomendações:")
            for rec in analysis["recommendations"]:
                print(f"[{rec['priority']}] {rec['action']}")
                print(f"  → {rec['details']}")

        if analysis["summary"]["critical_count"] > 0:
            print("\nDetalhes dos Erros Críticos:")
            for error in analysis["by_category"]["CRITICAL"]:
                print(f"- {error['timestamp']}: {error['details']}")
                print(f"  Impacto: {error['categorization']['impact']}")


def run(username: str, password: str, setor: str):
    """Função principal com parâmetros configuráveis e monitoramento de erros."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Configura monitoramento de recursos da página
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.set_default_timeout(30000)

        navigator = SAMNavigator(page)

        try:
            # Executa as operações principais
            navigator.login(username, password)
            navigator.navigate_to_filter_page()
            navigator.wait_for_filter_field()
            navigator.fill_filter(setor)
            navigator.click_search()

            if navigator.select_report_options():
                print("Relatório configurado com sucesso.")
            else:
                print("Falha na configuração do relatório")
                return

            # Agora usa o novo sistema de análise de erros
            navigator.error_tracker.print_error_summary()

            # Salva relatório detalhado
            navigator.error_tracker.save_error_report()

            input("Pressione Enter para fechar o navegador...")

        except Exception as e:
            print(f"Erro durante a execução: {e}")
            traceback.print_exc()

            # Mesmo com erro, tenta salvar o relatório de erros
            try:
                navigator.error_tracker.print_error_summary()  # Mostra análise mesmo com erro
                navigator.error_tracker.save_error_report("error_report_crash.json")
            except Exception as save_error:
                print(f"Não foi possível salvar o relatório de erros: {save_error}")

        finally:
            browser.close()


if __name__ == "__main__":
    run("menon", "Huffman81*", "IEE3")

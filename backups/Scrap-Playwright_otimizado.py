# ATENCAO: a exportacao do menu de relatorio simples gera um arquivo igual ao relatorio "completo" com detalhes
# e filtros habilitados. A unica diferenca e a apresentacao na tela dos dados. Trata-se de um codigo de
# aprendizado e logicamente selecionar somente esta opcao o tornara muito mais rapido.
# Objetivo: codigo generico reaproveitavel com tratamento de erro de requisicoes ao SAM
# Mauricio Menon, 25/10/2024

from playwright.sync_api import sync_playwright, Page
import os
from datetime import datetime
import time
from typing import Dict, Optional


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

    # Mantemos os IDs dos checkboxes exatamente como estavam
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

    def _safe_action(
        self, action_fn, error_msg: str, screenshot_name: Optional[str] = None
    ):
        """Wrapper para executar ações com tratamento de erro padronizado."""
        try:
            return action_fn()
        except Exception as e:
            print(f"{error_msg}: {e}")
            if screenshot_name:
                self.page.screenshot(path=f"{screenshot_name}.png")
            raise

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
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.page.wait_for_selector(
                    self.locators.FILTER["setor_executor"],
                    state="visible",
                    timeout=20000,
                )
                print("Campo 'Setor Executor' encontrado.")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Erro ao localizar campo 'Setor Executor': {e}")
                    self.page.screenshot(path="filter_field_error.png")
                    raise
                time.sleep(2)

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

    def click_search(self):
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
                raise Exception("Timeout aguardando carregamento após selecionar relatório detalhado")

            # Mantido o JavaScript original dos checkboxes (sem alteração)
            success = self.page.evaluate("""() => {
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
            }""")

            if not success:
                raise Exception("Falha ao selecionar opções via JavaScript")

            self.page.wait_for_timeout(1000)

            # Espera completa após os checkboxes
            print("Aguardando carregamento completo após configurar checkboxes...")
            max_attempts = 5
            for attempt in range(max_attempts):
                if self.wait_for_loading_complete(timeout=90000):
                    print("Carregamento completo confirmado, prosseguindo com exportação...")
                    break
                print(f"Tentativa {attempt + 1}/{max_attempts} de verificar carregamento...")
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

    def wait_for_loading_complete(self, timeout: int = 60000, after_checkboxes: bool = False):
        """Aguarda carregamento da página com verificação adaptativa."""
        try:
            print("Verificando estado da página...")
            start_time = time.time()
            consecutive_success = 0

            while (time.time() - start_time) < (timeout / 1000):
                # Verificação específica pós-checkboxes
                if after_checkboxes:
                    loading_complete = self.page.evaluate("""
                            () => {
                                // Para checkboxes, focamos apenas na barra principal
                                const loadingBar = document.querySelector('[id*="wtdivWait"]');
                                if (loadingBar && window.getComputedStyle(loadingBar).display !== 'none') {
                                    return false;
                                }
                                return true;
                            }
                        """)
                else:
                    # Verificação completa normal
                    loading_complete = self.page.evaluate("""
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
                        """)

                if loading_complete:
                    consecutive_success += 1
                    print(f"Verificação bem-sucedida ({consecutive_success}/3)")

                    # Após checkboxes, precisamos de menos confirmações
                    required_success = 2 if after_checkboxes else 3

                    if consecutive_success >= required_success:
                        self.page.wait_for_load_state("networkidle", timeout=5000)
                        self.page.wait_for_timeout(2000)
                        print("Carregamento completo confirmado após verificações consecutivas")
                        return True
                else:
                    if consecutive_success > 0:
                        print("Resetando contador de verificações - loading detectado novamente")
                    consecutive_success = 0

                self.page.wait_for_timeout(2000)
                if consecutive_success == 0:
                    print("Ainda carregando... aguardando")

            print("Timeout ao aguardar carregamento")
            return False

        except Exception as e:
            print(f"Erro ao aguardar carregamento: {e}")
            return False

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
                    success = self.page.evaluate("""
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
                    """)

                    if not success:
                        raise Exception("Não foi possível clicar no menu")

                    # Espera o menu aparecer
                    print("Aguardando menu de exportação...")
                    self.page.wait_for_timeout(2000)

                    # Verifica se o botão de exportar está visível e clicável
                    button_ready = self.page.evaluate("""
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
                    """)

                    if not button_ready:
                        raise Exception("Botão de exportação não está pronto")

                    # Espera final antes do clique
                    print("Aguardando botão estabilizar...")
                    self.page.wait_for_timeout(1000)

                    # Clique via JavaScript para garantir
                    print("Clicando no botão de exportação...")
                    success = self.page.evaluate("""
                        () => {
                            const exportButton = Array.from(document.querySelectorAll('a'))
                                .find(a => a.textContent.includes('Exportar para Excel'));
                            if (exportButton) {
                                exportButton.click();
                                return true;
                            }
                            return false;
                        }
                    """)

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
                success = self.page.evaluate("""
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
                """)

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


def run(username: str, password: str, setor: str):
    """Função principal com parâmetros configuráveis."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        navigator = SAMNavigator(page)

        try:
            navigator.login(username, password)
            navigator.navigate_to_filter_page()
            navigator.wait_for_filter_field()
            navigator.fill_filter(setor)
            navigator.click_search()

            # Alteramos para usar o retorno do select_report_options
            if navigator.select_report_options():
                print("Relatório configurado com sucesso.")
            else:
                print("Falha na configuração do relatório")
                return

            input("Pressione Enter para fechar o navegador...")

        finally:
            browser.close()


if __name__ == "__main__":
    run("menon", "Huffman87*", "IEE3")

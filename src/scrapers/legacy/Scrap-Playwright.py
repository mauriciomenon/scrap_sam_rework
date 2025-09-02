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


class SAMNavigator:
    def __init__(self, page):
        self.page = page

    def login(self, username, password):
        try:
            # Acesse a página de login
            self.page.goto("https://apps.itaipu.gov.br/SAM/NoPermission.aspx")

            # Preencher campos de login
            self.page.fill(
                "input[name='OutSystemsUIWeb_wt15$block$wtLogin$wt18$wtUsername$wtUserNameInput']",
                username,
            )
            self.page.fill(
                "input[name='OutSystemsUIWeb_wt15$block$wtLogin$wt18$wtPassword$wtPasswordInput']",
                password,
            )

            # Clicar no botão de login
            self.page.click(
                "input[name='OutSystemsUIWeb_wt15$block$wtLogin$wt18$wtAction$wt12']"
            )
            print("Login realizado com sucesso.")
        except Exception as e:
            print(f"Erro no login: {e}")

    def navigate_to_filter_page(self):
        """Navega até a página de filtro."""
        try:
            # Clique na opção "Manutenção Aperiódica"
            self.page.click("text=Manutenção Aperiódica")
            # Clique na aba "Relatórios" no menu à esquerda
            self.page.click("text=Relatórios")
            # Clique no link exato "Pendentes" para acessar a página de filtro
            self.page.click("xpath=//a[text()='Pendentes']")
            print("Página de filtro acessada.")
        except Exception as e:
            print(f"Erro ao navegar: {e}")

    def wait_for_filter_field(self):
        """Aguarda o campo 'Setor Executor' com retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.page.wait_for_selector(
                    "input[id*='SectorExecutor']", state="visible", timeout=20000
                )
                print("Campo 'Setor Executor' encontrado.")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Erro ao localizar campo 'Setor Executor': {e}")
                    self.page.screenshot(path="filter_field_error.png")
                    raise
                time.sleep(2)

    def fill_filter(self, executor_setor_value):
        """Preenche o filtro com verificação."""
        try:
            input_selector = "input[id*='SectorExecutor']"
            self.page.wait_for_selector(input_selector, state="visible")
            self.page.fill(input_selector, executor_setor_value)

            # Verificar se o valor foi preenchido corretamente
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

        except Exception as e:
            print(f"Erro ao preencher filtro: {e}")
            self.page.screenshot(path="fill_filter_error.png")
            raise

    def click_search(self):
        """Clica no botão de pesquisa com verificação de resultado."""
        try:
            search_button = "a[id*='SearchButton']"
            self.page.wait_for_selector(search_button, state="visible")
            self.page.click(search_button)

            # Aguardar resultado da pesquisa
            self.wait_for_loading_complete()
            print("Pesquisa realizada com sucesso.")

        except Exception as e:
            print(f"Erro ao realizar pesquisa: {e}")
            self.page.screenshot(path="search_error.png")
            raise

    '''
    # Metodo original que seleciona os 4 checkboxes, ja melhorou o antigo usava id
    # Outsystem manda uma requisicao para cada check entao mudar para JS
    def select_report_options(self):
        """Seleciona opções do relatório com verificação."""
        checkboxes = {
            "Informação Básica": "input[id*='ctl00'][id*='wtContent']",
            "Programação": "input[id*='ctl04'][id*='wtContent']",
            "Documentos": "input[id*='ctl08'][id*='wtContent']",
            "Planejamento": "input[id*='ctl02'][id*='wtContent']",
            "Execução": "input[id*='ctl06'][id*='wtContent']",
            "Derivadas": "input[id*='ctl10'][id*='wtContent']"
        }
        
        try:
            # Selecionar "Relatório com Detalhes"
            self.page.click("text=Relatório com Detalhes")
            
            # Selecionar cada checkbox
            for name, selector in checkboxes.items():
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.page.check(selector)
                    print(f"Opção '{name}' selecionada.")
                except Exception as e:
                    print(f"Erro ao selecionar '{name}': {e}")
                    raise
            
            # Garantir que APR está desmarcado
            apr_selector = "input[id*='ctl12'][id*='wtContent']"
            self.page.uncheck(apr_selector)
            
            # Verificar seleções
            self.verify_selections(checkboxes)
            print("Todas as opções do relatório foram configuradas corretamente.")
            
        except Exception as e:
            print(f"Erro ao configurar opções do relatório: {e}")
            self.page.screenshot(path="report_options_error.png")
            raise       
    '''


    def select_report_options(self):
        """Seleciona opções do relatório usando JavaScript e força uma atualização final."""
        try:
            print("Selecionando 'Relatório com Detalhes'...")
            self.page.click("text=Relatório com Detalhes")

            print("Aguardando elementos carregarem...")
            self.page.wait_for_timeout(2000)
            self.page.wait_for_selector(
                "input[id*='ctl00'][id*='wtContent']", state="visible", timeout=10000
            )
            self.wait_for_loading_complete()

            # JavaScript modificado para incluir eventos necessários
            success = self.page.evaluate(
                """() => {
                try {
                    const checkboxesToCheck = ['ctl00', 'ctl04', 'ctl08', 'ctl02', 'ctl06', 'ctl10'];
                    const checkboxesToUncheck = ['ctl12'];
                    
                    const triggerEvents = (element) => {
                        // Eventos que o sistema espera quando um checkbox é alterado
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
                                // Primeiro garantir que está desmarcado
                                checkbox.checked = false;
                                triggerEvents(checkbox);
                                
                                // Se devemos marcar, fazemos após um pequeno delay
                                if (checked) {
                                    setTimeout(() => {
                                        checkbox.checked = true;
                                        triggerEvents(checkbox);
                                    }, 100);
                                }
                            }
                        });
                    };
                    
                    // Desmarcar todos primeiro
                    handleCheckboxes([...checkboxesToCheck, ...checkboxesToUncheck], false);
                    
                    // Marcar os que devem ser marcados
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

            # Aguardar um pouco para todas as alterações serem processadas
            self.page.wait_for_timeout(1000)
            self.wait_for_loading_complete()

            # Verifica se todas as seleções foram aplicadas corretamente
            self.verify_selections(
                {
                    "Informação Básica": "input[id*='ctl00'][id*='wtContent']",
                    "Programação": "input[id*='ctl04'][id*='wtContent']",
                    "Documentos": "input[id*='ctl08'][id*='wtContent']",
                    "Planejamento": "input[id*='ctl02'][id*='wtContent']",
                    "Execução": "input[id*='ctl06'][id*='wtContent']",
                    "Derivadas": "input[id*='ctl10'][id*='wtContent']",
                }
            )

            print("Todas as opções do relatório foram configuradas corretamente.")

        except Exception as e:
            print(f"Erro ao configurar opções do relatório: {e}")
            self.page.screenshot(path="report_options_error.png")
            raise

    def verify_selections(self, checkboxes):
        """Verifica se todas as opções foram selecionadas corretamente."""
        for name, selector in checkboxes.items():
            try:
                # Usar evaluate para verificar o estado do checkbox
                is_checked = self.page.evaluate("""(selector) => {
                    const element = document.querySelector(selector);
                    return element ? element.checked : false;
                }""", selector)

                if not is_checked:
                    raise ValueError(f"Checkbox '{name}' não está selecionado como esperado")

            except Exception as e:
                print(f"Erro ao verificar seleção de '{name}': {e}")
                raise   

    def wait_for_loading_complete(self):
        """Aguarda a barra de progresso aparecer e depois desaparecer."""
        try:
            loading_bar_id = "SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wt31_OutSystemsUIWeb_wt2_block_RichWidgets_wt15_block_wtdivWait"
            print("Verificando carregamento da página...")

            # Aguardar a barra de progresso desaparecer
            self.page.wait_for_selector(f"#{loading_bar_id}", state="hidden")
            print("Barra de progresso desapareceu.")

            # Aguardar a rede estabilizar
            self.page.wait_for_load_state("networkidle")
            return True

        except Exception as e:
            print(f"Erro ao aguardar carregamento: {e}")
            return False

        except Exception as e:
            print(f"Erro durante o download: {e}")
            return False, None

    def export_to_excel(self):
        """Exporta o relatório para Excel, priorizando o método JavaScript."""
        try:
            print("Aguardando carregamento completo após seleção dos filtros...")

            # Aguardar o carregamento completo
            if not self.wait_for_loading_complete():
                print("Falha ao aguardar carregamento da página.")
                return False

            print("Página carregada completamente, prosseguindo com a exportação...")

            # Configurar o caminho de download
            download_path = os.path.join(os.getcwd(), "Downloads")
            os.makedirs(download_path, exist_ok=True)

            # Aumentar timeout padrão temporariamente
            self.page.set_default_timeout(60000)

            # Primeiro método: Usando cliques diretos (invertendo a ordem dos métodos)
            try:
                print("Tentando método com cliques diretos...")

                # XPath para o botão de três pontos
                three_dots_xpath = "//div[@id='SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt31_block_OutSystemsUIWeb_wt6_block_wtPrompt']/div/i"

                print("Aguardando botão de três pontos ficar visível...")

                # Configurar evento de download antes de qualquer clique
                with self.page.expect_download(timeout=70000) as download_promise:
                    # Clicar no botão de três pontos
                    self.page.click(f"xpath={three_dots_xpath}")
                    print("Clicado no botão de três pontos.")

                    # Aguardar o menu aparecer
                    self.page.wait_for_selector("text=Exportar para Excel", state="visible")
                    print("Opção 'Exportar para Excel' visível.")

                    # Clicar na opção de exportar
                    self.page.click("text=Exportar para Excel", timeout=30000)
                    print("Clicado em 'Exportar para Excel'")

                    try:
                        # Aguardar o download iniciar
                        print("Aguardando início do download...")
                        download = download_promise.value
                        print(f"Download iniciado: {download.suggested_filename}")

                        # Salvar o arquivo
                        download_file_path = os.path.join(
                            download_path, download.suggested_filename
                        )
                        download.save_as(download_file_path)
                        print(f"Download concluído: {download_file_path}")
                        return True
                    except Exception as download_error:
                        print(f"Erro durante o download: {download_error}")
                        raise

            except Exception as click_e:
                print(f"Erro no método de clique direto: {click_e}")
                self.page.screenshot(path="click_error.png")

                # Método alternativo: JavaScript
                print("Tentando método alternativo via JavaScript...")
                try:
                    with self.page.expect_download(timeout=75000) as download_promise:
                        success = self.page.evaluate(
                            """
                            () => {
                                // Tentar abrir o menu se estiver fechado
                                const dropdown = document.querySelector('[class*="dropdown"]');
                                if (dropdown) {
                                    dropdown.classList.add('show', 'open');
                                }
                                
                                // Encontrar e clicar no botão de exportação
                                const links = Array.from(document.querySelectorAll('a'));
                                const exportButton = links.find(link => 
                                    link.textContent.includes('Exportar para Excel') || 
                                    link.innerText.includes('Exportar para Excel')
                                );
                                
                                if (exportButton) {
                                    console.log('Botão de exportação encontrado');
                                    exportButton.click();
                                    return true;
                                }
                                console.log('Botão de exportação não encontrado');
                                return false;
                            }
                        """
                        )

                        if success:
                            download = download_promise.value
                            download_file_path = os.path.join(
                                download_path, download.suggested_filename
                            )
                            download.save_as(download_file_path)
                            print(
                                f"Download via JavaScript concluído: {download_file_path}"
                            )
                            return True
                        else:
                            print(
                                "JavaScript não conseguiu encontrar o botão de exportação"
                            )
                            return False

                except Exception as js_e:
                    print(f"Erro no método JavaScript: {js_e}")
                    self.page.screenshot(path="js_error.png")
                    return False

        except Exception as e:
            print(f"Erro geral ao exportar o relatório: {e}")
            self.page.screenshot(path="general_error.png")
            return False

        finally:
            # Restaurar timeout padrão
            self.page.set_default_timeout(30000)


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    # Configurar download automático
    page.set_default_timeout(60000)  # 60 segundos global

    # Instanciar a classe SAMNavigator
    navigator = SAMNavigator(page)

    # Fazer o login
    navigator.login("menon", "Huffman81*")

    # Navegar até a página de filtro
    navigator.navigate_to_filter_page()

    # Aguardar o campo 'Setor Executor'
    navigator.wait_for_filter_field()

    # Preencher o filtro com o valor "IEE3"
    navigator.fill_filter("IEE3")

    # Clicar na lupa para gerar o relatório
    navigator.click_search()

    # Aguardar para garantir que o relatório seja gerado
    page.wait_for_load_state('networkidle')

    # Após select_report_options, adicionar uma espera extra
    navigator.select_report_options()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)  # Dar tempo extra para estabilizar

    # Exportar para Excel
    navigator.export_to_excel()

    # Manter o navegador aberto para visualização
    page.wait_for_timeout(10000)
    input("Pressione Enter para fechar o navegador...")


# Executar o código usando Playwright
with sync_playwright() as playwright:
    run(playwright)

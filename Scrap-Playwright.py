from playwright.sync_api import sync_playwright
import os


class SAMNavigator:
    def __init__(self, page):
        self.page = page

    def login(self, username, password):
        """Realiza login no sistema com o usuário e senha fornecidos."""
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
        """Aguarda o campo 'Setor Executor' estar disponível e pronto para interação."""
        try:
            # Usar o seletor específico para aguardar o campo 'Setor Executor'
            self.page.wait_for_selector(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wt22_wtSSADashboardFilter_SectorExecutor",
                timeout=20000,
            )
            print("Campo 'Setor Executor' encontrado.")
        except Exception as e:
            print(f"Erro ao esperar pelo campo 'Setor Executor': {e}")

    def fill_filter(self, executor_setor_value):
        """Preenche o campo 'Setor Executor' com o valor fornecido."""
        try:
            # Preencher o campo de setor executor com o valor especificado
            self.page.fill(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wt22_wtSSADashboardFilter_SectorExecutor",
                executor_setor_value,
            )
            print(f"Campo 'Setor Executor' preenchido com: {executor_setor_value}")
        except Exception as e:
            print(f"Erro ao preencher o campo: {e}")

    def click_search(self):
        """Clica no botão de pesquisa (lupa)."""
        try:
            # Aguardar até que o botão de pesquisa esteja disponível e clicar
            self.page.click(
                "a#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wt22_OutSystemsUIWeb_wt60_block_wtWidget_wtSearchButton"
            )
            print("Lupa de pesquisa clicada.")
        except Exception as e:
            print(f"Erro ao clicar na lupa: {e}")

    def select_report_options(self):
        try:
            # Selecionar "Relatório com Detalhes"
            self.page.click("text=Relatório com Detalhes")

            # Selecionar os campos específicos
            self.page.check(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl00_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # Informação Básica
            self.page.check(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl04_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # Programação
            self.page.check(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl08_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # Documentos
            self.page.check(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl02_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # Planejamento
            self.page.check(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl06_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # Execução
            self.page.check(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl10_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # Derivadas

            # Certifique-se de que o campo APR não está selecionado
            self.page.uncheck(
                "input#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt90_block_wtListRecordsOptions_ctl12_OutSystemsUIWeb_wt21_block_wtContent_wt14"
            )  # APR

            print("Opções de relatório selecionadas.")

        except Exception as e:
            print(f"Erro ao selecionar as opções do relatório: {e}")
            self.page.screenshot(path="select_options_error.png")
            print("Screenshot de erro salvo como 'select_options_error.png'")

    '''
    def export_to_excel(self):
        try:
            # Aguardar para garantir que a página esteja estável
            self.page.wait_for_load_state("networkidle")

            # Usar JavaScript para clicar diretamente na opção "Exportar para Excel"
            click_success = self.page.evaluate(
                """
                () => {
                    const exportButtons = Array.from(document.querySelectorAll('a span'))
                        .filter(span => span.textContent.includes('Exportar para Excel'));
                    if (exportButtons.length > 0) {
                        exportButtons[0].click();
                        return true;
                    }
                    return false;
                }
            """
            )

            if click_success:
                print("Clique na opção 'Exportar para Excel' realizado via JavaScript.")
            else:
                print("Não foi possível encontrar a opção 'Exportar para Excel'.")
                self.page.screenshot(path="export_option_not_found.png")
                print("Screenshot salvo como 'export_option_not_found.png'")
                return

            # Configurar o caminho de download
            download_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(download_path, exist_ok=True)

            # Aguardar o download iniciar
            try:
                with self.page.expect_download(timeout=30000) as download_info:
                    # Aguardar um pouco para garantir que o download comece
                    self.page.wait_for_timeout(5000)

                download = download_info.value
                print(f"Download iniciado: {download.suggested_filename}")

                # Salvar o arquivo
                download_file_path = os.path.join(
                    download_path, download.suggested_filename
                )
                download.save_as(download_file_path)
                print(f"Arquivo Excel salvo como: {download_file_path}")
            except Exception as e:
                print(f"Erro durante o download: {e}")
                self.page.screenshot(path="download_error.png")
                print("Screenshot salvo como 'download_error.png'")

        except Exception as e:
            print(f"Erro geral ao exportar o relatório: {e}")
            self.page.screenshot(path="general_export_error.png")
            print("Screenshot de erro geral salvo como 'general_export_error.png'")

        # Verificação adicional para garantir que o download foi iniciado
        files_in_download_folder = os.listdir(download_path)
        if files_in_download_folder:
            print(f"Arquivos na pasta de download: {files_in_download_folder}")
        else:
            print("Nenhum arquivo encontrado na pasta de download.")
    '''

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
                with self.page.expect_download(timeout=60000) as download_promise:
                    # Clicar no botão de três pontos
                    self.page.click(f"xpath={three_dots_xpath}")
                    print("Clicado no botão de três pontos.")

                    # Aguardar o menu aparecer
                    self.page.wait_for_selector("text=Exportar para Excel", state="visible")
                    print("Opção 'Exportar para Excel' visível.")

                    # Clicar na opção de exportar
                    self.page.click("text=Exportar para Excel", timeout=10000)
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
                    with self.page.expect_download(timeout=60000) as download_promise:
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

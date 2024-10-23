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
        """
        Aguarda o carregamento completo, considerando múltiplas requisições assíncronas do OutSystems.
        Inclui timeouts adequados para operações longas.
        """
        try:
            loading_bar_id = "SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wt31_OutSystemsUIWeb_wt2_block_RichWidgets_wt15_block_wtdivWait"
            print("Iniciando monitoramento de carregamento...")
            
            # Aumentar o timeout padrão para 5 minutos
            self.page.set_default_timeout(300000)  # 5 minutos em milissegundos
            
            max_wait_time = 300  # Tempo máximo total de espera (5 minutos)
            stability_time = 5    # Tempo de estabilidade necessário (5 segundos)
            start_time = self.page.evaluate("() => Date.now()")
            
            while True:
                # Verificar se excedeu o tempo máximo
                current_time = self.page.evaluate("() => Date.now()")
                if (current_time - start_time) > (max_wait_time * 1000):
                    print("Tempo máximo de espera excedido!")
                    return False
                
                # Verificar se a barra está visível com timeout aumentado
                try:
                    is_loading = self.page.locator(f"#{loading_bar_id}").is_visible()
                    
                    if is_loading:
                        print("Barra de progresso detectada, aguardando...")
                        # Usar timeout explícito maior para wait_for_selector
                        self.page.wait_for_selector(f"#{loading_bar_id}", state="hidden", timeout=300000)
                        print("Barra de progresso desapareceu.")
                        start_time = self.page.evaluate("() => Date.now()")
                    else:
                        print(f"Verificando estabilidade por {stability_time} segundos...")
                        self.page.wait_for_timeout(stability_time * 1000)
                        
                        if not self.page.locator(f"#{loading_bar_id}").is_visible():
                            print("Página estável, carregamento concluído.")
                            # Verificação final do estado da rede com timeout aumentado
                            self.page.wait_for_load_state("networkidle", timeout=300000)
                            return True
                        else:
                            print("Barra reapareceu durante verificação de estabilidade, continuando monitoramento...")
                            continue
                            
                except Exception as wait_error:
                    print(f"Erro durante verificação de visibilidade/espera: {wait_error}")
                    continue

        except Exception as e:
            print(f"Erro ao monitorar carregamento: {e}")
            return False
        finally:
            # Restaurar o timeout padrão
            self.page.set_default_timeout(30000)

    def handle_download(self):
        """Gerencia o processo de download."""
        try:
            download_path = os.path.join(os.getcwd(), "Downloads")
            os.makedirs(download_path, exist_ok=True)

            with self.page.expect_download() as download_promise:
                # Clicar no botão de exportação
                export_button_xpath = "//div[@id='SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt31_block_OutSystemsUIWeb_wt6_block_wtPrompt']/div/i"
                self.page.click(f"xpath={export_button_xpath}")

                # Aguardar o download iniciar
                download = download_promise.value
                print(f"Download iniciado: {download.suggested_filename}")

                # Salvar o arquivo
                download_file_path = os.path.join(download_path, download.suggested_filename)
                download.save_as(download_file_path)

                # Verificar o arquivo
                if os.path.exists(download_file_path) and os.path.getsize(download_file_path) > 0:
                    print(f"Download concluído: {download_file_path}")
                    return True, download_file_path
                else:
                    print("Arquivo de download não encontrado ou vazio")
                    return False, None

        except Exception as e:
            print(f"Erro durante o download: {e}")
            return False, None

    def export_to_excel(self):
        """Exporta o relatório para Excel."""
        try:
            print("Aguardando carregamento completo após seleção dos filtros...")

            # Aguardar o carregamento completo
            if not self.wait_for_loading_complete():
                print("Falha ao aguardar carregamento da página.")
                return False

            print("Página carregada completamente, prosseguindo com a exportação...")

            # XPath para o botão de três pontos
            three_dots_xpath = "//div[@id='SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt31_block_OutSystemsUIWeb_wt6_block_wtPrompt']/div/i"

            # Aguardar e clicar no botão de três pontos
            try:
                self.page.wait_for_selector(
                    f"xpath={three_dots_xpath}", state="visible", timeout=10000
                )
                self.page.click(f"xpath={three_dots_xpath}")
                print("Menu de exportação aberto via três pontos.")

                # Aguardar um momento para o menu aparecer
                self.page.wait_for_selector(
                    "text=Exportar para Excel", state="visible", timeout=5000
                )

                # Iniciar o processo de download
                success, file_path = self.handle_download()

                if success:
                    print(
                        f"Exportação concluída com sucesso. Arquivo salvo em: {file_path}"
                    )
                    return True
                else:
                    print("Falha na exportação do arquivo.")
                    return False

            except Exception as e:
                print(f"Erro ao usar XPath para exportar: {e}")

                # Fallback usando JavaScript
                print("Tentando método alternativo via JavaScript...")
                with self.page.expect_download() as download_promise:
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
                        success, file_path = self.handle_download()
                        if success:
                            print(
                                f"Exportação via JavaScript concluída com sucesso. Arquivo salvo em: {file_path}"
                            )
                            return True

                print("Falha em todas as tentativas de exportação.")
                return False

        except Exception as e:
            print(f"Erro geral ao exportar o relatório: {e}")
            return False


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

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

    # Selecionar as opções do relatório
    navigator.select_report_options()

    # Exportar para Excel
    navigator.export_to_excel()

    # Manter o navegador aberto para visualização
    page.wait_for_timeout(10000)
    input("Pressione Enter para fechar o navegador...")


# Executar o código usando Playwright
with sync_playwright() as playwright:
    run(playwright)

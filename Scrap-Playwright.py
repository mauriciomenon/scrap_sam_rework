from playwright.sync_api import sync_playwright


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
        """Seleciona os detalhes do relatório e marca as opções desejadas."""
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
            
            """Exibe o menu de exportação e seleciona a opção 'Exportar para Excel'."""
            # Tentar exibir o dropdown se ele estiver oculto
            dropdown_selector = "#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt31_block_OutSystemsUIWeb_wt6_block_wtButtonDropdownWrapper .dropdown-icon"

            # Forçar visibilidade via JavaScript
            self.page.evaluate(
                'document.querySelector("#SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt31_block_OutSystemsUIWeb_wt6_block_wtButtonDropdownWrapper").classList.remove("is--hidden")'
            )

            # Clicar nos três pontos (dropdown) para abrir o menu
            self.page.click(dropdown_selector)
            print("Menu de exportação aberto.")
            
        except Exception as e:
            print(f"Erro ao selecionar as opções do relatório: {e}")

    def export_to_excel(self):
        try:
            # Aguardar a opção "Exportar para Excel" estar visível usando o XPath fornecido
            export_selector = '//*[contains(concat( " ", @class, " " ), concat( " ", "iguazu-ico-size-double", " " ))] | //*[(@id = "SAMTemplateAssets_wt93_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt31_block_OutSystemsUIWeb_wt6_block_wtDropdownList_wtDropdownList_wtLink_ExportToExcel")]//span'
            self.page.wait_for_selector(export_selector, timeout=5000)

            # Clicar na opção "Exportar para Excel"
            self.page.click(export_selector)
            print("Relatório exportado para Excel.")
        except Exception as e:
            print(f"Erro ao exportar o relatório: {e}")

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

    # Selecionar as opções do relatório
    navigator.select_report_options()

    # Exportar para Excel
    navigator.export_to_excel()

    # Manter o navegador aberto para visualização
    page.wait_for_timeout(30000)
    input("Pressione Enter para fechar o navegador...")


# Executar o código usando Playwright
with sync_playwright() as playwright:
    run(playwright)

    def export_to_excel(self):
        """Executa a função __doPostBack diretamente para exportar o relatório para Excel."""
        try:
            # Espera para garantir que a página esteja pronta
            self.page.wait_for_timeout(
                1000
            )  # Pequeno delay para garantir que o DOM esteja estável

            # Executa diretamente a função __doPostBack via JavaScript para exportar para Excel
            self.page.evaluate(
                """
                __doPostBack('SAMTemplateAssets_wt93$block$IguazuTheme_wt30$block$wtMenuDropdown$wtConditionalMenu$IguazuTheme_wt31$block$OutSystemsUIWeb$wt6$block$wtDropdownList$wtDropdownList$wtLink_ExportToExcel','');
            """
            )

            print("Relatório exportado para Excel via __doPostBack.")
        except Exception as e:
            print(f"Erro ao exportar o relatório: {e}")
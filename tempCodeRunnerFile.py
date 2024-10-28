        # Status do download após os erros
        if any("PendingGeneralSSAs.aspx" in str(error.get('details', '')) 
            for error in analysis["by_category"]["CRITICAL"]):
            print("\nSTATUS: Download do relatório completado com sucesso")
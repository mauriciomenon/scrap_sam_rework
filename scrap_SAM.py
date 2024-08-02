# MAURICIO MENON 20240621
# Ferramenta para gerar relatorios automaticamente, preenchedo os campos
# TO DO
# autenticação, chrome, caminhos absolutos, incluir driver na distribuição, 
# resolver lentidão na abertura, nao salva excel automaticamente
# por ultimo se preocupar em como so dados serao entrados

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os

# Caminho para o executável do GeckoDriver
gecko_driver_path = "C:/Users/menon/Downloads/geckodriver-v0.34.0-win32/geckodriver.exe"

# Caminho para o binário do Firefox
firefox_binary_path = "C:/Program Files/Mozilla Firefox/firefox.exe"

# Caminho para o perfil do Firefox 
profile_path = "C:/Users/menon/AppData/Roaming/Mozilla/Firefox/Profiles/xm9lfsi1.default-esr"

# Configuração do WebDriver 
options = webdriver.FirefoxOptions()
options.binary_location = firefox_binary_path

# Configurar preferências de download para o Firefox
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.manager.showWhenStarting", False)
options.set_preference("browser.download.dir", "C:/Users/menon/Downloads")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream")
options.set_preference("pdfjs.disabled", True)  # Desabilita visualizador de PDF embutido

# Especificar o caminho para o GeckoDriver
service = Service(gecko_driver_path, log_output="geckodriver.log")

driver = webdriver.Firefox(service=service, options=options)

try:
    # Acessa a página
    driver.get("https://apps.itaipu.gov.br/SAM_SMA_Reports/SSAsExecuted.aspx")
    
    # Aguarda o usuário fazer login manualmente
    print("Por favor, faça login manualmente e depois pressione Enter.")
    input("Pressione Enter depois de fazer login...")

    # Espera a página carregar o campo Setor Emissor
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtSSADashboardFilter_SectorExecutor"))
    )

    # Preenche o campo Setor Emissor
    setor_emissor = driver.find_element(
        By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtSSADashboardFilter_SectorExecutor"
    )
    setor_emissor.send_keys("IEE3")
    
    # Preenche os campos de Data de Execução (Ano/Semana)
    data_execucao_inicial = driver.find_element(
        By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtPlanningYearWeekStart_input2"
    )
    data_execucao_inicial.send_keys("202401")
    
    data_execucao_final = driver.find_element(
        By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtPlanningYearWeekEnd_input2"
    )
    data_execucao_final.send_keys("202425")
    
    # Clica no botão de procurar
    procurar_button = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_OutSystemsUIWeb_wt57_block_wtWidget_wtSearchButton"))
    )
    driver.execute_script("arguments[0].scrollIntoView();", procurar_button)
    driver.execute_script("arguments[0].click();", procurar_button)
    
    # Espera a página carregar os resultados (tempo ajustável conforme necessário)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//i[@class='iguazu-ico iguazu-ico-more3 iguazu-ico-size-double']"))
    )
    
    # Clica nos três pontinhos para exportar
    menu_button = driver.find_element(By.XPATH, "//i[@class='iguazu-ico iguazu-ico-more3 iguazu-ico-size-double']")
    driver.execute_script("arguments[0].scrollIntoView();", menu_button)
    driver.execute_script("arguments[0].click();", menu_button)
    
    # Clica na opção de exportar para Excel
    export_button = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt54_block_OutSystemsUIWeb_wt6_block_wtDropdownList_wtDropdownList_wtLink_ExportToExcel"))
    )
    driver.execute_script("arguments[0].scrollIntoView();", export_button)
    driver.execute_script("arguments[0].click();", export_button)
    
    # Espera o download do arquivo Excel (ajuste o tempo conforme necessário)
    time.sleep(10)  # Aguarde pelo tempo necessário para que o download seja concluído

finally:
    # Para facilitar o debug, vamos deixar o navegador aberto comentando a linha abaixo:
    # driver.quit()
    time.sleep(0)

# Caminho para o arquivo Excel baixado
excel_path = "C:/Users/menon/Downloads/Report.xlsx"

# Verifica se o arquivo foi baixado
if os.path.exists(excel_path):
    # Carrega o arquivo Excel baixado e processa com pandas
    df = pd.read_excel(excel_path)
    
    # Exemplo de manipulação de dados com pandas
    print(df.head())
else:
    print(f"O arquivo {excel_path} não foi encontrado.")

import os
import sys
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import pandas as pd

def download_geckodriver(target_path):
    base_url = "https://github.com/mozilla/geckodriver/releases/download/v0.33.0/"
    if sys.platform.startswith("win"):
        filename = "geckodriver-v0.33.0-win64.zip"
    elif sys.platform.startswith("linux"):
        filename = "geckodriver-v0.33.0-linux64.tar.gz"
    elif sys.platform.startswith("darwin"):
        filename = "geckodriver-v0.33.0-macos.tar.gz"
    else:
        raise OSError("Sistema operacional não suportado")

    url = base_url + filename
    response = requests.get(url)
    zip_path = os.path.join(target_path, filename)
    
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    
    if filename.endswith(".zip"):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_path)
    else:
        import tarfile
        with tarfile.open(zip_path, "r:gz") as tar:
            tar.extractall(path=target_path)
    
    os.remove(zip_path)
    
    if sys.platform.startswith("win"):
        return os.path.join(target_path, "geckodriver.exe")
    else:
        return os.path.join(target_path, "geckodriver")

def find_or_download_geckodriver():
    possible_paths = [
        "geckodriver.exe" if sys.platform.startswith("win") else "geckodriver",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "geckodriver.exe" if sys.platform.startswith("win") else "geckodriver"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "drivers", "geckodriver.exe" if sys.platform.startswith("win") else "geckodriver"),
        "C:\\WebDriver\\bin\\geckodriver.exe" if sys.platform.startswith("win") else "/usr/local/bin/geckodriver",
    ]
    
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    
    print("GeckoDriver não encontrado. Baixando...")
    return download_geckodriver(os.path.dirname(os.path.abspath(__file__)))

# Configuração de caminhos
base_path = os.path.dirname(os.path.abspath(__file__))
download_path = os.path.join(base_path, "downloads")

# Criar pasta de downloads se não existir
os.makedirs(download_path, exist_ok=True)

# Encontrar ou baixar o geckodriver
gecko_driver_path = find_or_download_geckodriver()

# Configuração do Firefox
options = Options()
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.manager.showWhenStarting", False)
options.set_preference("browser.download.dir", download_path)
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream")
options.set_preference("pdfjs.disabled", True)

# Função para tentar uma ação com retry
def retry_action(action, max_attempts=5, delay=5):
    for attempt in range(max_attempts):
        try:
            return action()
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            if attempt == max_attempts - 1:
                raise e
            print(f"Tentativa {attempt + 1} falhou. Tentando novamente em {delay} segundos...")
            time.sleep(delay)

# Inicializar o driver
try:
    service = Service(gecko_driver_path, log_output=os.path.devnull)  # Suprime o aviso de log
    driver = webdriver.Firefox(service=service, options=options)
except WebDriverException as e:
    print(f"Erro ao inicializar o WebDriver: {e}")
    print("Verifique se o Firefox está instalado corretamente.")
    sys.exit(1)

try:
    # Acessa a página
    driver.get("https://apps.itaipu.gov.br/SAM_SMA_Reports/SSAsExecuted.aspx")
    
    # Aguarda o usuário fazer login manualmente
    input("Por favor, faça login manualmente e pressione Enter quando concluir...")

    # Espera e preenche o campo Setor Emissor
    def fill_setor_emissor():
        setor_emissor = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtSSADashboardFilter_SectorExecutor"))
        )
        setor_emissor.clear()
        setor_emissor.send_keys("IEE3")
        print("Campo Setor Emissor preenchido com sucesso.")

    retry_action(fill_setor_emissor)
    
    # Preenche os campos de Data de Execução
    def fill_datas():
        data_execucao_inicial = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtPlanningYearWeekStart_input2"))
        )
        data_execucao_inicial.clear()
        data_execucao_inicial.send_keys("202401")
        
        data_execucao_final = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_wtPlanningYearWeekEnd_input2"))
        )
        data_execucao_final.clear()
        data_execucao_final.send_keys("202426")
        print("Campos de data preenchidos com sucesso.")

    retry_action(fill_datas)
    
    # Clica no botão de procurar
    def click_procurar():
        try:
            # Tenta encontrar o botão de várias maneiras
            procurar_button = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., 'Procurar')]"))
            )
            print("Botão 'Procurar' encontrado.")

            # Verifica se há algum overlay bloqueando o botão
            overlay = driver.find_elements(By.XPATH, "//div[contains(@class, 'modal-backdrop') or contains(@class, 'loading-overlay')]")
            if overlay:
                print("Overlay detectado. Aguardando sua remoção...")
                WebDriverWait(driver, 30).until(EC.invisibility_of_element(overlay[0]))

            # Tenta clicar no botão de várias maneiras
            try:
                procurar_button.click()
            except:
                driver.execute_script("arguments[0].scrollIntoView(true);", procurar_button)
                driver.execute_script("arguments[0].click();", procurar_button)

            print("Botão de procurar clicado com sucesso.")

            # Aguarda o carregamento dos resultados
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'table-generic')]"))
            )
            print("Resultados carregados com sucesso.")
        except Exception as e:
            print(f"Erro ao clicar no botão Procurar: {e}")
            print("Tentando método alternativo...")
            
            # Método alternativo: usar JavaScript para clicar em todos os botões visíveis
            buttons = driver.find_elements(By.XPATH, "//button[not(contains(@style,'display:none')) and not(contains(@style,'display: none'))]")
            for button in buttons:
                try:
                    driver.execute_script("arguments[0].click();", button)
                    print(f"Clicado no botão: {button.text}")
                    time.sleep(2)  # Espera curta após cada clique
                except:
                    pass

            # Verifica novamente se os resultados foram carregados
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'table-generic')]"))
                )
                print("Resultados carregados com sucesso após método alternativo.")
            except:
                print("Não foi possível carregar os resultados mesmo após o método alternativo.")
                raise

    retry_action(click_procurar)
    
    # Espera e clica nos três pontinhos para exportar
    def click_menu():
        menu_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//i[@class='iguazu-ico iguazu-ico-more3 iguazu-ico-size-double']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", menu_button)
        driver.execute_script("arguments[0].click();", menu_button)
        print("Menu de opções aberto com sucesso.")

    retry_action(click_menu)
    
    # Clica na opção de exportar para Excel
    def click_export():
        export_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMenuDropdown_wtConditionalMenu_IguazuTheme_wt54_block_OutSystemsUIWeb_wt6_block_wtDropdownList_wtDropdownList_wtLink_ExportToExcel"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", export_button)
        driver.execute_script("arguments[0].click();", export_button)
        print("Opção de exportar para Excel clicada com sucesso.")

    retry_action(click_export)
    
    # Espera o download do arquivo Excel
    print("Aguardando o download do arquivo Excel...")
    time.sleep(30)  # Aumentado para 30 segundos

except Exception as e:
    print(f"Ocorreu um erro durante a execução: {e}")
    print("Detalhes adicionais:")
    print(f"URL atual: {driver.current_url}")
    print(f"Título da página: {driver.title}")
    print("HTML da página:")
    print(driver.page_source[:1000])  # Imprime os primeiros 1000 caracteres do HTML

finally:
    driver.quit()

# Processa o arquivo Excel baixado
excel_path = os.path.join(download_path, "Report.xlsx")
if os.path.exists(excel_path):
    df = pd.read_excel(excel_path)
    print(df.head())
else:
    print(f"O arquivo {excel_path} não foi encontrado.")
    print("Verifique se o download foi concluído com sucesso.")
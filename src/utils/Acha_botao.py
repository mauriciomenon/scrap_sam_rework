from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
driver.get("https://apps.itaipu.gov.br/SAM_SMA_Reports/SSAsExecuted.aspx")

def highlight_element(element, color="blue", border=4):
    driver.execute_script("""
    arguments[0].style.border = "%spx solid %s";
    """ % (border, color), element)

# Espere até que a página esteja carregada
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.TAG_NAME, "body"))
)

# Tente localizar o botão por ID
try:
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "SAMTemplateAssets_wt14_block_IguazuTheme_wt30_block_wtMainContent_wtMainContent_SAM_SMA_CW_wt107_block_OutSystemsUIWeb_wt60_block_wtWidget_wtSearchButton"))
    )
    highlight_element(button)
    print("Botão encontrado por ID e destacado em azul")
except:
    print("Botão não encontrado por ID")

# Tente localizar o botão por texto (ícone de busca)
try:
    search_icon = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'fa-search')]"))
    )
    parent_button = search_icon.find_element_by_xpath("..")  # Pega o elemento pai do ícone
    highlight_element(parent_button, color="green")
    print("Botão encontrado por ícone de busca e destacado em verde")
except:
    print("Botão não encontrado por ícone de busca")

# Tente localizar qualquer elemento com 'search' no ID
try:
    search_elements = driver.find_elements_by_xpath("//*[contains(@id, 'search') or contains(@id, 'Search')]")
    for i, element in enumerate(search_elements):
        highlight_element(element, color=f"rgb({i*30}, {i*30}, 255)")
        print(f"Elemento de busca {i+1} encontrado e destacado")
except:
    print("Nenhum elemento de busca adicional encontrado")

print("Inspeção visual ativa por 30 segundos. Verifique os elementos destacados.")
time.sleep(30)

driver.quit()
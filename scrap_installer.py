import os
import requests
import zipfile
import subprocess

# Definir URLs de download
firefox_url = "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=en-US"
gecko_driver_url = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-win64.zip"

# Definir diretórios de destino
base_path = os.path.dirname(os.path.abspath(__file__))
drivers_path = os.path.join(base_path, "drivers")
firefox_path = os.path.join(drivers_path, "firefox")
gecko_driver_path = os.path.join(drivers_path, "geckodriver")

# Criar diretórios de destino se não existirem
os.makedirs(firefox_path, exist_ok=True)
os.makedirs(gecko_driver_path, exist_ok=True)

# Função para baixar um arquivo
def download_file(url, dest):
    response = requests.get(url, stream=True)
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

# Baixar o instalador do Firefox
firefox_installer_path = os.path.join(firefox_path, "firefox_installer.exe")
download_file(firefox_url, firefox_installer_path)

# Instalar o Firefox silenciosamente
subprocess.run([firefox_installer_path, "/S"], check=True)

# Baixar e extrair GeckoDriver
gecko_driver_zip_path = os.path.join(gecko_driver_path, "geckodriver.zip")
download_file(gecko_driver_url, gecko_driver_zip_path)
with zipfile.ZipFile(gecko_driver_zip_path, 'r') as zip_ref:
    zip_ref.extractall(gecko_driver_path)
os.remove(gecko_driver_zip_path)

print("Firefox e GeckoDriver foram baixados e instalados com sucesso.")

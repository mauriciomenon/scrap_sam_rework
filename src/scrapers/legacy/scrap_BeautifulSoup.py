from bs4 import BeautifulSoup
import pandas as pd

# Carregar o conteúdo do arquivo HTML
file_path = 'c:\\Users\\menon\\Downloads\\https _apps.itaipu.gov.br_SAM_SMA_Reports_SSAsExecuted.aspx.htm'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Analisar o conteúdo HTML
soup = BeautifulSoup(content, 'html.parser')

# Encontrar todos os elementos input e button
elements = soup.find_all(['input', 'button'])

# Preparar uma lista para armazenar os dados
data = []

# Extrair informações relevantes de cada elemento
for element in elements:
    element_type = element.name
    element_id = element.get('id', '')
    element_name = element.get('name', '')
    element_value = element.get('value', '')
    element_class = ' '.join(element.get('class', []))
    
    data.append({
        'Type': element_type,
        'ID': element_id,
        'Name': element_name,
        'Value': element_value,
        'Class': element_class
    })

# Criar um DataFrame com os dados
df = pd.DataFrame(data)

# Exibir o DataFrame
print(df)

# Salvar o DataFrame como uma tabela em um arquivo CSV
output_path = 'c:\\Users\\menon\\Downloads\\web_elements_updated.csv'
df.to_csv(output_path, index=False)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from urllib.parse import urljoin
from datetime import datetime
import os
import time
import json

# 변수 저장
today_date_str = datetime.now().strftime("%Y%m%d")
download_directory = os.path.join("./data/Research_toprank", today_date_str)
company_name = "유안타증권"
title_prefix_xpath = '//*[@id="content"]/div/div[2]/div/div[4]/div/div/div[1]/ul/li'
date_prefix_xpath = '//*[@id="content"]/div/div[2]/div/div[4]/div/div/div[1]/ul/li'

previous_file_title = None

# Check if the directory exists, if not, create it
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

url = "https://www.myasset.com/myasset/research/RS_0000000_M.cmd"

# Start a headless browser session (make sure to have the appropriate webdriver installed, e.g., chromedriver)
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

driver.get(url)

# 버튼을 누르기전 첫번째 리서치 제목(다음버튼을 누른후 절차를 위해 저장)


# 조회수 상위 버튼을 누르게함.
top_views_button = driver.find_element(By.XPATH, '//a[@class="type2 js-bdTab" and @data-seq="1"]')
top_views_button.click()
time.sleep(3)

# Assuming the links are loaded dynamically after the page is rendered
# Wait for some time for the page to load or use WebDriverWait for more robust waiting
driver.implicitly_wait(10)

pdf_file_url = {}

while True: 
    # Find all elements with cmd-type="download"
    download_links = driver.find_elements(By.XPATH, '//a[@cmd-type="download"]')
    print("download_links: ", len(download_links))


    if not download_links:
        print("No more download links found, exit the loop")
        break  # No more download links found, exit the loop

    for i, link in enumerate(download_links, start=1):
        # 제목과 날짜 뽑아내기
        title_xpath = f'{title_prefix_xpath}[{i}]//a'
        date_xpath = f'{title_prefix_xpath}[{i}]//p[contains(@class, "rsBoardLIstLow")][last()]'

        # Find elements for title and date
        title_element = driver.find_element(By.XPATH, title_xpath)
        date_element = driver.find_element(By.XPATH, date_xpath)

        # Extract text content
        file_title = title_element.text.strip()
        file_title = file_title.replace(" ", "_").replace("/", "_")
        file_date = date_element.text.split(' | ')[0]
        file_date = file_date.replace('/', '-')
        print("Title:", file_title)
        print("Date:", file_date)
    
        if previous_file_title == file_title:
            print("File title is the same as the previous page", previous_file_title, file_title)
            break  # File title is the same as the previous page, exit the loop

        # Save the first file title of each page
        if i == 1:
            previous_file_title = file_title

        # url 뽑아내기 (data-seq ="2023~~~~ko.pdf"로 구성)
        pdf_url = link.get_attribute('data-seq')

        # Construct the full URL by joining the relative path with the base URL
        base_url = "https://file.myasset.com/sitemanager/upload/"
        full_pdf_url = urljoin(base_url, pdf_url)
        print('full_pdf_url: ', full_pdf_url)

        # Download the PDF file
        pdf_response = requests.get(full_pdf_url, stream=True)
        
        # Specify the filename for saving
        filename = f"{file_title}_{file_date}_{company_name}.pdf"
        print('filename:',filename)
        file_path = os.path.join(download_directory, filename)
        print(download_directory)
        print('여기까지가 파일 쓰기전임')

        # Save the PDF file
        with open(file_path, 'wb') as pdf_file:
            for chunk in pdf_response.iter_content(chunk_size=1024):
                if chunk:
                    pdf_file.write(chunk)
        
        print(f"Downloaded {filename}  to {download_directory} ")
        
        # 사전에 데이터 추가
        pdf_file_url[filename] = full_pdf_url
    if previous_file_title == file_title:
        break

    print("다음 버튼을 클릭함")
    next_button = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[2]/div/div[4]/div/div/div[1]/div/div/a[2]')
    next_button.click()
    time.sleep(3)
    
    
print(pdf_file_url)
# Save the DataFrame to a JSON file
with open(f'data/Research_toprank/TopRank_file_urls_{today_date_str}.json', 'w', encoding='utf-8') as json_file:
    json.dump(pdf_file_url, json_file, ensure_ascii=False)


driver.quit()


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from urllib.parse import urljoin
from datetime import datetime
import os
import time


# 변수 저장
today_date_str = datetime.now().strftime("%Y%m%d")
download_directory = os.path.join("./research_ranktop", today_date_str)
company_name = "유안타증권"
title_prefix_xpath = '//*[@id="content"]/div/div[2]/div/div[4]/div/div/div[1]/ul/li'
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


while True: 
    # Find all elements with cmd-type="download"
    download_links = driver.find_elements(By.XPATH, '//a[@cmd-type="download"]')
    print("download_links: ", len(download_links))


    if not download_links:
        print("No more download links found, exit the loop")
        break  # No more download links found, exit the loop

    for i, link in enumerate(download_links, start=1):
        # 제목 뽑아내기
        title_xpath = f'{title_prefix_xpath}[{i}]/ul/li[2]/a'
        title_element = driver.find_element(By.XPATH, title_xpath)
        file_title = title_element.text.strip()
        print(file_title)
        # Sanitize file title
        file_title = file_title.replace(" ", "_").replace("/", "_").replace(":", "_")

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
        filename = f"{file_title}_{today_date_str}_{company_name}.pdf"
        file_path = os.path.join(download_directory, filename)

        # Save the PDF file
        with open(file_path, 'wb') as pdf_file:
            for chunk in pdf_response.iter_content(chunk_size=1024):
                if chunk:
                    pdf_file.write(chunk)
        
        print(f"Downloaded {filename}  to {download_directory} ")

    if previous_file_title == file_title:
        break

    print("다음 버튼을 클릭함")
    next_button = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[2]/div/div[4]/div/div/div[1]/div/div/a[2]')
    next_button.click()
    time.sleep(3)


driver.quit()



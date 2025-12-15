from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Đường dẫn Chrome + Chromedriver của bạn
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
driver_path = "/Users/binh/Downloads/chromedriver-mac-arm64 bài tập lớp/chromedriver"

# Cấu hình Chrome
options = Options()
options.binary_location = chrome_path

# Tạo service driver
service = Service(driver_path)

# Khởi chạy Chrome
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://en.wikipedia.org/wiki/List_of_painters_by_name")
time.sleep(2)

# Lấy tất cả link
tags = driver.find_elements(By.TAG_NAME, "a")
links = [tag.get_attribute("href") for tag in tags]

# In ra 20 link đầu tiên để bạn xem
for link in links[:20]:
    print(link)

driver.quit()

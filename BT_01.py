from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Khởi tạo webdriver
driver = webdriver.Chrome()

# Mở trang
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name"
driver.get(url)

# Đợi khoảng chừng 2s
time.sleep(2)

# Lấy tất cả các thẻ <a>
tags = driver.find_elements(By.TAG_NAME, "a")

# Tạo ra danh sách các liên kết
links = [tag.get_attribute("href") for tag in tags]

# Xuất thông tin
for link in links:
    print(link)

# Đóng webdriver
driver.quit()

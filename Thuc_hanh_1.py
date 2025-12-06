from pygments.formatters.html import webify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

#khoi tao web
driver = webdriver.Chrome()

#mo trang
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name"
driver.get(url)

time.sleep(3)  # cho trang web tai xong

tags = driver.find_elements(By.TAG_NAME, "a")

links = [tag.get_attribute("href") for tag in tags]

for link in links:
    print(link)
    
driver.quit()

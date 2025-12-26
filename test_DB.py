"""
Web Scraper cho Chợ Tốt - Version 8.1 (DATABASE + CSV AUTO-EXPORT)
Giữ nguyên 100% logic cào của bạn.
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
# --- THÊM: Thư viện MongoDB ---
from pymongo import MongoClient

class ChototScraper:
    def __init__(self, headless=True):
        """Khởi tạo scraper"""
        gecko_path = r'D:\Cong viec\Ma_Nguon_Mo\BT_cuoiki_MNM\geckodriver.exe'
        firefox_path = "C:/Program Files/Mozilla Firefox/firefox.exe"
        
        self.options = Options()
        self.options.binary_location = firefox_path
        self.options.page_load_strategy = 'eager'
        
        if headless:
            self.options.add_argument('--headless')
        
        self.options.set_preference('general.useragent.override', 
                                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/120.0')
        
        service = Service(executable_path=gecko_path)
        self.driver = webdriver.Firefox(service=service, options=self.options)
        self.driver.set_page_load_timeout(20)
        self.wait = None
        self.data = []

        # --- THÊM: Kết nối MongoDB ---
        try:
            self.client = MongoClient("mongodb://localhost:27017/")
            self.db = self.client["chotot_db"]
            self.collection = self.db["xe_may"]
            self.collection.create_index("URL", unique=True) # Chống trùng link
            print("✓ Đã kết nối MongoDB thành công!")
        except Exception as e:
            print(f"✗ Lỗi kết nối DB: {e}")
        
        # DANH SÁCH CỘT (Giữ nguyên)
        self.required_columns = [
            'URL', 'Tên sản phẩm', 'Giá', 'Tên người đăng', 'Địa chỉ', 'Thời gian đăng', 'URL hình ảnh',
            'Số Km đã đi', 'Số đời chủ', 'Có phụ kiện đi kèm', 'Còn hạn đăng kiểm',
            'Xuất xứ', 'Tình trạng', 'Chính sách bảo hành',
            'Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Hộp số',
            'Nhiên liệu', 'Kiểu dáng', 'Số chỗ', 
            'Trọng lượng', 'Trọng tải'
        ]
        
        # MAPPING ITEMPROP (Giữ nguyên)
        self.itemprop_mappings = {
            'mileage_v2': 'Số Km đã đi', 'number_of_owners': 'Số đời chủ',
            'include_accessories': 'Có phụ kiện đi kèm', 'valid_registration': 'Còn hạn đăng kiểm',
            'carorigin': 'Xuất xứ', 'condition_ad': 'Tình trạng',
            'veh_warranty_policy': 'Chính sách bảo hành', 'carbrand': 'Hãng xe',
            'carmodel': 'Dòng xe', 'mfdate': 'Năm sản xuất',
            'gearbox': 'Hộp số', 'fuel': 'Nhiên liệu',
            'cartype': 'Kiểu dáng', 'carseats': 'Số chỗ',
            'veh_unladen_weight': 'Trọng lượng', 'veh_gross_weight': 'Trọng tải'
        }

    # --- GIỮ NGUYÊN 100% CÁC HÀM CÀO DỮ LIỆU CỦA BẠN ---
    def get_product_links_from_page(self):
        product_links = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        while scroll_attempts < 10:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts += 1
            if new_height == last_height: break
            last_height = new_height
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href:
                full_url = 'https://xe.chotot.com' + href if href.startswith('/') else href
                if ('chotot.com' in full_url and re.search(r'/\d+', full_url) and 
                    '/mua-ban' in full_url and '?' not in full_url and full_url not in product_links):
                    product_links.append(full_url)
        return product_links

    def extract_specs_by_itemprop(self, soup):
        specs = {}
        for prop, label in self.itemprop_mappings.items():
            elem = soup.find(itemprop=prop)
            if elem:
                value = elem.get_text(strip=True)
                if value: specs[label] = value
        return specs

    def extract_seller_info(self, soup):
        seller_info = {'Tên người đăng': '', 'Địa chỉ': '', 'Thời gian đăng': '', 'URL hình ảnh': ''}
        try:
            seller_container = soup.find('div', itemprop='seller')
            if seller_container:
                pf9ruvz_div = seller_container.find('div', class_=re.compile(r'pf9ruvz'))
                if pf9ruvz_div:
                    seller_link = pf9ruvz_div.find('a', href=re.compile(r'/(cua-hang|user)/'))
                    if seller_link:
                        seller_b = seller_link.find('b')
                        if seller_b: seller_info['Tên người đăng'] = seller_b.get_text(strip=True)
            time_posted = soup.find('span', class_='bwq0cbs', string=re.compile(r'Đăng.*trước'))
            if time_posted: seller_info['Thời gian đăng'] = time_posted.get_text(strip=True)
            address_spans = soup.find_all('span', class_='bwq0cbs')
            for span in address_spans:
                text = span.get_text(strip=True)
                if len(text) > 15 and any(x in text for x in ['Phường', 'Quận', 'TP', 'Huyện']):
                    if 'Đăng' not in text: 
                        seller_info['Địa chỉ'] = text
                        break
            # Logic hình ảnh (giữ nguyên của bạn)
            all_imgs = soup.find_all('img', src=True)
            for img in all_imgs:
                src = img.get('src', '')
                if 'cdn.chotot.com' in src:
                    seller_info['URL hình ảnh'] = src
                    break
        except: pass
        return seller_info

    def scrape_product(self, url):
        try:
            self.driver.get(url)
            time.sleep(4)
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1)*800});")
                time.sleep(1.5)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            product_data = {'URL': url, 'Tên sản phẩm': '', 'Giá': ''}
            title_elem = soup.find('h1')
            if title_elem: product_data['Tên sản phẩm'] = title_elem.get_text(strip=True)
            price_elem = soup.find('b', class_='p26z2wb')
            if price_elem: product_data['Giá'] = price_elem.get_text(strip=True)
            product_data.update(self.extract_seller_info(soup))
            product_data.update(self.extract_specs_by_itemprop(soup))
            return product_data
        except: return None

    def go_to_next_page_direct(self, next_page):
        try:
            new_url = f"https://xe.chotot.com/mua-ban-oto-tp-ho-chi-minh?page={next_page}"
            self.driver.get(new_url)
            time.sleep(4)
            return True
        except: return False

    def scrape_test_pages(self, start_url, num_pages=2):
        self.driver.get(start_url)
        time.sleep(3)
        for page_num in range(1, num_pages + 1):
            if page_num > 1: self.go_to_next_page_direct(page_num)
            links = self.get_product_links_from_page()
            for link in links:
                data = self.scrape_product(link)
                if data: self.data.append(data)
                print(f" ✓ Đã cào: {link[:50]}")

    # --- THAY ĐỔI: Chuyển Export Excel sang Database + CSV ---
    def save_to_db_and_export_csv(self):
        if not self.data: return
        
        # 1. Lưu vào MongoDB (Upsert tránh trùng)
        print("\n⏳ Đang lưu vào MongoDB...")
        for item in self.data:
            self.collection.update_one({"URL": item["URL"]}, {"$set": item}, upsert=True)
        
        # 2. Tự động đóng gói ra file CSV từ Database
        print("📦 Đang xuất file CSV...")
        cursor = self.collection.find({})
        df = pd.DataFrame(list(cursor))
        
        if not df.empty:
            if '_id' in df.columns: df.drop('_id', axis=1, inplace=True)
            # encoding='utf-8-sig' để Excel mở không lỗi tiếng Việt
            df.to_csv('chotot_oto_database.csv', index=False, encoding='utf-8-sig')
            print(f"✅ Đã lưu xong DB và xuất file 'chotot_oto_database.csv'!")

    def close(self):
        self.driver.quit()
        if hasattr(self, 'client'): self.client.close()

def main():
    url = "https://xe.chotot.com/mua-ban-oto-tp-ho-chi-minh"
    scraper = ChototScraper(headless=True)
    try:
        scraper.scrape_test_pages(url, num_pages=150)
        # Thay hàm cũ bằng hàm mới
        scraper.save_to_db_and_export_csv()
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
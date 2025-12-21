"""
Web Scraper cho Chợ Tốt - Cào dữ liệu xe máy (FIXED)
Sửa lỗi: Chuyển trang và trích xuất thông số kỹ thuật
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

class ChototScraper:
    def __init__(self, headless=True):
        """Khởi tạo scraper"""
        gecko_path = "/Users/binh/thuc_hanh_ma_nguon_mo/gecko bài tập /bài tập trên lớp/geckodriver"
        firefox_path = "/Applications/Firefox.app/Contents/MacOS/firefox"
        
        self.options = Options()
        self.options.binary_location = firefox_path
        self.options.page_load_strategy = 'eager'
        
        if headless:
            self.options.add_argument('--headless')
        
        self.options.set_preference('permissions.default.image', 2)
        self.options.set_preference('general.useragent.override', 
                                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/120.0')
        
        service = Service(executable_path=gecko_path)
        self.driver = webdriver.Firefox(service=service, options=self.options)
        self.driver.set_page_load_timeout(20)
        self.wait = WebDriverWait(self.driver, 15)
        self.data = []
    
    def step1_go_to_homepage(self):
        """Bước 1: Vào trang chủ Chợ Tốt và chọn khu vực"""
        print("\n[BƯỚC 1] Truy cập trang chủ https://www.chotot.com/")
        self.driver.get("https://www.chotot.com/")
        time.sleep(3)
        print(f"✓ Đã vào trang: {self.driver.title}")
        
        print("\n[BƯỚC 1.1] Xử lý popup chọn khu vực...")
        try:
            hcm_selectors = [
                (By.XPATH, "//*[contains(text(), 'Hồ Chí Minh')]"),
                (By.XPATH, "//img[@alt='Hồ Chí Minh']/ancestor::*[1]"),
                (By.XPATH, "//*[text()='Hồ Chí Minh']"),
            ]
            
            clicked = False
            for by, selector in hcm_selectors:
                try:
                    hcm_element = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    hcm_element.click()
                    print(f"✓ Đã chọn 'Hồ Chí Minh'")
                    clicked = True
                    time.sleep(2)
                    break
                except:
                    continue
            
            if not clicked:
                print("ℹ Không tìm thấy popup khu vực, có thể đã được chọn sẵn")
            
            try:
                confirm_selectors = [
                    (By.XPATH, "//button[contains(text(), 'Xác nhận')]"),
                    (By.XPATH, "//*[contains(text(), 'Xác nhận')]"),
                    (By.XPATH, "//button[contains(@class, 'confirm') or contains(@class, 'submit')]"),
                ]
                
                for by, selector in confirm_selectors:
                    try:
                        confirm_btn = self.wait.until(EC.element_to_be_clickable((by, selector)))
                        confirm_btn.click()
                        print(f"✓ Đã click 'Xác nhận'")
                        time.sleep(3)
                        break
                    except:
                        continue
            except:
                print("ℹ Không tìm thấy nút Xác nhận")
                
        except Exception as e:
            print(f"ℹ Bỏ qua popup: {str(e)}")
        
        print(f"✓ URL sau khi chọn khu vực: {self.driver.current_url}")
    
    def step2_click_xe_co(self):
        """Bước 2: Click vào category 'Xe cộ'"""
        print("\n[BƯỚC 2] Click vào 'Xe cộ'")
        time.sleep(2)
        
        try:
            selectors = [
                (By.XPATH, "//*[text()='Xe cộ']"),
                (By.XPATH, "//*[contains(text(), 'Xe cộ')]"),
                (By.XPATH, "//img[@alt='Xe cộ']"),
                (By.XPATH, "//img[contains(@alt, 'Xe cộ')]/ancestor::a"),
                (By.XPATH, "//img[contains(@alt, 'Xe cộ')]/parent::*/parent::*"),
                (By.XPATH, "//span[@class='coblrut' and text()='Xe cộ']"),
                (By.XPATH, "//span[contains(@class, 'coblrut') and contains(text(), 'Xe cộ')]"),
                (By.XPATH, "//a[contains(., 'Xe cộ')]"),
            ]
            
            for by, selector in selectors:
                try:
                    print(f"   Thử selector: {selector[:50]}...")
                    element = self.wait.until(EC.presence_of_element_located((by, selector)))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                    print(f"✓ Đã click vào 'Xe cộ'")
                    time.sleep(3)
                    print(f"✓ URL hiện tại: {self.driver.current_url}")
                    return True
                except Exception as e:
                    continue
            
            with open('debug_homepage.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("✗ Không tìm thấy 'Xe cộ', đã lưu debug_homepage.html")
            return False
            
        except Exception as e:
            print(f"✗ Lỗi: {str(e)}")
            return False
    
    def step3_click_xem_them(self):
        """Bước 3: Click nút 'Xem thêm X tin đăng'"""
        print("\n[BƯỚC 3] Tìm và click 'Xem thêm ... tin đăng'")
        self.driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        try:
            selectors = [
                (By.XPATH, "//*[contains(text(), 'Xem thêm') and contains(text(), 'tin đăng')]"),
                (By.XPATH, "//button[contains(text(), 'Xem thêm')]"),
                (By.XPATH, "//a[contains(text(), 'Xem thêm')]"),
                (By.XPATH, "//*[contains(text(), 'tin đăng')]/ancestor::button"),
                (By.XPATH, "//*[contains(text(), 'tin đăng')]/ancestor::a"),
            ]
            
            for by, selector in selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    button_text = element.text
                    print(f"✓ Tìm thấy nút: '{button_text}'")
                    element.click()
                    time.sleep(3)
                    print(f"✓ Đã click, URL hiện tại: {self.driver.current_url}")
                    return True
                except:
                    continue
            
            print("ℹ Không tìm thấy nút 'Xem thêm', có thể đã ở trang danh sách rồi")
            return True
            
        except Exception as e:
            print(f"ℹ Không click được 'Xem thêm': {str(e)}")
            return True
    
    def get_product_links_from_page(self):
        """Lấy tất cả links sản phẩm từ trang hiện tại"""
        product_links = []
        print(f"📥 Đang scroll để load sản phẩm...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 10
        
        while scroll_attempts < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts += 1
            if new_height == last_height:
                break
            last_height = new_height
        
        print(f"✓ Đã scroll {scroll_attempts} lần")
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    full_url = 'https://www.chotot.com' + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                if ('chotot.com' in full_url and 
                    re.search(r'/\d+', full_url) and
                    '/mua-ban' in full_url and
                    '?' not in full_url and
                    full_url not in product_links):
                    product_links.append(full_url)
        
        if len(product_links) > 0:
            print(f"✓ Tìm thấy {len(product_links)} sản phẩm")
            print(f"📝 Ví dụ 3 links đầu:")
            for i, link in enumerate(product_links[:3], 1):
                print(f"   {i}. {link}")
        
        return product_links
    
    def extract_specs(self, soup):
        """
        Trích xuất thông số kỹ thuật - FIXED VERSION
        Xử lý cả 2 loại cấu trúc HTML khác nhau
        """
        specs = {}
        
        try:
            # Tìm h2 "Thông số kỹ thuật" hoặc "Thông số chi tiết"
            detail_section = soup.find('h2', class_='tfvqu6u', string=re.compile(r'Thông số'))
            
            if detail_section:
                # Tìm container chính (div.pqop88r)
                main_container = detail_section.find_next('div', class_='pqop88r')
                
                if main_container:
                    # Tìm tất cả div chứa thông số (có thể là s1r2e0fc hoặc befjs93)
                    spec_containers = main_container.find_all('div', class_=re.compile(r's1r2e0fc|befjs93'))
                    
                    for container in spec_containers:
                        # Tìm tất cả các item thông số (pqp26ip hoặc p1ja3eq0)
                        spec_items = container.find_all('div', class_=re.compile(r'pqp26ip|p1ja3eq0'))
                        
                        for item in spec_items:
                            # Tìm tất cả span
                            all_spans = item.find_all('span', class_='bwq0cbs')
                            
                            if len(all_spans) >= 2:
                                # Span đầu tiên có màu xám (rgb(140, 140, 140)) = label
                                # Span thứ 2 = value
                                label_span = all_spans[0]
                                value_span = all_spans[1]
                                
                                # Lấy text và làm sạch
                                label = label_span.get_text(strip=True).replace(':', '').strip()
                                value = value_span.get_text(strip=True)
                                
                                if label and value:
                                    specs[label] = value
                            
                            # Trường hợp đặc biệt: có thể có link <a> trong value
                            # Ví dụ: Hãng xe, Dòng xe
                            elif len(all_spans) == 1:
                                label = all_spans[0].get_text(strip=True).replace(':', '').strip()
                                # Tìm link hoặc span tiếp theo
                                link = item.find('a')
                                if link:
                                    value_span = link.find('span', class_='bwq0cbs')
                                    if value_span:
                                        value = value_span.get_text(strip=True)
                                        if label and value:
                                            specs[label] = value
        
        except Exception as e:
            print(f"    ⚠ Lỗi trích xuất specs: {str(e)}")
        
        return specs
    
    def scrape_product(self, url):
        """Cào thông tin chi tiết một sản phẩm"""
        try:
            self.driver.get(url)
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product_data = {
                'URL': url,
                'Tiêu đề': '',
                'Giá': '',
            }
            
            # Lấy tiêu đề
            title_elem = soup.find('h1')
            if title_elem:
                product_data['Tiêu đề'] = title_elem.get_text(strip=True)
            
            # Lấy giá
            price_patterns = [
                soup.find(string=re.compile(r'\d+\.\d+\.\d+ đ')),
                soup.find(string=re.compile(r'\d+ triệu')),
                soup.find(string=re.compile(r'\d+\.\d+ tỷ')),
            ]
            for price_elem in price_patterns:
                if price_elem:
                    product_data['Giá'] = price_elem.strip()
                    break
            
            # Lấy thông số kỹ thuật
            specs = self.extract_specs(soup)
            product_data.update(specs)
            
            return product_data
            
        except Exception as e:
            print(f"    ✗ Lỗi cào sản phẩm: {str(e)}")
            return None
    
    def go_to_next_page(self, current_page):
        """
        Chuyển sang trang tiếp theo - FIXED VERSION
        """
        next_page = current_page + 1
        
        try:
            # CÁCH 1: Click vào link số trang tiếp theo
            # Ví dụ: <a href="/mua-ban-xe-tp-ho-chi-minh?page=2"><span>2</span></a>
            next_page_link = self.driver.find_element(
                By.XPATH, 
                f"//a[@href='/mua-ban-xe-tp-ho-chi-minh?page={next_page}']"
            )
            
            print(f"\n➡️  Tìm thấy link trang {next_page}, đang click...")
            
            # Scroll đến element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_link)
            time.sleep(1)
            
            # Click
            next_page_link.click()
            time.sleep(4)
            
            print(f"✓ Đã chuyển sang trang {next_page}")
            print(f"✓ URL hiện tại: {self.driver.current_url}")
            return True
            
        except Exception as e1:
            # CÁCH 2: Click vào nút mũi tên phải (rightIcon)
            try:
                right_arrow = self.driver.find_element(
                    By.XPATH,
                    "//button[@class='Paging_redirectPageBtn__KvsqJ']//i[contains(@class, 'rightIcon') and not(contains(@class, 'Disable'))]"
                )
                
                # Click vào button cha
                button = right_arrow.find_element(By.XPATH, "./ancestor::button")
                
                print(f"\n➡️  Tìm thấy nút mũi tên phải, đang click...")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                button.click()
                time.sleep(4)
                
                print(f"✓ Đã chuyển sang trang tiếp theo")
                print(f"✓ URL hiện tại: {self.driver.current_url}")
                return True
                
            except Exception as e2:
                # CÁCH 3: Thay đổi URL trực tiếp
                try:
                    new_url = f"https://www.chotot.com/mua-ban-xe-tp-ho-chi-minh?page={next_page}"
                    print(f"\n➡️  Không tìm thấy nút, đang chuyển URL trực tiếp...")
                    self.driver.get(new_url)
                    time.sleep(4)
                    
                    print(f"✓ Đã chuyển sang trang {next_page}")
                    print(f"✓ URL hiện tại: {self.driver.current_url}")
                    return True
                    
                except Exception as e3:
                    print(f"\n✗ Không thể chuyển trang: {str(e3)}")
                    return False
    
    def scrape_all_pages(self, max_products=100):
        """Cào tất cả sản phẩm từ nhiều trang"""
        print("=" * 70)
        print("BẮT ĐẦU QUY TRÌNH CÀO DỮ LIỆU")
        print("=" * 70)
        
        self.step1_go_to_homepage()
        
        if not self.step2_click_xe_co():
            print("✗ Không thể tiếp tục, dừng lại")
            return
        
        self.step3_click_xem_them()
        
        print("\n" + "=" * 70)
        print("[BƯỚC 4] BẮT ĐẦU CÀO SẢN PHẨM")
        print("=" * 70)
        
        page_num = 1
        
        while len(self.data) < max_products:
            print(f"\n{'='*70}")
            print(f"📄 TRANG {page_num}")
            print(f"🔗 URL: {self.driver.current_url}")
            print(f"{'='*70}")
            
            product_links = self.get_product_links_from_page()
            
            if len(product_links) == 0:
                print("⚠ Không còn sản phẩm, dừng lại")
                break
            
            remaining = max_products - len(self.data)
            product_links = product_links[:remaining]
            
            print(f"\n🔄 Cào {len(product_links)} sản phẩm từ trang này...")
            
            for i, link in enumerate(product_links, 1):
                print(f"\n  [{page_num}.{i}/{len(product_links)}] ", end="")
                product_data = self.scrape_product(link)
                
                if product_data and product_data.get('Tiêu đề'):
                    self.data.append(product_data)
                    print(f"✓ {product_data.get('Tiêu đề', '')[:50]}")
                    print(f"    💰 {product_data.get('Giá', 'N/A')}")
                    
                    spec_count = len([k for k in product_data.keys() if k not in ['URL', 'Tiêu đề', 'Giá']])
                    if spec_count > 0:
                        print(f"    📊 {spec_count} thông số")
                else:
                    print(f"✗ Lỗi")
                
                time.sleep(0.5)
            
            print(f"\n✓ Hoàn thành trang {page_num}")
            print(f"📊 Tổng đã cào: {len(self.data)}/{max_products}")
            
            # Kiểm tra xem còn cào tiếp không
            if len(self.data) >= max_products:
                print("\n🎯 Đã đủ số lượng sản phẩm cần cào")
                break
            
            # Chuyển sang trang tiếp theo
            if not self.go_to_next_page(page_num):
                print("\n⚠ Không thể chuyển trang, dừng lại")
                break
            
            page_num += 1
        
        print(f"\n{'='*70}")
        print(f"🎉 HOÀN TẤT: Đã cào {len(self.data)} sản phẩm")
        print(f"{'='*70}")
    
    def export_to_excel(self, filename='chotot_xemay_data.xlsx'):
        """Xuất dữ liệu ra Excel"""
        if not self.data:
            print("\n✗ Không có dữ liệu để xuất!")
            return
        
        df = pd.DataFrame(self.data)
        
        # Sắp xếp cột
        priority_cols = [
            'URL', 'Tiêu đề', 'Giá',
            'Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Hộp số', 'Nhiên liệu', 
            'Kiểu dáng', 'Số chỗ', 'Trọng lượng', 'Trọng tải',
            'Số Km đã đi', 'Tình trạng', 'Xuất xứ', 
            'Có phụ kiện đi kèm', 'Còn hạn đăng kiểm',
            'Chính sách bảo hành',
            'Loại xe', 'Dung tích xe', 'Loại phụ tùng', 'Mã phụ tùng'
        ]
        
        existing_cols = [col for col in priority_cols if col in df.columns]
        other_cols = [col for col in df.columns if col not in priority_cols]
        df = df[existing_cols + other_cols]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n{'='*70}")
        print(f"💾 ĐÃ LƯU FILE")
        print(f"📁 {filename}")
        print(f"📊 {len(self.data)} sản phẩm, {len(df.columns)} cột")
        print(f"{'='*70}")
    
    def close(self):
        """Đóng browser"""
        self.driver.quit()


def main():
    """Hàm chính"""
    print("🚀 Khởi động Chợ Tốt Scraper (FIXED VERSION)...")
    
    scraper = ChototScraper(headless=True)
    
    try:
        scraper.scrape_all_pages(max_products=100)
        scraper.export_to_excel('chotot_xemay_data.xlsx')
        
    except KeyboardInterrupt:
        print("\n\n⚠ Dừng bởi người dùng")
        if len(scraper.data) > 0:
            scraper.export_to_excel('chotot_partial.xlsx')
    except Exception as e:
        print(f"\n✗ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔒 Đóng browser...")
        scraper.close()
        print("✅ Hoàn tất!")


if __name__ == "__main__":
    main()
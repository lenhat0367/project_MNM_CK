from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

class ChototScraper:
    def __init__(self, headless=True):
        gecko_path = "D:/project_MNM_CK/geckodriver.exe"
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
        
        self.required_columns = [
            'URL', 'Tên sản phẩm', 'Giá', 'Tên người đăng', 'Địa chỉ', 'Thời gian đăng', 'URL hình ảnh',
            'Số Km đã đi', 'Số đời chủ', 'Có phụ kiện đi kèm', 'Còn hạn đăng kiểm',
            'Xuất xứ', 'Tình trạng', 'Chính sách bảo hành',
            'Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Hộp số',
            'Nhiên liệu', 'Kiểu dáng', 'Số chỗ', 
            'Trọng lượng', 'Trọng tải'
        ]
        
        self.itemprop_mappings = {
            'mileage_v2': 'Số Km đã đi',
            'number_of_owners': 'Số đời chủ',
            'include_accessories': 'Có phụ kiện đi kèm',
            'valid_registration': 'Còn hạn đăng kiểm',
            'carorigin': 'Xuất xứ',
            'condition_ad': 'Tình trạng',
            'veh_warranty_policy': 'Chính sách bảo hành',
            'carbrand': 'Hãng xe',
            'carmodel': 'Dòng xe',
            'mfdate': 'Năm sản xuất',
            'gearbox': 'Hộp số',
            'fuel': 'Nhiên liệu',
            'cartype': 'Kiểu dáng',
            'carseats': 'Số chỗ',
            'veh_unladen_weight': 'Trọng lượng',
            'veh_gross_weight': 'Trọng tải'
        }
        
    def get_product_links_from_page(self):
        product_links = []
        
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
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    full_url = 'https://xe.chotot.com' + href
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
        
        print(f"✓ Tìm thấy {len(product_links)} sản phẩm")
        return product_links
    
    def extract_specs_by_itemprop(self, soup):
        specs = {}
        
        for prop, label in self.itemprop_mappings.items():
            elem = soup.find(itemprop=prop)
            if elem:
                value = elem.get_text(strip=True)
                if value:
                    specs[label] = value
        
        return specs
    
    def extract_seller_info(self, soup):
        seller_info = {
            'Tên người đăng': '',
            'Địa chỉ': '',
            'Thời gian đăng': '',
            'URL hình ảnh': ''
        }
        
        try:
            seller_container = soup.find('div', itemprop='seller')
            
            if seller_container:
                pf9ruvz_div = seller_container.find('div', class_=re.compile(r'pf9ruvz'))
                
                if pf9ruvz_div:
                    seller_link = pf9ruvz_div.find('a', href=re.compile(r'/(cua-hang|user)/'))
                    
                    if seller_link:
                        seller_b = seller_link.find('b')
                        if seller_b:
                            seller_name = seller_b.get_text(strip=True)
                            
                            if seller_name and not seller_name.replace('.', '').replace('(', '').replace(')', '').isdigit():
                                if len(seller_name) > 1:
                                    seller_info['Tên người đăng'] = seller_name
            
            if not seller_info['Tên người đăng'] and seller_container:
                all_b_tags = seller_container.find_all('b')
                for b_tag in all_b_tags:
                    parent_a = b_tag.find_parent('a')
                    if parent_a:
                        href = parent_a.get('href', '')
                        if '/cua-hang/' in href or '/user/' in href:
                            name = b_tag.get_text(strip=True)
                            
                            if name and len(name) > 2:
                                if not name.replace('.', '').replace('(', '').replace(')', '').isdigit():
                                    if not any(x in name.lower() for x in ['bán', 'đánh giá', 'rating']):
                                        seller_info['Tên người đăng'] = name
                                        break
            
            time_posted = soup.find('span', class_='bwq0cbs', string=re.compile(r'Đăng.*trước'))
            if time_posted:
                seller_info['Thời gian đăng'] = time_posted.get_text(strip=True)
            else:
                all_spans = soup.find_all('span')
                for span in all_spans:
                    text = span.get_text(strip=True)
                    if 'Đăng' in text and 'trước' in text:
                        seller_info['Thời gian đăng'] = text
                        break
            
            address_spans = soup.find_all('span', class_='bwq0cbs')
            for span in address_spans:
                text = span.get_text(strip=True)
                if len(text) > 15 and any(x in text for x in ['Phường', 'Quận', 'TP', 'Tp', 'Huyện', 'Thành phố', 'Tỉnh']):
                    if 'Đăng' not in text and 'bán' not in text.lower() and 'Phản hồi' not in text:
                        seller_info['Địa chỉ'] = text
                        break
            
            all_imgs = soup.find_all('img', src=True)
            candidate_images = []
            
            for img in all_imgs:
                src = img.get('src', '')
                if not src or any(x in src.lower() for x in ['icon', 'logo', 'static', 'svg']):
                    continue
                
                if 'cdn.chotot.com' in src or 'storage' in src or 'img' in src:
                    width = img.get('width', '')
                    height = img.get('height', '')
                    
                    size = 0
                    if width and str(width).isdigit():
                        size += int(width)
                    if height and str(height).isdigit():
                        size += int(height)
                    
                    candidate_images.append((src, size))
            
            if candidate_images:
                candidate_images.sort(key=lambda x: x[1], reverse=True)
                seller_info['URL hình ảnh'] = candidate_images[0][0]
            
            if not seller_info['URL hình ảnh']:
                for img in all_imgs:
                    src = img.get('src', '')
                    if src and src.startswith('http'):
                        seller_info['URL hình ảnh'] = src
                        break
                        
        except Exception as e:
            print(f"Lỗi lấy thông tin người bán: {str(e)}")
        
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
            if title_elem:
                product_data['Tên sản phẩm'] = title_elem.get_text(strip=True)
            
            price_elem = soup.find('b', class_='p26z2wb')
            if price_elem:
                product_data['Giá'] = price_elem.get_text(strip=True)
            else:
                price_patterns = [
                    soup.find(string=re.compile(r'\d+\.\d+\.\d+ đ')),
                    soup.find(string=re.compile(r'\d+ triệu')),
                    soup.find(string=re.compile(r'\d+\.\d+ tỷ')),
                ]
                for p in price_patterns:
                    if p:
                        product_data['Giá'] = p.strip()
                        break
            
            seller_info = self.extract_seller_info(soup)
            product_data.update(seller_info)
            
            specs = self.extract_specs_by_itemprop(soup)
            product_data.update(specs)
            
            return product_data
            
        except Exception as e:
            print(f"✗ Lỗi: {str(e)}")
            return None
    
    def go_to_next_page_direct(self, next_page):
        try:
            new_url = f"https://xe.chotot.com/mua-ban-oto-tp-ho-chi-minh?page={next_page}"
            print(f"\n➡️  Chuyển sang trang {next_page}...")
            self.driver.get(new_url)
            time.sleep(4)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = soup.find_all('a', href=re.compile(r'/mua-ban.*\d+'))
            
            return len(products) > 0
                
        except Exception as e:
            print(f"\n✗ Lỗi: {str(e)}")
            return False
    
    def scrape_test_pages(self, start_url, num_pages=2):
        self.driver.get(start_url)
        time.sleep(3)
        
        for page_num in range(1, num_pages + 1):

            print(f"TRANG {page_num}/{num_pages}")
            
            if page_num > 1:
                if not self.go_to_next_page_direct(page_num):
                    break
            
            product_links = self.get_product_links_from_page()
            
            if not product_links:
                print(f"Trang trống!")
                break
            
            for i, link in enumerate(product_links, 1):
                print(f"[{page_num}.{i}/{len(product_links)}] Đang cào...")
                
                product_data = self.scrape_product(link)
                
                if product_data and product_data.get('Tên sản phẩm'):
                    self.data.append(product_data)
                    print(f"{product_data.get('Tên sản phẩm', '')[:50]}")
                else:
                    print(f"Lỗi")
                
                time.sleep(1)
        
        print(f"HOÀN TẤT: {len(self.data)} sản phẩm")
    
    def export_to_excel(self, filename='chotot_final.xlsx'):
        if not self.data:
            print("\nKhông có dữ liệu!")
            return
        
        df = pd.DataFrame(self.data)
        
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[self.required_columns]
        df.to_excel(filename, index=False, engine='openpyxl')
    
    def close(self):
        self.driver.quit()


def main():
    url = "https://xe.chotot.com/mua-ban-oto-tp-ho-chi-minh"
    scraper = ChototScraper(headless=True)
    
    try:
        scraper.scrape_test_pages(url, num_pages=2)
        scraper.export_to_excel('chotot_final.xlsx')
        
    except KeyboardInterrupt:
        print("\n\nDừng")
        if scraper.data:
            scraper.export_to_excel('chotot_interrupted.xlsx')
    except Exception as e:
        print(f"\nLỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        if scraper.data:
            scraper.export_to_excel('chotot_error.xlsx')
    finally:
        print("\nĐóng browser...")
        scraper.close()
        print("Hoàn tất!")


if __name__ == "__main__":
    main()
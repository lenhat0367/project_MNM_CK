from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

class ChototScraper:
    def __init__(self, headless=True):
        """Khởi tạo scraper"""
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
        
        # DANH SÁCH CỘT
        self.required_columns = [
            'URL', 'Tên sản phẩm', 'Giá', 'Tên người đăng', 'Địa chỉ', 'Thời gian đăng', 'URL hình ảnh',
            'Số Km đã đi', 'Số đời chủ', 'Có phụ kiện đi kèm', 'Còn hạn đăng kiểm',
            'Xuất xứ', 'Tình trạng', 'Chính sách bảo hành',
            'Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Hộp số',
            'Nhiên liệu', 'Kiểu dáng', 'Số chỗ', 
            'Trọng lượng', 'Trọng tải'
        ]
        
        # MAPPING ITEMPROP
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
        """Lấy links sản phẩm"""
        product_links = []
        print(f"📥 Đang scroll...")
        
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
        """Cào theo itemprop"""
        specs = {}
        
        print(f"    🔑 Tìm theo itemprop...")
        
        for prop, label in self.itemprop_mappings.items():
            elem = soup.find(itemprop=prop)
            if elem:
                value = elem.get_text(strip=True)
                if value:
                    specs[label] = value
                    print(f"       ✓ {label}: {value}")
        
        print(f"    ✅ Tìm được {len(specs)} thông số")
        return specs
    
    def extract_seller_info(self, soup):
        """Cào thông tin người bán - VERSION 8.1 FIX HOÀN TOÀN"""
        seller_info = {
            'Tên người đăng': '',
            'Địa chỉ': '',
            'Thời gian đăng': '',
            'URL hình ảnh': ''
        }
        
        try:
            # ===== FIX TÊN NGƯỜI ĐĂNG - LẤY CẢ CỬA HÀNG VÀ CÁ NHÂN =====
            # Tìm div chứa thông tin seller
            seller_container = soup.find('div', itemprop='seller')
            
            if seller_container:
                # Method 1: Tìm trong div class="pf9ruvz" (chứa tên)
                pf9ruvz_div = seller_container.find('div', class_=re.compile(r'pf9ruvz'))
                
                if pf9ruvz_div:
                    # Tìm thẻ <a> với href chứa "/cua-hang/" HOẶC "/user/"
                    seller_link = pf9ruvz_div.find('a', href=re.compile(r'/(cua-hang|user)/'))
                    
                    if seller_link:
                        seller_b = seller_link.find('b')
                        if seller_b:
                            seller_name = seller_b.get_text(strip=True)
                            
                            # Lọc: không phải số rating và đủ dài
                            if seller_name and not seller_name.replace('.', '').replace('(', '').replace(')', '').isdigit():
                                if len(seller_name) > 1:  # Tên ít nhất 2 ký tự
                                    seller_info['Tên người đăng'] = seller_name
                                    print(f"       ✓ Tên người đăng: {seller_name}")
            
            # Backup method: Tìm tất cả <b> trong itemprop="seller"
            if not seller_info['Tên người đăng'] and seller_container:
                all_b_tags = seller_container.find_all('b')
                for b_tag in all_b_tags:
                    # Kiểm tra thẻ b này có nằm trong link /cua-hang/ hoặc /user/ không
                    parent_a = b_tag.find_parent('a')
                    if parent_a:
                        href = parent_a.get('href', '')
                        if '/cua-hang/' in href or '/user/' in href:
                            name = b_tag.get_text(strip=True)
                            
                            # Loại bỏ rating số, text ngắn, text có "bán"/"Đánh giá"
                            if name and len(name) > 2:
                                # Kiểm tra không phải số (rating)
                                if not name.replace('.', '').replace('(', '').replace(')', '').isdigit():
                                    # Kiểm tra không chứa từ không mong muốn
                                    if not any(x in name.lower() for x in ['bán', 'đánh giá', 'rating']):
                                        seller_info['Tên người đăng'] = name
                                        print(f"       ✓ Tên người đăng (backup): {name}")
                                        break
            
            # ===== THỜI GIAN ĐĂNG BÀI =====
            # Pattern: "Đăng X ngày trước" hoặc "Đăng X giờ trước" hoặc "Đăng X phút trước"
            time_posted = soup.find('span', class_='bwq0cbs', string=re.compile(r'Đăng.*trước'))
            if time_posted:
                seller_info['Thời gian đăng'] = time_posted.get_text(strip=True)
                print(f"       ✓ Thời gian đăng: {seller_info['Thời gian đăng']}")
            else:
                # Backup: Tìm trong tất cả span
                all_spans = soup.find_all('span')
                for span in all_spans:
                    text = span.get_text(strip=True)
                    if 'Đăng' in text and 'trước' in text:
                        seller_info['Thời gian đăng'] = text
                        print(f"       ✓ Thời gian đăng (backup): {text}")
                        break
            
            # ===== ĐỊA CHỈ =====
            address_spans = soup.find_all('span', class_='bwq0cbs')
            for span in address_spans:
                text = span.get_text(strip=True)
                # Địa chỉ thường dài và chứa địa danh
                if len(text) > 15 and any(x in text for x in ['Phường', 'Quận', 'TP', 'Tp', 'Huyện', 'Thành phố', 'Tỉnh']):
                    # Không lấy text có "Đăng", "đã bán", "đang bán"
                    if 'Đăng' not in text and 'bán' not in text.lower() and 'Phản hồi' not in text:
                        seller_info['Địa chỉ'] = text
                        print(f"       ✓ Địa chỉ: {text}")
                        break
            
            # ===== URL HÌNH ẢNH =====
            all_imgs = soup.find_all('img', src=True)
            candidate_images = []
            
            for img in all_imgs:
                src = img.get('src', '')
                if not src or any(x in src.lower() for x in ['icon', 'logo', 'static', 'svg']):
                    continue
                
                # Ưu tiên ảnh từ CDN
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
                print(f"       ✓ URL hình ảnh: {seller_info['URL hình ảnh'][:60]}...")
            
            if not seller_info['URL hình ảnh']:
                for img in all_imgs:
                    src = img.get('src', '')
                    if src and src.startswith('http'):
                        seller_info['URL hình ảnh'] = src
                        print(f"       ✓ URL hình ảnh (backup): {src[:60]}...")
                        break
                        
        except Exception as e:
            print(f"       ⚠️ Lỗi lấy thông tin người bán: {str(e)}")
        
        return seller_info
    
    def scrape_product(self, url):
        """Cào thông tin chi tiết"""
        try:
            self.driver.get(url)
            time.sleep(4)
            
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1)*800});")
                time.sleep(1.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product_data = {'URL': url, 'Tên sản phẩm': '', 'Giá': ''}
            
            # Lấy tiêu đề
            title_elem = soup.find('h1')
            if title_elem:
                product_data['Tên sản phẩm'] = title_elem.get_text(strip=True)
            
            # Lấy giá
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
            
            # Lấy thông tin người bán, địa chỉ, thời gian, hình ảnh
            seller_info = self.extract_seller_info(soup)
            product_data.update(seller_info)
            
            # Lấy thông số kỹ thuật
            specs = self.extract_specs_by_itemprop(soup)
            product_data.update(specs)
            
            return product_data
            
        except Exception as e:
            print(f"    ✗ Lỗi: {str(e)}")
            return None
    
    def go_to_next_page_direct(self, next_page):
        """Chuyển trang"""
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
        """CÀO TEST"""
        print("=" * 70)
        print("🔧 Chợ Tốt Scraper - Version 8.1 FINAL")
        print("=" * 70)
        print(f"🔗 URL: {start_url}\n")
        
        self.driver.get(start_url)
        time.sleep(3)
        print(f"✓ Đã vào: {self.driver.title}\n")
        
        for page_num in range(1, num_pages + 1):
            print(f"\n{'='*70}")
            print(f"📄 TRANG {page_num}/{num_pages}")
            print(f"{'='*70}")
            
            if page_num > 1:
                if not self.go_to_next_page_direct(page_num):
                    break
            
            product_links = self.get_product_links_from_page()
            
            if not product_links:
                print(f"⚠ Trang trống!")
                break
            
            print(f"\n🔄 Cào {len(product_links)} sản phẩm...\n")
            
            for i, link in enumerate(product_links, 1):
                print(f"{'='*50}")
                print(f"  [{page_num}.{i}/{len(product_links)}]")
                print(f"{'='*50}")
                
                product_data = self.scrape_product(link)
                
                if product_data and product_data.get('Tên sản phẩm'):
                    self.data.append(product_data)
                    print(f"  ✅ {product_data.get('Tên sản phẩm', '')[:50]}")
                    print(f"     💰 {product_data.get('Giá', 'N/A')}")
                    print(f"     👤 {product_data.get('Tên người đăng', 'N/A')}")
                    print(f"     ⏰ {product_data.get('Thời gian đăng', 'N/A')}")
                    
                    spec_count = len([k for k in product_data.keys() if k not in ['URL', 'Tên sản phẩm', 'Giá', 'Tên người đăng', 'Địa chỉ', 'Thời gian đăng', 'URL hình ảnh']])
                    print(f"     📊 {spec_count} thông số")
                else:
                    print(f"  ✗ Lỗi")
                
                time.sleep(1)
        
        print(f"\n{'='*70}")
        print(f"🎉 HOÀN TẤT: {len(self.data)} sản phẩm")
        print(f"{'='*70}")
    
    def export_to_excel(self, filename='chotot_final_v8.xlsx'):
        """Xuất Excel với thống kê chi tiết"""
        if not self.data:
            print("\n✗ Không có dữ liệu!")
            return
        
        df = pd.DataFrame(self.data)
        
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[self.required_columns]
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n{'='*70}")
        print(f"💾 ĐÃ LƯU: {filename}")
        print(f"📊 {len(self.data)} sản phẩm × {len(self.required_columns)} cột")
        print(f"{'='*70}")
        
        print(f"\n📊 THỐNG KÊ:")
        
        print(f"\n   👤 THÔNG TIN NGƯỜI BÁN:")
        seller_fields = ['Tên người đăng', 'Địa chỉ', 'Thời gian đăng', 'URL hình ảnh']
        
        for col in seller_fields:
            if col in df.columns:
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                pct = non_empty*100//len(df) if len(df) > 0 else 0
                status = "✅" if pct >= 50 else "⚠️"
                print(f"      {status} {col}: {non_empty}/{len(df)} ({pct}%)")
        
        print(f"\n   🚗 THÔNG SỐ XE:")
        spec_fields = ['Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Hộp số', 'Nhiên liệu', 'Số Km đã đi']
        
        for col in spec_fields:
            if col in df.columns:
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                pct = non_empty*100//len(df) if len(df) > 0 else 0
                status = "✅" if pct > 50 else "⚠️"
                print(f"      {status} {col}: {non_empty}/{len(df)} ({pct}%)")
        
        print(f"\n{'='*70}")
    
    def close(self):
        """Đóng browser"""
        self.driver.quit()


def main():
    """Hàm chính"""
    print("🚀 Chợ Tốt Scraper - Version 8.1 FINAL")
    print("=" * 70)
    print("📋 Fix HOÀN TOÀN:")
    print("   ✓ Lấy tên CẢ cửa hàng (/cua-hang/) VÀ cá nhân (/user/)")
    print("   ✓ Tìm trong <div itemprop='seller'>")
    print("   ✓ Lọc chặt rating số và text không mong muốn")
    print("   ✓ Thêm cột 'Thời gian đăng'")
    print("=" * 70)
    print()
    
    url = "https://xe.chotot.com/mua-ban-oto-tp-ho-chi-minh"
    scraper = ChototScraper(headless=True)
    
    try:
        scraper.scrape_test_pages(url, num_pages=2)
        scraper.export_to_excel('chotot_final_v8.1.xlsx')
        
    except KeyboardInterrupt:
        print("\n\n⚠ Dừng")
        if scraper.data:
            scraper.export_to_excel('chotot_interrupted_v8.1.xlsx')
    except Exception as e:
        print(f"\n✗ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        if scraper.data:
            scraper.export_to_excel('chotot_error_v8.1.xlsx')
    finally:
        print("\n🔒 Đóng browser...")
        scraper.close()
        print("✅ Hoàn tất!")


if __name__ == "__main__":
    main()
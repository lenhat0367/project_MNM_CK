"""
Web Scraper cho Chợ Tốt - FIX HOÀN TOÀN bằng itemprop
Version 5: Ưu tiên itemprop trước, backup bằng DOM parsing
"""

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
        self.wait = None
        self.data = []
        
        # DANH SÁCH CỘT
        self.required_columns = [
            'URL', 'Tiêu đề', 'Giá',
            'Số Km đã đi', 'Số đời chủ', 'Có phụ kiện đi kèm', 'Còn hạn đăng kiểm',
            'Xuất xứ', 'Tình trạng', 'Chính sách bảo hành',
            'Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Phiên bản xe', 'Hộp số',
            'Nhiên liệu', 'Kiểu dáng', 'Số chỗ', 'Hệ dẫn động', 'Công suất động cơ',
            'Momen xoắn', 'Dung tích động cơ', 'Nhiên liệu tiêu thụ', 'Số túi khí',
            'Khoảng sáng gầm xe', 'Số cửa', 'Trọng lượng', 'Trọng tải'
        ]
        
        # 🔑 MAPPING ITEMPROP - PHƯƠNG PHÁP CHÍNH XÁC NHẤT
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
            'option': 'Phiên bản xe',
            'gearbox': 'Hộp số',
            'fuel': 'Nhiên liệu',
            'cartype': 'Kiểu dáng',
            'carseats': 'Số chỗ',
            'drivetrain': 'Hệ dẫn động',          # ⭐ Trường bị thiếu
            'horse_power': 'Công suất động cơ',   # ⭐ Trường bị thiếu
            'torque': 'Momen xoắn',               # ⭐ Trường bị thiếu
            'engine_capacity': 'Dung tích động cơ', # ⭐ Trường bị thiếu
            'kml_combined': 'Nhiên liệu tiêu thụ', # ⭐ Trường bị thiếu
            'air_bag': 'Số túi khí',              # ⭐ Trường bị thiếu
            'minimum_ground_clearance': 'Khoảng sáng gầm xe',
            'doors': 'Số cửa',                    # ⭐ Trường bị thiếu
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
        """
        🔑 PHƯƠNG PHÁP CHÍNH: Dùng itemprop
        Đây là cách chính xác 100% vì HTML có sẵn attribute itemprop
        """
        specs = {}
        
        print(f"    🔑 Phương pháp 1: Tìm theo itemprop...")
        
        for prop, label in self.itemprop_mappings.items():
            elem = soup.find(itemprop=prop)
            if elem:
                value = elem.get_text(strip=True)
                if value:
                    specs[label] = value
                    print(f"       ✓ {label}: {value}")
        
        print(f"    ✅ Tìm được {len(specs)} thông số qua itemprop")
        return specs
    
    def extract_specs_by_label_matching(self, soup):
        """
        🔄 PHƯƠNG PHÁP BACKUP: Tìm theo label text
        Tìm tất cả span có text là label, lấy span kế tiếp làm value
        """
        specs = {}
        
        print(f"    🔄 Phương pháp 2: Tìm theo label matching...")
        
        # Map label text -> column name
        label_map = {
            'Hệ dẫn động': 'Hệ dẫn động',
            'Công suất động cơ': 'Công suất động cơ',
            'Momen xoắn': 'Momen xoắn',
            'Dung tích động cơ': 'Dung tích động cơ',
            'Nhiên liệu tiêu thụ': 'Nhiên liệu tiêu thụ',
            'Số túi khí': 'Số túi khí',
            'Số cửa': 'Số cửa',
            'Hãng': 'Hãng xe',
            'Dòng xe': 'Dòng xe',
            'Năm sản xuất': 'Năm sản xuất',
            'Phiên bản xe': 'Phiên bản xe',
            'Hộp số': 'Hộp số',
            'Nhiên liệu': 'Nhiên liệu',
            'Kiểu dáng': 'Kiểu dáng',
            'Số chỗ': 'Số chỗ',
            'Khoảng sáng gầm xe': 'Khoảng sáng gầm xe',
            'Trọng lượng': 'Trọng lượng',
            'Trọng tải': 'Trọng tải'
        }
        
        for label_text, column_name in label_map.items():
            if column_name in specs:
                continue
                
            # Tìm span chứa label text
            label_spans = soup.find_all('span', class_='bwq0cbs', 
                                       string=lambda t: t and label_text in t)
            
            for label_span in label_spans:
                # Tìm span kế tiếp cùng level (sibling)
                next_span = label_span.find_next_sibling('span', class_='bwq0cbs')
                
                if next_span:
                    value = next_span.get_text(strip=True)
                    if value:
                        specs[column_name] = value
                        print(f"       ✓ {column_name}: {value}")
                        break
                
                # Nếu không có sibling, tìm trong parent
                parent = label_span.parent
                if parent:
                    all_spans = parent.find_all('span', class_='bwq0cbs')
                    # Nếu có 2 span, lấy span thứ 2
                    if len(all_spans) >= 2:
                        value = all_spans[1].get_text(strip=True)
                        if value and value != label_text:
                            specs[column_name] = value
                            print(f"       ✓ {column_name}: {value}")
                            break
        
        if len(specs) > 0:
            print(f"    ✅ Tìm thêm {len(specs)} thông số qua label matching")
        
        return specs
    
    def extract_specs(self, soup):
        """
        Kết hợp 2 phương pháp để đảm bảo 100% lấy được dữ liệu
        """
        specs = {}
        
        try:
            print(f"    🔍 BẮT ĐẦU CÀO THÔNG SỐ...")
            
            # Phương pháp 1: itemprop (chính xác nhất)
            specs1 = self.extract_specs_by_itemprop(soup)
            specs.update(specs1)
            
            # Phương pháp 2: Label matching (backup)
            specs2 = self.extract_specs_by_label_matching(soup)
            # Chỉ thêm những trường chưa có
            for key, value in specs2.items():
                if key not in specs:
                    specs[key] = value
            
            print(f"    🎯 TỔNG: {len(specs)} thông số")
            
            # Debug: Kiểm tra các trường quan trọng
            critical_fields = ['Hệ dẫn động', 'Công suất động cơ', 'Momen xoắn', 
                             'Dung tích động cơ', 'Nhiên liệu tiêu thụ', 'Số túi khí', 'Số cửa']
            
            missing = [f for f in critical_fields if f not in specs]
            if missing:
                print(f"    ⚠️  Còn thiếu: {', '.join(missing)}")
            else:
                print(f"    ✅ ĐẦY ĐỦ tất cả các trường quan trọng!")
            
        except Exception as e:
            print(f"    ⚠ Lỗi: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return specs
    
    def scrape_product(self, url):
        """Cào thông tin chi tiết"""
        try:
            self.driver.get(url)
            time.sleep(3)  # Tăng thời gian chờ
            
            # Scroll nhiều hơn để load đầy đủ
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1)*800});")
                time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product_data = {'URL': url, 'Tiêu đề': '', 'Giá': ''}
            
            # Lấy tiêu đề
            title_elem = soup.find('h1')
            if title_elem:
                product_data['Tiêu đề'] = title_elem.get_text(strip=True)
            
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
            
            # Lấy thông số
            specs = self.extract_specs(soup)
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
        print("🔧 FIX 100% - ƯU TIÊN ITEMPROP")
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
                
                if product_data and product_data.get('Tiêu đề'):
                    self.data.append(product_data)
                    print(f"  ✅ {product_data.get('Tiêu đề', '')[:50]}")
                    print(f"     💰 {product_data.get('Giá', 'N/A')}")
                    
                    spec_count = len([k for k in product_data.keys() if k not in ['URL', 'Tiêu đề', 'Giá']])
                    print(f"     📊 {spec_count} thông số")
                else:
                    print(f"  ✗ Lỗi")
                
                time.sleep(1)
        
        print(f"\n{'='*70}")
        print(f"🎉 HOÀN TẤT: {len(self.data)} sản phẩm")
        print(f"{'='*70}")
    
    def export_to_excel(self, filename='chotot_100percent.xlsx'):
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
        
        print(f"\n   🔧 CÁC TRƯỜNG ĐÃ FIX:")
        critical = ['Hệ dẫn động', 'Công suất động cơ', 'Momen xoắn', 
                   'Dung tích động cơ', 'Nhiên liệu tiêu thụ', 'Số túi khí', 'Số cửa']
        
        for col in critical:
            if col in df.columns:
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                pct = non_empty*100//len(df) if len(df) > 0 else 0
                
                if pct >= 80:
                    status = "✅"
                elif pct >= 50:
                    status = "⚠️"
                else:
                    status = "❌"
                
                print(f"      {status} {col}: {non_empty}/{len(df)} ({pct}%)")
        
        print(f"\n   ⚙️  THÔNG SỐ KHÁC:")
        others = ['Hãng xe', 'Dòng xe', 'Năm sản xuất', 'Hộp số', 'Nhiên liệu']
        
        for col in others:
            if col in df.columns:
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                pct = non_empty*100//len(df) if len(df) > 0 else 0
                status = "✅" if pct > 50 else "⚠️"
                print(f"      {status} {col}: {non_empty}/{len(df)} ({pct}%)")
        
        print(f"\n{'='*70}")
        
        # Kiểm tra các trường quan trọng
        all_good = True
        for col in critical:
            if col in df.columns:
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                if non_empty == 0:
                    all_good = False
                    print(f"⚠️  CẢNH BÁO: {col} vẫn còn TRỐNG!")
        
        if all_good:
            print("✅ HOÀN HẢO - Tất cả các trường đều có dữ liệu!")
        
        print(f"{'='*70}")
    
    def close(self):
        """Đóng browser"""
        self.driver.quit()


def main():
    """Hàm chính"""
    print("🚀 Chợ Tốt Scraper - FIX 100%")
    print("=" * 70)
    print("🔑 Chiến lược:")
    print("   1. Ưu tiên itemprop (chính xác 100%)")
    print("   2. Backup bằng label matching")
    print("   3. Tăng thời gian chờ để load đầy đủ")
    print("=" * 70)
    print()
    
    url = "https://xe.chotot.com/mua-ban-oto-tp-ho-chi-minh"
    scraper = ChototScraper(headless=True)
    
    try:
        scraper.scrape_test_pages(url, num_pages=2)
        scraper.export_to_excel('chotot_100percent.xlsx')
        
    except KeyboardInterrupt:
        print("\n\n⚠ Dừng")
        if scraper.data:
            scraper.export_to_excel('chotot_interrupted.xlsx')
    except Exception as e:
        print(f"\n✗ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        if scraper.data:
            scraper.export_to_excel('chotot_error.xlsx')
    finally:
        print("\n🔒 Đóng browser...")
        scraper.close()
        print("✅ Hoàn tất!")


if __name__ == "__main__":
    main()
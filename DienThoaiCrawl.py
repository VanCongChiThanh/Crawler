from flask import Flask, jsonify, request
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pyodbc
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Hàm khởi tạo trình duyệt
def init_driver():
    # try:
    #     driver = webdriver.Chrome()
    #     return driver
    # except Exception as e:
    #     print(f"Error initializing Chrome driver: {e}")
    #     raise
    try:
        options = Options()
        options.add_argument("--headless")  # Chế độ headless
        options.add_argument("--disable-gpu")  # Tắt GPU
        options.add_argument("--window-size=1920x1080")  # Đặt kích thước cửa sổ (giả lập màn hình lớn hơn)
        options.add_argument("--disable-extensions")  # Tắt các extension
        options.add_argument("--proxy-server='direct://'")  # Bỏ qua proxy
        options.add_argument("--proxy-bypass-list=*")  # Bỏ qua tất cả proxy
        options.add_argument("--start-maximized")  # Mở trình duyệt với kích thước lớn nhất
        options.add_argument("--disable-dev-shm-usage")  # Khắc phục giới hạn bộ nhớ chia sẻ
        options.add_argument("--no-sandbox")  # Vô hiệu hóa sandbox, đặc biệt khi chạy trong container
        options.add_argument("--disable-infobars")  # Tắt thanh thông tin của Chrome
        options.add_argument('--disable-application-cache')  # Tắt cache của ứng dụng
        options.add_argument('--disable-software-rasterizer')  # Tắt việc xử lý đồ họa bằng phần mềm
        options.add_argument('--disable-web-security')  # Vô hiệu hóa bảo mật web nếu cần thiết

        service = Service()  # Tạo dịch vụ cho ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        raise

# Hàm mở trang web và click vào nút "Xem thêm" nếu có
def load_all_products(driver, url, site_name):
    driver.get(url)
    
    if site_name == "clickbuy":
        close_popup(driver)  # Đóng popup nếu là ClickBuy
    
    while True:
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Xem thêm')] | //a[contains(., 'Xem thêm')]"))
            )
            load_more_button.click()
            time.sleep(3)
        except Exception as e:
            print(f"Không tìm thấy nút 'Xem thêm' nữa hoặc đã tải hết sản phẩm. Error: {e}")
            break

# Hàm kiểm tra và đóng nút "Đóng" trên trang ClickBuy
def close_popup(driver):
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.close-modal.icon-minutes"))
        )
        close_button.click()
        print("Đã đóng popup trên trang ClickBuy.")
    except Exception as e:
        print(f"Không tìm thấy nút 'Đóng' trên trang ClickBuy. Error: {e}")

# Hàm lấy thông tin sản phẩm từ bất kỳ trang web nào
def get_product_info(driver, name_selector, price_selector, link_selector, image_selector):
    products_data = []
    products = driver.find_elements(By.CSS_SELECTOR, link_selector)

    for product in products:
        try:

            name = product.find_element(By.CSS_SELECTOR, name_selector).text
            price = product.find_element(By.CSS_SELECTOR, price_selector).text
            link = product.get_attribute('href')
            image_url = product.find_element(By.CSS_SELECTOR, image_selector).get_attribute('src')

            products_data.append({
                'product_name': name,
                'product_price': price,
                'product_link': link,
                'product_image': image_url
            })
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu sản phẩm: {e}")

    return products_data

# Hàm lưu dữ liệu vào DataFrame và xuất file
def save_to_dataframe(products_data, file_name):
    df = pd.DataFrame(products_data)
    df.to_csv(f'{file_name}.csv', encoding='utf-8-sig', index=False)
    print(f"Lưu dữ liệu vào {file_name}.csv thành công!")

# Kết nối chung cho toàn bộ chương trình
conn_str = "Driver={SQL Server};Server=DESKTOP-KKVDHC9\\SQLEXPRESS;Database=PriceCompare;Trusted_Connection=yes;"

def clean_price(price_str):
    if price_str.strip().lower() in ["liên hệ", "call", "contact", "on request"]:
        return None
    cleaned_price = re.sub(r'[^\d]', '', price_str)
    try:
        return int(cleaned_price)
    except ValueError:
        return None

def site_id_mapping(site_name):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        # Kiểm tra xem site_name đã tồn tại hay chưa
        cursor.execute("SELECT id FROM Websites WHERE LOWER(name) = ?", (site_name.lower(),))
        website = cursor.fetchone()
        
        if website:  # Nếu đã tồn tại, trả về id
            print(f"Website '{site_name}' đã tồn tại. ID: {website[0]}")
            return website[0]
        
        # Nếu chưa tồn tại, thêm bản ghi mới với url và url_logo để ''
        insert_query = """
            INSERT INTO Websites (name, url, url_logo) 
            OUTPUT INSERTED.id
            VALUES (?, '', '');
        """
        cursor.execute(insert_query, (site_name,))
        
        new_website_id = cursor.fetchone()
        
        # Debug: Xác nhận giá trị trả về
        if new_website_id:
            print(f"Website '{site_name}' được thêm mới. ID: {new_website_id[0]}")
            conn.commit()  
            return new_website_id[0]
        else:
            print(f"Không thể lấy ID của website vừa thêm: {site_name}")
            conn.rollback()
            return None
    except Exception as e:
        conn.rollback()  
        print(f"Error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def normalize_product_name(product_name, category_id):
    if category_id == 1:
        normalized_name = product_name.lower()
        if "b" in normalized_name:
            normalized_name = normalized_name.split("b", 1)[0] + "b"
        return normalized_name.strip()
    else:
        # Chuẩn hóa tên cho các category khác
        # Loại bỏ khoảng trắng, dấu ngoặc
        normalized_name = re.sub(r'[()\[\]{}]', '', product_name).strip()
        normalized_name = ' '.join(normalized_name.split())  # Loại bỏ khoảng trắng thừa
        return normalized_name

# Hàm thêm hoặc cập nhật sản phẩm vào cơ sở dữ liệu
def add_or_update_product(product_name, category_id, image_url, website_id, price, product_url):
    normalized_product_name = normalize_product_name(product_name, category_id)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        # Kiểm tra sản phẩm đã tồn tại chưa
        product_query = """
            SELECT id FROM Products 
            WHERE LOWER(name) LIKE ?;
        """
        cursor.execute(product_query, ('%' + normalized_product_name + '%',))
        product = cursor.fetchone()

        if product:
            product_id = product[0]
            price_query = """
                SELECT id FROM ProductPrices 
                WHERE product_id = ? AND website_id = ? AND url = ?;
            """
            cursor.execute(price_query, (product_id, website_id, product_url))
            price_record = cursor.fetchone()

            if price_record:
                # Nếu giá đã tồn tại thì cập nhật giá
                update_price_query = """
                    UPDATE ProductPrices 
                    SET price = ? 
                    WHERE id = ?;
                """
                cursor.execute(update_price_query, (price if price is not None else 0, price_record[0]))
            else:
                # Thêm giá mới
                insert_price_query = """
                    INSERT INTO ProductPrices (product_id, website_id, price, url) 
                    VALUES (?, ?, ?, ?);
                """
                cursor.execute(insert_price_query, (product_id, website_id, price if price is not None else 0, product_url))

                # Kiểm tra dữ liệu sau khi chèn
                cursor.execute("""
                    SELECT * FROM ProductPrices WHERE product_id = ? AND website_id = ? AND url = ?;
                """, (product_id, website_id, product_url))

        else:
            # Nếu sản phẩm chưa tồn tại thì thêm mới
            insert_product_query = """
                INSERT INTO Products (name, image_url, category_id) 
                OUTPUT INSERTED.id
                VALUES (?, ?, ?);
            """
            cursor.execute(insert_product_query, (normalized_product_name, image_url, category_id))
            product_id = cursor.fetchone()[0]
            # Thêm giá cho sản phẩm mới
            insert_price_query = """
                INSERT INTO ProductPrices (product_id, website_id, price, url) 
                VALUES (?, ?, ?, ?);
            """
            cursor.execute(insert_price_query, (product_id, website_id, price if price is not None else 0, product_url))

            # Kiểm tra dữ liệu sau khi chèn
            cursor.execute("""
                SELECT * FROM ProductPrices WHERE product_id = ? AND website_id = ? AND url = ?;
            """, (product_id, website_id, product_url))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()


# API crawl sản phẩm từ các trang web, trả về JSON
@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.get_json()

    site_name = data.get('site_name')
    url = data.get('url')
    category_id = data.get('category_id')
    selectors = data.get('selectors')

    driver = init_driver()
    products_data = []
    try:
        print(f"Đang lấy dữ liệu từ {site_name}...")

        load_all_products(driver, url, site_name)

        products_data = get_product_info(
            driver,
            name_selector=selectors['name_selector'],
            price_selector=selectors['price_selector'],
            link_selector=selectors['link_selector'],
            image_selector=selectors['image_selector']
        )
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        driver.quit()

    return jsonify(products_data)

# API thêm sản phẩm vào cơ sở dữ liệu hàng loạt
@app.route('/add_products', methods=['POST'])
def add_products():
    data = request.get_json()
    products = data.get('products')
    category_id = data.get('category_id')
    site_name = data.get('site_name')
    print(f"Site name received: {site_name}") 
    website_id = site_id_mapping(site_name)
    
    for product in products:
        product_name = product['product_name']
        product_price = clean_price(product['product_price'])
        product_link = product['product_link']
        product_image = product['product_image']
        
        add_or_update_product(
            product_name=product_name,
            category_id=category_id,
            image_url=product_image,
            website_id=website_id,
            price=product_price,
            product_url=product_link
        )
    
    return jsonify({'status': 'success', 'message': 'Products added successfully'})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
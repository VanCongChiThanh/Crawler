from flask import Flask, jsonify, request
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyodbc
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

# Hàm khởi tạo trình duyệt
def init_driver():
    try:
        driver = webdriver.Chrome()
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
            # Tìm nút "Xem thêm" bằng văn bản
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
                'Tên sản phẩm': name,
                'Giá sản phẩm': price,
                'Link sản phẩm': link,
                'URL ảnh sản phẩm': image_url
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
conn_str = "Driver={SQL Server};Server=DESKTOP-KKVDHC9\\SQLEXPRESS;Database=BestPriceDB;Trusted_Connection=yes;"

def clean_price(price_str):
    if price_str.strip().lower() in ["liên hệ", "call", "contact", "on request"]:
        return None
    cleaned_price = re.sub(r'[^\d]', '', price_str)
    try:
        return int(cleaned_price)
    except ValueError:
        return None

def site_id_mapping(site_name):
    mapping = {
        "didongviet": 1,
        "clickbuy": 2,
        "minhtuanmobile": 3,
    }
    return mapping.get(site_name, None)

def normalize_product_name(product_name):
    normalized_name = product_name.lower()
    if "b" in normalized_name:
        normalized_name = normalized_name.split("b", 1)[0] + "b"
    normalized_name = normalized_name.strip()
    return normalized_name

def add_or_update_product(product_name, category_id, image_url, website_id, price, product_url):
    normalized_product_name = normalize_product_name(product_name)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
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
                update_price_query = """
                    UPDATE ProductPrices 
                    SET price = ? 
                    WHERE id = ?;
                """
                cursor.execute(update_price_query, (price if price is not None else 0, price_record[0]))
            else:
                insert_price_query = """
                    INSERT INTO ProductPrices (product_id, website_id, price, url) 
                    VALUES (?, ?, ?, ?);
                """
                cursor.execute(insert_price_query, (product_id, website_id, price if price is not None else 0, product_url))
        else:
            insert_product_query = """
                INSERT INTO Products (name, image_url, category_id) 
                OUTPUT INSERTED.id
                VALUES (?, ?, ?);
            """
            cursor.execute(insert_product_query, (normalized_product_name, image_url, category_id))
            product_id = cursor.fetchone()[0]
            
            insert_price_query = """
                INSERT INTO ProductPrices (product_id, website_id, price, url) 
                VALUES (?, ?, ?, ?);
            """
            cursor.execute(insert_price_query, (product_id, website_id, price if price is not None else 0, product_url))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

@app.route('/crawl', methods=['POST'])
def crawl():
    # Lấy thông tin từ JSON request
    data = request.get_json()

    site_name = data.get('site_name')
    url = data.get('url')
    category_id = data.get('category_id')
    selectors = data.get('selectors')

    results = {}
    driver = init_driver()
    try:
        print(f"Đang lấy dữ liệu từ {site_name}...")
        
        # Mở trang web và click vào nút "Xem thêm" nếu có
        load_all_products(driver, url, site_name)
        
        # Lấy thông tin sản phẩm từ trang web
        products_data = get_product_info(
            driver,
            name_selector=selectors['name_selector'],
            price_selector=selectors['price_selector'],
            link_selector=selectors['link_selector'],
            image_selector=selectors['image_selector']
        )
        
        # Lưu thông tin vào DataFrame và file CSV
        results[site_name] = {
            'count': len(products_data),
            'status': 'success'
        }
        save_to_dataframe(products_data, "products_" + site_name)
        
        # Lưu dữ liệu vào cơ sở dữ liệu
        for product in products_data:
            product_name = product['Tên sản phẩm']
            product_price = clean_price(product['Giá sản phẩm'])
            product_link = product['Link sản phẩm']
            product_image = product['URL ảnh sản phẩm']
            
            add_or_update_product(
                product_name=product_name,
                category_id=category_id,
                image_url=product_image,
                website_id=site_id_mapping(site_name),
                price=product_price,
                product_url=product_link
            )
    except Exception as e:
        results['error'] = str(e)
    finally:
        driver.quit()
    
    return jsonify(results)


if __name__ == "__main__":
     app.run(port=5000, debug=True)

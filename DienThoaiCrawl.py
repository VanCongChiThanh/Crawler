import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyodbc
import re
# Hàm khởi tạo trình duyệt
def init_driver():
    driver = webdriver.Chrome()
    return driver

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
        except:
            print("Không tìm thấy nút 'Xem thêm' nữa hoặc đã tải hết sản phẩm.")
            break

# Hàm kiểm tra và đóng nút "Đóng" trên trang ClickBuy
def close_popup(driver):
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.close-modal.icon-minutes"))
        )
        close_button.click()
        print("Đã đóng popup trên trang ClickBuy.")
    except:
        print("Không tìm thấy nút 'Đóng' trên trang ClickBuy.")


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
    print(f"Lưu dữ liệu vào {file_name}.csv  thành công!")


# Kết nối chung cho toàn bộ chương trình
conn_str = "Driver={SQL Server};Server=DESKTOP-KKVDHC9\\SQLEXPRESS;Database=BestPriceDB;Trusted_Connection=yes;"


import re

def clean_price(price_str):
    # Kiểm tra các chuỗi không hợp lệ
    if price_str.strip().lower() in ["liên hệ", "call", "contact", "on request"]:
        # Trả về None nếu giá không xác định
        return None
    
    # Loại bỏ các ký tự không phải số, dấu phân cách hoặc khoảng trắng
    cleaned_price = re.sub(r'[^\d]', '', price_str)
    
    # Chuyển chuỗi thành số nguyên (int)
    try:
        return int(cleaned_price)
    except ValueError:
        # Trả về None nếu không thể chuyển đổi
        return None



def site_id_mapping(site_name):
    mapping = {
        "didongviet": 1,  # Ví dụ: website_id = 1 cho Didongviet
        "clickbuy": 2,    # website_id = 2 cho ClickBuy
        "minhtuanmobile": 3,  # website_id = 3 cho MinhTuanMobile
    }
    return mapping.get(site_name, None)

def normalize_product_name(product_name):
    # Chuyển tên sản phẩm về chữ thường
    normalized_name = product_name.lower()
    
    # Chỉ lấy phần chuỗi trước chữ "b" đầu tiên
    if "b" in normalized_name:
        normalized_name = normalized_name.split("b", 1)[0] + "b"  # Giữ lại cả chữ "b"
    
    # Loại bỏ khoảng trắng ở đầu và cuối, giữ lại khoảng trắng ở giữa
    normalized_name = normalized_name.strip()
    
    return normalized_name


def add_or_update_product(product_name, category_id, image_url, website_id, price, product_url):
    # Chuyển tên sản phẩm về chữ thường và chỉ lấy phần trước "GB"
    normalized_product_name = normalize_product_name(product_name)
    
    # Kết nối đến cơ sở dữ liệu
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    try:
        # Tìm kiếm sản phẩm đã tồn tại dựa trên tên chuẩn hóa
        product_query = """
            SELECT id FROM Products 
            WHERE LOWER(name) LIKE ?;
        """
        cursor.execute(product_query, ('%' + normalized_product_name + '%',))
        product = cursor.fetchone()
        
        if product:
            print(f"Sản phẩm đã tồn tại: {normalized_product_name}")
            product_id = product[0]
            # Kiểm tra xem giá của sản phẩm trên website này đã tồn tại chưa
            price_query = """
                SELECT id FROM ProductPrices 
                WHERE product_id = ? AND website_id = ? AND url = ?;
            """
            cursor.execute(price_query, (product_id, website_id, product_url))
            price_record = cursor.fetchone()
            
            if price_record:
                # Cập nhật giá nếu đã tồn tại
                update_price_query = """
                    UPDATE ProductPrices 
                    SET price = ? 
                    WHERE id = ?;
                """
                cursor.execute(update_price_query, (price if price is not None else 0, price_record[0]))
            else:
                # Chèn mới nếu giá chưa tồn tại
                insert_price_query = """
                    INSERT INTO ProductPrices (product_id, website_id, price, url) 
                    VALUES (?, ?, ?, ?);
                """
                cursor.execute(insert_price_query, (product_id, website_id, price if price is not None else 0, product_url))
        else:
            print(f"Normalized product name: {normalized_product_name}")
            # Nếu sản phẩm chưa tồn tại, tạo sản phẩm mới và chỉ lưu phần trước "GB"
            insert_product_query = """
                INSERT INTO Products (name, image_url, category_id) 
                OUTPUT INSERTED.id
                VALUES (?, ?, ?);
            """
            cursor.execute(insert_product_query, (normalized_product_name, image_url, category_id))
            product_id = cursor.fetchone()[0]
            
            # Sau đó chèn giá
            insert_price_query = """
                INSERT INTO ProductPrices (product_id, website_id, price, url) 
                VALUES (?, ?, ?, ?);
            """
            cursor.execute(insert_price_query, (product_id, website_id, price if price is not None else 0, product_url))
        
        # Lưu các thay đổi
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()



# Hàm main để chạy chương trình
def main():
    # URL của các trang web
    url = {
        "didongviet": "https://didongviet.vn/dien-thoai-iphone.html",
        "clickbuy": "https://clickbuy.com.vn/dien-thoai-iphone-cu",
        "minhtuanmobile": "https://minhtuanmobile.com/iphone-cu/",
    }

    # Các CSS selector tùy chỉnh theo trang web
    selectors = {
        "didongviet": {
            "name_selector": "h3.truncate-multiline",
            "price_selector": "p.font-bold",
            "link_selector": "a.max-md\\:min-w-\\[185px\\]",
            "image_selector": "img.max-h-full"
        },
        "clickbuy": {
            "name_selector": "h3.title_name",
            "price_selector": "ins.new-price",
            "link_selector": "a[aria-label]",  
            "image_selector": "img.lazyload"
        },
        "minhtuanmobile": {
        "name_selector": "h3.probox__title",
        "price_selector": "b.price",
        "link_selector": "a.box",
        "image_selector": "div.probox__img figure img"
         }
  
    }

    # Khởi tạo trình duyệt
    driver = init_driver()
    
    try:
        for site in url:
            print(f"Đang lấy dữ liệu từ {site}...")
            # Tải toàn bộ sản phẩm từ trang web
            load_all_products(driver, url[site], site)
            
            # Lấy thông tin sản phẩm
            products_data = get_product_info(
                driver,
                name_selector=selectors[site]['name_selector'],
                price_selector=selectors[site]['price_selector'],
                link_selector=selectors[site]['link_selector'],
                image_selector=selectors[site]['image_selector']
            )
            print(f"Đã lấy {len(products_data)} sản phẩm từ {site}")
            # Lưu thông tin vào DataFrame và xuất file
            save_to_dataframe(products_data, "products_" + site)
            # Duyệt qua từng sản phẩm và gọi hàm add_or_update_product để lưu vào database
            for product in products_data:
                product_name = product['Tên sản phẩm']
                product_price = clean_price(product['Giá sản phẩm'])
                print(product_price)
                product_link = product['Link sản phẩm']
                product_image = product['URL ảnh sản phẩm']
                
                # Lưu sản phẩm vào cơ sở dữ liệu
                add_or_update_product(
                    product_name=product_name,
                    category_id=1,  # Giả định category_id = 1, thay đổi theo nhu cầu của bạn
                    image_url=product_image,
                    website_id=site_id_mapping(site),  # Hàm ánh xạ từ tên trang sang website_id
                    price=product_price,
                    product_url=product_link
                )
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

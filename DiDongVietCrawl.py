import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    df.to_excel(f'{file_name}.xlsx', index=False)
    print(f"Lưu dữ liệu vào {file_name}.csv và {file_name}.xlsx thành công!")

# Hàm main để chạy chương trình
def main():
    # URL của các trang web
    url = {
        # "didongviet": "https://didongviet.vn/dien-thoai-iphone.html",
        # "clickbuy": "https://clickbuy.com.vn/dien-thoai-iphone-cu",
        # "taozinsaigon":"https://taozinsaigon.com/iphone"
        "minhtuanmobile": "https://minhtuanmobile.com/iphone-cu/",
    }

    # Các CSS selector tùy chỉnh theo trang web
    selectors = {
        # "didongviet": {
        #     "name_selector": "h3.truncate-multiline",
        #     "price_selector": "p.font-bold",
        #     "link_selector": "a.max-md\\:min-w-\\[185px\\]",
        #     "image_selector": "img.max-h-full"
        # },
        # "clickbuy": {
        #     "name_selector": "h3.title_name",
        #     "price_selector": "ins.new-price",
        #     "link_selector": "a[aria-label]",  # Trỏ đến thẻ <a> có aria-label
        #     "image_selector": "img.lazyload"
        # },
    #              "taozinsaigon": {
    # "name_selector": ".pinfo h3 a",
    # "price_selector": ".price",
    # "link_selector": ".boxItem .pic a",  # Cập nhật lại để phù hợp với cấu trúc
    # "image_selector": ".boxItem .pic img"
    #              }
               "minhtuanmobile": {
        "name_selector": "h3.probox__title",
        "price_selector": "b.price",
        "link_selector": "a.box",
        "image_selector": "div.probox__img figure img"
         },

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
            
            # Lưu thông tin vào DataFrame và xuất file
            save_to_dataframe(products_data, "products_" + site)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

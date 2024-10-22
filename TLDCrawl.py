from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Hàm crawl sản phẩm từ một trang web cụ thể với các tham số tuỳ biến
def crawl_website(url, name_selector, price_selector, link_selector, img_selector, next_page_selector=None, load_more_selector=None):
    # Mở trình duyệt
    driver = webdriver.Chrome()

    # Truy cập vào trang web
    driver.get(url)

    # Hàm để tải toàn bộ sản phẩm từ trang hiện tại
    def load_all_products():
        # Nếu có nút "Xem thêm", thì bấm để tải thêm sản phẩm
        if load_more_selector:
            while True:
                try:
                    load_more_button = driver.find_element(By.XPATH, load_more_selector)
                    load_more_button.click()
                    time.sleep(3)  # Đợi trang tải thêm sản phẩm
                except:
                    break

        # Lấy thông tin sản phẩm sau khi đã tải xong
        products = driver.find_elements(By.CSS_SELECTOR, link_selector)

        for product in products:
            try:
                # Lấy tên sản phẩm
                name = product.find_element(By.CSS_SELECTOR, name_selector).text
                
                # Lấy giá sản phẩm (nếu có)
                try:
                    price = product.find_element(By.CSS_SELECTOR, price_selector).text
                except:
                    price = "Không có thông tin giá"
                
                # Lấy liên kết sản phẩm
                link = product.get_attribute('href')
                
                # Lấy ảnh sản phẩm
                try:
                    img = product.find_element(By.CSS_SELECTOR, img_selector).get_attribute('src')
                except:
                    img = "Không có ảnh sản phẩm"

                # In kết quả
                print(f"Tên sản phẩm: {name}")
                print(f"Giá sản phẩm: {price}")
                print(f"Link sản phẩm: {link}")
                print(f"Ảnh sản phẩm: {img}\n")
            except Exception as e:
                print(f"Lỗi khi lấy dữ liệu sản phẩm: {e}")

    # Bắt đầu thu thập sản phẩm trên trang đầu tiên
    load_all_products()

    # Xử lý việc chuyển trang nếu có nhiều trang
    if next_page_selector:
        while True:
            try:
                next_page_button = driver.find_element(By.XPATH, next_page_selector)
                next_page_button.click()
                time.sleep(3)  # Đợi trang tiếp theo tải
                
                # Thu thập sản phẩm trên trang mới
                load_all_products()
                
            except:
                print("Không tìm thấy hoặc không còn nút chuyển trang. Kết thúc quá trình.")
                break

    # Đóng trình duyệt
    driver.quit()

# Điều chỉnh cho trang laptoptld.com
url_1 = "https://laptoptld.com/cat/laptop-moi//"
name_selector_1 = "a.woocommerce-LoopProduct-link"  # Thẻ chứa tên sản phẩm
price_selector_1 = "span.woocommerce-Price-amount"  # Thẻ chứa giá sản phẩm
link_selector_1 = "a.woocommerce-LoopProduct-link"  # Thẻ chứa link sản phẩm
img_selector_1 = "img"  # Thẻ chứa ảnh sản phẩm

# Gọi hàm crawl với các tham số đã điều chỉnh
crawl_website(url_1, name_selector_1, price_selector_1, link_selector_1, img_selector_1)

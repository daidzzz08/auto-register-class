import time
import base64
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from .captcha import solve_captcha_with_gemini

URL_LOGIN = "https://mydtu.duytan.edu.vn/Signin.aspx"
# URL đăng ký (cần cập nhật đúng theo học kỳ thực tế)
URL_REGISTER = "https://mydtu.duytan.edu.vn/sites/index.aspx?p=home_registeredall&semesterid=92&yearid=90"

def login_mydtu(driver, username, password):
    print(f"🔄 Đang đăng nhập user: {username}")
    driver.get(URL_LOGIN)
    
    for attempt in range(3): # Thử tối đa 3 lần
        try:
            # 1. Chụp ảnh Captcha
            captcha_img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "imgCaptcha"))
            )
            # Chụp screenshot element captcha
            base64_str = captcha_img.screenshot_as_base64
            
            # 2. Giải Captcha
            captcha_text = solve_captcha_with_gemini(base64_str)
            if not captcha_text:
                driver.refresh(); continue

            # 3. Điền form
            driver.find_element(By.ID, "txtUser").clear()
            driver.find_element(By.ID, "txtUser").send_keys(username)
            driver.find_element(By.ID, "txtPass").clear()
            driver.find_element(By.ID, "txtPass").send_keys(password)
            driver.find_element(By.ID, "txtCaptcha").clear()
            driver.find_element(By.ID, "txtCaptcha").send_keys(captcha_text)
            
            # 4. Click Login
            driver.find_element(By.ID, "btnSignin").click()
            
            # 5. Check thành công
            time.sleep(3)
            if "Signin.aspx" not in driver.current_url:
                print("✅ Đăng nhập thành công!")
                return True
            else:
                print("⚠️ Đăng nhập thất bại (Có thể sai captcha), thử lại...")
                
        except Exception as e:
            print(f"❌ Lỗi login: {e}")
            driver.refresh()
            
    return False

def register_class(driver, class_code, reg_code):
    print(f"🚀 Bắt đầu đăng ký môn: {class_code} ({reg_code})")
    driver.get(URL_REGISTER)
    
    try:
        # 1. Chờ load trang & Tắt thông báo (nếu có)
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            driver.switch_to.alert.accept()
        except: pass

        # 2. Tìm môn học (Inject JS để tìm cho nhanh và chính xác)
        # Tìm ô input search và button search
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_txtkeyword"))
        )
        search_input.clear()
        search_input.send_keys(reg_code) # Tìm bằng mã đăng ký cho chính xác 100%
        
        # Click nút tìm kiếm (thường là ctl00_Button1 hoặc tương tự)
        # Ở đây giả định dùng JS click cho chắc ăn
        driver.execute_script("document.getElementById('ctl00_Button1').click();")
        time.sleep(2) # Chờ load lại

        # 3. Tick chọn lớp (Thường là checkbox đầu tiên sau khi search)
        # Logic: Tìm tất cả checkbox trong bảng kết quả
        checkboxes = driver.find_elements(By.CSS_selector, "input[type='checkbox']")
        
        target_checkbox = None
        for cb in checkboxes:
            # Logic này cần tinh chỉnh tùy HTML thực tế của trường
            # Thường checkbox đăng ký nằm trong grid
            if cb.is_displayed() and cb.get_attribute("name") and "chk" in cb.get_attribute("name"):
                target_checkbox = cb
                break
        
        if target_checkbox and not target_checkbox.is_selected():
            target_checkbox.click()
            print("✅ Đã tick chọn lớp")
        else:
            print("⚠️ Không tìm thấy checkbox hoặc lớp đã được đăng ký.")
            # Có thể return False ở đây nếu muốn strict

        # 4. Bấm nút Lưu Đăng Ký
        save_btn = driver.find_element(By.ID, "ctl00_btnSave")
        save_btn.click()
        
        # 5. Xử lý Captcha bước 2 (Nếu có) hoặc Alert xác nhận
        # MyDTU đôi khi hỏi captcha lúc lưu, đôi khi chỉ hỏi alert
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            print(f"🔔 Thông báo từ MyDTU: {alert_text}")
            
            if "thành công" in alert_text.lower():
                return True, "Thành công"
            else:
                return False, alert_text
        except:
            # Nếu không có alert, có thể phải giải captcha bước lưu (tùy thời điểm trường bật)
            # Logic này thêm vào sau nếu cần thiết
            pass

        return True, "Đã gửi lệnh lưu (Cần kiểm tra lại)"

    except Exception as e:
        print(f"❌ Lỗi quá trình đăng ký: {e}")
        return False, str(e)
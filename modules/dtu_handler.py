import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from modules.captcha import solve_captcha_with_gemini

URL_LOGIN = "https://mydtu.duytan.edu.vn/Signin.aspx"
# Lưu ý: URL này có thể thay đổi theo học kỳ, cần check kỹ!
URL_REGISTER = "https://mydtu.duytan.edu.vn/sites/index.aspx?p=home_registeredall&semesterid=92&yearid=90"

def save_debug_screenshot(driver, name):
    """Lưu ảnh lỗi để debug"""
    try:
        filename = f"debug_{name}_{int(time.time())}.png"
        driver.save_screenshot(filename)
        print(f"📸 Đã chụp ảnh debug: {filename}")
    except: pass

def login_mydtu(driver, username, password):
    print(f"🔄 Đang vào trang Login: {URL_LOGIN}")
    driver.get(URL_LOGIN)
    
    for attempt in range(1, 4): # Thử 3 lần
        print(f"   ► Lần thử {attempt}...")
        try:
            # 1. Chờ Captcha xuất hiện
            captcha_img = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, "imgCaptcha"))
            )
            time.sleep(1) # Chờ ảnh load xong hoàn toàn
            
            base64_str = captcha_img.screenshot_as_base64
            captcha_text = solve_captcha_with_gemini(base64_str)
            
            if not captcha_text or "ERROR" in captcha_text:
                print("      ⚠️ Không giải được captcha, refresh...")
        print(f"🔥 Lỗi đăng ký: {e}")
                continue

            # 2. Điền form
            user_input = driver.find_element(By.ID, "txtUser")
            user_input.clear()
            user_input.send_keys(username)
            
            pass_input = driver.find_element(By.ID, "txtPass")
            pass_input.clear()
            pass_input.send_keys(password)
            
            cap_input = driver.find_element(By.ID, "txtCaptcha")
            cap_input.clear()
            cap_input.send_keys(captcha_text)
            
            # 3. Click Login
            driver.find_element(By.ID, "btnSignin").click()
            
            # 4. Kiểm tra URL sau khi login
            time.sleep(5) 
            if "Signin.aspx" not in driver.current_url:
                print("✅ Đăng nhập THÀNH CÔNG!")
                return True
            else:
                # Kiểm tra xem có thông báo lỗi không (VD: Sai captcha, Sai pass)
                try:
                    lbl_err = driver.find_element(By.ID, "lblError") # Hoặc ID tương tự
                    if lbl_err.is_displayed():
                        print(f"      ⚠️ Lỗi từ web: {lbl_err.text}")
                except: pass
                print("      ⚠️ Login thất bại (vẫn ở trang login).")
                
        except Exception as e:
            print(f"      ❌ Exception login: {e}")
            save_debug_screenshot(driver, "login_error")
            driver.refresh()
            
    return False

def register_class(driver, class_code, reg_code):
    print(f"🚀 Chuyển hướng đến trang Đăng Ký: {URL_REGISTER}")
    driver.get(URL_REGISTER)
    
    try:
        # 1. Tắt Alert (nếu có)
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            driver.switch_to.alert.accept()
        except: pass

        # 2. Tìm lớp bằng Mã Đăng Ký (Chính xác nhất)
        print(f"🔎 Tìm kiếm: {reg_code}")
        search_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "ctl00_txtkeyword"))
        )
        search_box.clear()
        search_box.send_keys(reg_code)
        
        # Click nút Tìm
        # search_btn = driver.find_element(By.ID, "ctl00_Button1")
        # search_btn.click()
        # Dùng JS click cho an toàn
        driver.execute_script("document.getElementById('ctl00_Button1').click();")
        
        time.sleep(3) # Chờ load kết quả

        # 3. Chọn Checkbox
        # Logic: Tìm checkbox trong dòng đầu tiên của bảng kết quả
        # XPath này tìm checkbox có tên chứa 'chk' nằm trong bảng
        try:
            checkbox = driver.find_element(By.XPATH, "//input[contains(@name, 'chk') and @type='checkbox']")
            if not checkbox.is_selected():
        print(f"🔥 Lỗi đăng ký: {e}")
                print("✅ Đã tick chọn lớp.")
            else:
                print("ℹ️ Lớp đã được tick sẵn.")
        except:
            print("❌ Không tìm thấy lớp hoặc lớp đã full/ẩn.")
            save_debug_screenshot(driver, "search_failed")
            return False, "Không tìm thấy lớp"

        # 4. Bấm Lưu
        print("💾 Đang bấm Lưu...")
        driver.execute_script("document.getElementById('ctl00_btnSave').click();")
        
        # 5. Xử lý kết quả (Alert)
        time.sleep(2)
        try:
            WebDriverWait(driver, 10).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            msg = alert.text
            alert.accept()
            print(f"🔔 Thông báo: {msg}")
            
            if "thành công" in msg.lower():
        print(f"🔥 Lỗi đăng ký: {e}")
            return False, msg
        except:
            # Nếu không có alert, có thể phải check html
            print("⚠️ Không thấy thông báo phản hồi.")
            return False, "Unknown response"

    except Exception as e:
        print(f"🔥 Lỗi đăng ký: {e}")
        save_debug_screenshot(driver, "reg_error")
        return False, str(e)
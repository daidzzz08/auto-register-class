import time
import os
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# Giả định file captcha.py nằm trong thư mục modules như cấu trúc cũ
# Nếu bạn để cùng thư mục, hãy sửa thành: from captcha import solve_captcha_with_gemini
from captcha import solve_captcha_with_gemini

# Link trang web
URL_LOGIN = "https://mydtu.duytan.edu.vn/Signin.aspx"
URL_REGISTER = "https://mydtu.duytan.edu.vn/sites/index.aspx?p=home_registeredall&semesterid=92&yearid=90"

def log(msg):
    """Ghi log có thời gian để dễ theo dõi trên GitHub Actions"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def save_debug_screenshot(driver, name):
    try:
        timestamp = int(time.time())
        filename = f"debug_{name}_{timestamp}.png"
        driver.save_screenshot(filename)
        log(f"📸 Saved Screenshot: {filename}")
    except: pass

def login_mydtu(driver, username, password):
    log(f"🚀 LOGIN START: {username}")
    
    # Retry load trang login nếu mạng chậm (tăng nhẹ lên 5 lần cho chắc chắn)
    for i in range(5):
        try:
            driver.get(URL_LOGIN)
            break
        except Exception as e:
            log(f"⚠️ Load timeout ({i+1}/5): {e}")
            time.sleep(3)

    # TĂNG SỐ LẦN RETRY LOGIN LÊN 10
    max_login_retries = 10
    for attempt in range(1, max_login_retries + 1):
        log(f"⚡ Login Attempt {attempt}/{max_login_retries}...")
        try:
            # 1. Chờ form login xuất hiện
            try:
                WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "txtUser")))
            except TimeoutException:
                log("❌ Timeout: Login form not found")
                driver.refresh()
                continue

            # 2. Xử lý Captcha
            captcha_text = None
            try:
                # Tìm ảnh theo src chứa CaptchaImage.axd
                captcha_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'CaptchaImage.axd')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_element)
                time.sleep(1.5) 
                
                base64_str = captcha_element.screenshot_as_base64
                if not base64_str: raise Exception("Empty Image")
                
                captcha_text = solve_captcha_with_gemini(base64_str)
            except Exception as e:
                log(f"❌ Captcha Error: {e}")
            
            if not captcha_text or "ERROR" in captcha_text:
                log("⚠️ Captcha decoding failed -> Refreshing")
                driver.refresh()
                continue

            # 3. Điền Form (JS Bypass)
            log(f"🖊️ Filling form: {username} | {captcha_text}")
            driver.execute_script(f"document.getElementById('txtUser').value = '{username}';")
            driver.execute_script(f"document.getElementById('txtPass').value = '{password}';")
            driver.execute_script(f"document.getElementById('txtCaptcha').value = '{captcha_text}';")
            
            # 4. Click Login
            btn_login = driver.find_element(By.ID, "btnLogin1")
            driver.execute_script("arguments[0].click();", btn_login)
            
            time.sleep(5) 

            # 5. Kiểm tra kết quả
            if "Signin.aspx" not in driver.current_url:
                log("✅ LOGIN SUCCESS!")
                return True
            else:
                log("⚠️ Still on login page (Check password or captcha)")
                save_debug_screenshot(driver, "login_failed")
                # Nếu vẫn ở trang login, refresh để lấy captcha mới cho lần thử sau
                driver.refresh()
                
        except Exception as e:
            log(f"🔥 Login Exception: {e}")
            driver.refresh()
            
    return False

def register_class(driver, class_code, reg_code):
    log(f"🚀 REGISTRATION START: Class {reg_code}")
    driver.get(URL_REGISTER)
    
    # TĂNG SỐ LẦN RETRY ĐĂNG KÝ LÊN 10
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        log(f"\n⚡ Register Attempt {attempt}/{max_retries}...")
        
        try:
            # Tắt Alert rác
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                driver.switch_to.alert.accept()
            except: pass

            # --- BƯỚC 1: NHẬP MÃ LỚP ---
            try:
                txt_class_id = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "ctl00_PlaceHolderContentArea_ctl00_ctl01_txt_ClassID"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", txt_class_id)
                txt_class_id.clear()
                txt_class_id.send_keys(reg_code)
                log(f"✍️ Entered Class ID: {reg_code}")
            except:
                log("❌ Class Input not found. Session lost?")
                driver.get(URL_REGISTER) # Reload lại trang đăng ký
                continue

            # --- BƯỚC 2: GIẢI CAPTCHA ĐĂNG KÝ ---
            captcha_reg_text = None
            try:
                captcha_reg_img = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "imgCapt"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_reg_img)
                time.sleep(1)
                
                base64_reg = captcha_reg_img.screenshot_as_base64
                captcha_reg_text = solve_captcha_with_gemini(base64_reg)
            except Exception as e:
                log(f"❌ Register Captcha Error: {e}")
            
            if not captcha_reg_text:
                log("⚠️ Captcha failed -> Retrying")
                continue 

            log(f"🧩 Captcha Solved: {captcha_reg_text}")

            # Nhập Captcha
            try:
                txt_captcha_reg = driver.find_element(By.ID, "ctl00_PlaceHolderContentArea_ctl00_ctl01_txtCaptchar")
                txt_captcha_reg.clear()
                txt_captcha_reg.send_keys(captcha_reg_text)
            except:
                log("❌ Captcha Input not found")
                continue

            # --- BƯỚC 3: SUBMIT ---
            log("💾 Clicking Register Button...")
            try:
                btn_add = driver.find_element(By.NAME, "btnadd")
                driver.execute_script("arguments[0].click();", btn_add)
            except:
                log("❌ Submit Button not found")
                continue
            
            # Xử lý Alert Xác nhận
            time.sleep(1.5)
            try:
                WebDriverWait(driver, 8).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                log(f"🔔 Alert: {alert.text}")
                alert.accept() 
                log("✅ Confirmed Alert.")
            except:
                log("⚠️ No Alert appeared.")

            # --- BƯỚC 4: KIỂM TRA KẾT QUẢ ---
            log("👀 Checking result (Max 30s)...")
            final_msg = ""
            
            # Chờ thông báo xuất hiện
            for _ in range(10): # Check 10 lần, mỗi lần 3s
                time.sleep(3)
                try:
                    res_div = driver.find_element(By.ID, "displayThongBao")
                    final_msg = res_div.text.strip()
                    if final_msg:
                        log(f"🏁 Web Message: '{final_msg}'")
                        
                        if "thành công" in final_msg.lower() or "đã đăng ký" in final_msg.lower():
                            return True, final_msg
                        
                        if "sai số bảo vệ" in final_msg.lower():
                            log("🔄 Wrong Captcha -> Retrying...")
                            break # Thoát vòng lặp nhỏ để retry vòng lớn
                        
                        if "lớp đã đầy" in final_msg.lower() or "trùng lịch" in final_msg.lower():
                            return False, final_msg # Lỗi này không retry được
                except: pass
                
                # Check Page Source (Double Check - Cách chắc chắn nhất)
                if reg_code in driver.page_source and ("Hủy" in driver.page_source or "Delete" in driver.page_source):
                     log("🎉 DOUBLE-CHECK: Found class in registered list!")
                     return True, "Thành công (Verified)"

            if final_msg and "sai số bảo vệ" in final_msg.lower():
                continue # Retry vòng lớn

            log(f"⚠️ Result inconclusive. Last msg: '{final_msg}'")
            save_debug_screenshot(driver, "reg_unknown")

        except Exception as e:
            log(f"🔥 Critical Error: {e}")
            try: driver.refresh(); time.sleep(3)
            except: pass

    return False, "Max Retries Exceeded"

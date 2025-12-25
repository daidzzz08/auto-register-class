import os
import sys
import requests
from modules.browser import init_driver
from modules.dtu_handler import login_mydtu, register_class

# Cấu hình Firebase Repo A
FIREBASE_BASE_URL = "https://tool-theo-doi-slot-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SECRET = os.environ.get("FIREBASE_SECRET")

def get_student_credentials(uid):
    if not FIREBASE_SECRET:
        print("❌ Missing FIREBASE_SECRET")
        return None, None
        
    auth_suffix = f"?auth={FIREBASE_SECRET}"
    url = f"{FIREBASE_BASE_URL}/users/{uid}/student_account.json{auth_suffix}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data: return data.get('id'), data.get('pass')
    except Exception as e:
        print(f"❌ Firebase Error: {e}")
    return None, None

def main():
    # Input từ GitHub Actions
    uid = os.environ.get("INPUT_UID")
    class_code = os.environ.get("INPUT_CLASS_CODE")
    reg_code = os.environ.get("INPUT_REG_CODE")
    
    print(f"🚀 START JOB: Class {reg_code} | User UID: {uid[:5]}...")

    if not uid or not reg_code:
        print("❌ Missing Inputs")
        sys.exit(1)

    # Lấy pass
    student_id, student_pass = get_student_credentials(uid)
    if not student_id or not student_pass:
        print("❌ No Credentials Found in DB")
        sys.exit(1)
        
    print(f"👤 Student Account: {student_id}")

    # Chạy Browser
    driver = None
    try:
        driver = init_driver()
        
        if login_mydtu(driver, student_id, student_pass):
            success, msg = register_class(driver, class_code, reg_code)
            
            if success:
                print(f"✅ FINAL RESULT: SUCCESS - {msg}")
                # (Tùy chọn) Gửi thông báo thành công về DB/Telegram tại đây
            else:
                print(f"❌ FINAL RESULT: FAILED - {msg}")
        else:
            print("❌ Login Failed")
            
    except Exception as e:
        print(f"🔥 Fatal Error: {e}")
    finally:
        if driver:
            driver.quit()
            print("🛑 Browser Closed")

if __name__ == "__main__":
    main()
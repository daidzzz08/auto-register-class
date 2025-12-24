import os
import sys
import requests
from modules.browser import init_driver
from modules.dtu_handler import login_mydtu, register_class

# Cấu hình Firebase Repo A (Để lấy pass sinh viên)
FIREBASE_DB_URL = "https://tool-theo-doi-slot-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SECRET = os.environ.get("FIREBASE_SECRET") # Lấy từ Secrets

def get_student_credentials(uid):
    """Lấy user/pass sinh viên từ Firebase dựa trên UID của khách"""
    auth_suffix = f"?auth={FIREBASE_SECRET}"
    url = f"{FIREBASE_BASE_URL}/users/{uid}/student_account.json{auth_suffix}"
    
    try:
        resp = requests.get(url)
        data = resp.json()
        if data:
            return data.get('id'), data.get('pass')
    except Exception as e:
        print(f"Lỗi lấy thông tin SV: {e}")
    return None, None

def main():
    # 1. Nhận input từ GitHub Actions (Repository Dispatch)
    # Các biến này được truyền vào từ file workflow .yml
    uid = os.environ.get("INPUT_UID")
    class_code = os.environ.get("INPUT_CLASS_CODE") # VD: ENG 111
    reg_code = os.environ.get("INPUT_REG_CODE")     # VD: ENG111...
    
    if not uid or not reg_code:
        print("❌ Thiếu tham số đầu vào (UID hoặc Reg Code)")
        sys.exit(1)

    print(f"🔧 Bắt đầu Job Auto-Reg cho User: {uid} - Môn: {reg_code}")

    # 2. Lấy mật khẩu MyDTU từ Firebase
    student_id, student_pass = get_student_credentials(uid)
    if not student_id or not student_pass:
        print("❌ Không tìm thấy thông tin đăng nhập MyDTU trong DB.")
        sys.exit(1)

    # 3. Khởi tạo trình duyệt
    driver = init_driver()
    
    try:
        # 4. Login
        if login_mydtu(driver, student_id, student_pass):
            # 5. Đăng ký
            success, msg = register_class(driver, class_code, reg_code)
            
            # 6. Báo cáo kết quả (Ghi lại vào Firebase hoặc gửi Telegram)
            # Ở đây in ra log, bạn có thể thêm logic update Firebase "requests/{uid}/status" = "success"
            if success:
                print(f"🎉 KẾT QUẢ: THÀNH CÔNG - {msg}")
            else:
                print(f"💀 KẾT QUẢ: THẤT BẠI - {msg}")
        else:
            print("💀 Login thất bại, hủy job.")
            
    except Exception as e:
        print(f"🔥 Fatal Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
import os
import sys
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from modules.browser import init_driver
from modules.dtu_handler import login_mydtu, register_class

# Cấu hình Firebase Repo A
FIREBASE_BASE_URL = "https://tool-theo-doi-slot-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SECRET = os.environ.get("FIREBASE_SECRET")

# Cấu hình Email (Lấy từ GitHub Secrets)
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

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

def send_success_email(to_email, class_code, reg_code, result_msg):
    """Gửi email chúc mừng đăng ký thành công"""
    if not EMAIL_USER or not EMAIL_PASSWORD or not to_email:
        print("⚠️ Không thể gửi email (Thiếu config hoặc email khách)")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🎉 ĐĂNG KÝ THÀNH CÔNG: {class_code}"
    msg['From'] = f"DTU Sniper Auto <{EMAIL_USER}>"
    msg['To'] = to_email

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f0fdf4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid #bbf7d0;">
          
          <div style="background-color: #16a34a; padding: 20px; text-align: center; color: white;">
            <h2 style="margin: 0; font-size: 24px;">CHÚC MỪNG! 🥳</h2>
          </div>

          <div style="padding: 30px;">
            <p style="font-size: 16px;">Hệ thống Auto-Reg đã đăng ký thành công lớp học phần cho bạn.</p>
            
            <div style="background-color: #f0fdf4; padding: 15px; border-radius: 8px; border: 1px solid #dcfce7; margin: 20px 0;">
              <p><strong>Mã lớp:</strong> {class_code}</p>
              <p><strong>Mã đăng ký:</strong> <span style="font-family: monospace; font-weight: bold;">{reg_code}</span></p>
              <p><strong>Kết quả từ MyDTU:</strong> {result_msg}</p>
            </div>

            <p style="color: #ea580c; font-weight: bold; font-size: 14px;">
              ⚠️ Vui lòng đăng nhập MyDTU và kiểm tra lại Thời Khóa Biểu ngay lập tức để chắc chắn.
            </p>
          </div>

          <div style="background-color: #f8fafc; padding: 15px; text-align: center; font-size: 12px; color: #64748b;">
            <p>© 2025 DTU Sniper Pro Auto-Reg System</p>
          </div>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(EMAIL_USER, EMAIL_PASSWORD)
            s.sendmail(EMAIL_USER, to_email, msg.as_string())
        print(f"📧 Đã gửi email chúc mừng tới: {to_email}")
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")

def main():
    # Input từ GitHub Actions (Kèm Email khách)
    uid = os.environ.get("INPUT_UID")
    class_code = os.environ.get("INPUT_CLASS_CODE")
    reg_code = os.environ.get("INPUT_REG_CODE")
    user_email = os.environ.get("INPUT_EMAIL") # Email khách hàng
    
    print(f"🚀 START JOB: Class {reg_code} | Email: {user_email}")

    if not uid or not reg_code:
        print("❌ Missing Inputs")
        sys.exit(1)

    student_id, student_pass = get_student_credentials(uid)
    if not student_id or not student_pass:
        print("❌ No Credentials Found in DB")
        sys.exit(1)
        
    print(f"👤 Student Account: {student_id}")

    driver = None
    try:
        driver = init_driver()
        
        if login_mydtu(driver, student_id, student_pass):
            success, msg = register_class(driver, class_code, reg_code)
            
            if success:
                print(f"✅ FINAL RESULT: SUCCESS - {msg}")
                # Gửi email chúc mừng
                send_success_email(user_email, class_code, reg_code, msg)
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
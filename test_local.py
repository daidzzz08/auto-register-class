import os
import sys

# --- CẤU HÌNH TEST ---
TEST_USER = "phamhoangvuong"
TEST_PASS = "Hoangvuonglop5d@"
TEST_CLASS_CODE = "ENG 267"
TEST_REG_CODE = "ENG267202502013"

# DANH SÁCH KEY CÁCH NHAU BỞI DẤU PHẨY
# (Lưu ý: Không để khoảng trắng sau dấu phẩy để an toàn nhất)
keys_list = [
    "AIzaSyB_HuauQvwakNPCvcxy2tcvIHWa9-XkM50",
    "AIzaSyBWQo6cKaro6JD4OXL8bW5lespYjP3UrjA",
    "AIzaSyBLCcxNAbmm3k5oQhgXGZdQ4xmnuQtdtCM"
]
os.environ["GEMINI_API_KEY"] = ",".join(keys_list)

print(f"🔑 DEBUG: Loaded {len(keys_list)} keys.")

from modules.browser import init_driver
from modules.dtu_handler import login_mydtu, register_class

def run_test():
    print("🧪 START LOCAL TEST (MULTI-KEY)")
    
    try:
        driver = init_driver()
        print("✅ Driver init OK")
    except Exception as e:
        print(f"❌ Driver init FAIL: {e}")
        return

    try:
        if login_mydtu(driver, TEST_USER, TEST_PASS):
            print("--- Login OK, Start Register ---")
            success, msg = register_class(driver, TEST_CLASS_CODE, TEST_REG_CODE)
            print(f"RESULT: {success} - {msg}")
        else:
            print("💀 Login Test Failed")
    except Exception as e:
        print(f"🔥 Fatal Error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🛑 Closed Driver")

if __name__ == "__main__":
    run_test()
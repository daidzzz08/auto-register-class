import requests
import os
import random
import json
import time

# Lấy chuỗi key từ biến môi trường
# Hỗ trợ cả 1 key đơn lẻ hoặc nhiều key cách nhau bởi dấu phẩy
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "")
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

def solve_captcha_with_gemini(base64_image):
    if not API_KEYS:
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY nào.")
        return None

    models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    
    # CHIẾN LƯỢC 1: Prompt với các ràng buộc cứng (Strict Constraints)
    # Định nghĩa rõ vai trò, nhiệm vụ và luật (đặc biệt là độ dài 4 ký tự)
    PROMPT = """
    CONTEXT: You are a strict CAPTCHA solving OCR engine.
    TASK: Extract the text from the image.
    CONSTRAINTS:
    1. Output ONLY the text. No markdown, no explanations.
    2. The text is EXACTLY 4 alphanumeric characters.
    3. Uppercase only.
    4. Ignore spaces.
    """

    # Thử tối đa 3 lần với các key ngẫu nhiên
    for attempt in range(3):
        # Chọn ngẫu nhiên 1 key để sử dụng (Load Balancing)
        current_key = random.choice(API_KEYS)
        # Chọn ngẫu nhiên 1 model
        model = random.choice(models)
        
        # Che giấu key trong log để bảo mật
        masked_key = current_key[:5] + "..." + current_key[-3:]
        # print(f"   🤖 Using Key: {masked_key} | Model: {model}")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
        headers = {'Content-Type': 'application/json'}
        
        data = {
            "contents": [{
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": "image/png", "data": base64_image}}
                ]
            }],
            # Cấu hình sinh nội dung (Generation Config) tối ưu cho Captcha
            "generationConfig": {
                "temperature": 0.0,       # Giảm độ sáng tạo xuống 0 để tăng độ chính xác tuyệt đối
                "maxOutputTokens": 20,    # Giới hạn token đầu ra ngắn vì chỉ cần 4 ký tự
                "topP": 1.0
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=8)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Xử lý hậu kỳ: Xóa khoảng trắng và chuyển về chữ hoa
                    clean_text = content.strip().replace(" ", "").upper()
                    
                    # Kiểm tra nhanh độ dài (nếu cần thiết có thể thêm logic retry ở đây nếu len != 4)
                    if len(clean_text) != 4:
                        print(f"⚠️ Cảnh báo: Kết quả '{clean_text}' có độ dài {len(clean_text)}, mong đợi 4.")

                    print(f"🤖 Gemini Decoded ({model}): {clean_text}")
                    return clean_text
                
            elif response.status_code == 429:
                print(f"⚠️ Key {masked_key} hết quota (429). Đổi key khác...")
                time.sleep(1)
                continue # Thử lại với key khác ở vòng lặp sau
                
            elif response.status_code == 403 or response.status_code == 400:
                print(f"❌ Key {masked_key} lỗi quyền/invalid ({response.status_code}).")
                continue
                
            else:
                print(f"⚠️ Gemini Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception calling Gemini: {e}")
            
    print("❌ Tất cả các lần thử giải Captcha đều thất bại.")
    return None

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

    models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash"]
    
    # Thử tối đa 3 lần với các key ngẫu nhiên
    for attempt in range(3):
        # Chọn ngẫu nhiên 1 key để sử dụng (Load Balancing)
        current_key = random.choice(API_KEYS)
        # Chọn ngẫu nhiên 1 model
        model = random.choice(models)
        
        # Che giấu key trong log
        masked_key = current_key[:5] + "..." + current_key[-3:]
        # print(f"   🤖 Using Key: {masked_key} | Model: {model}")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
        headers = {'Content-Type': 'application/json'}
        
        data = {
            "contents": [{
                "parts": [
                    {"text": "OUTPUT: Text in image. Uppercase. Alphanumeric only. No spaces."},
                    {"inline_data": {"mime_type": "image/png", "data": base64_image}}
                ]
            }]
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=8)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    clean_text = content.strip().replace(" ", "").upper()
                    print(f"🤖 Gemini Decoded ({model}): {clean_text}")
                    return clean_text
                
            elif response.status_code == 429:
                print(f"⚠️ Key {masked_key} hết quota (429). Đổi key khác...")
                # Nếu list còn nhiều key, có thể remove key lỗi tạm thời (logic phức tạp hơn)
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
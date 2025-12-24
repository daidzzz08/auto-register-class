import requests
import os
import time
import random

# Lấy Key từ biến môi trường (Repo B Secrets)
# Hoặc dùng Pool Key nếu bạn muốn (nhưng tốt nhất là dùng Secret cho an toàn)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def solve_captcha_with_gemini(base64_image):
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Thiếu GEMINI_API_KEY")
        return None

    # Random model để tránh bị rate limit của Google
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest"]
    model = random.choice(models)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Prompt đơn giản, hiệu quả cho Captcha MyDTU (chữ/số)
    data = {
        "contents": [{
            "parts": [
                {"text": "Đọc chính xác các ký tự chữ và số trong ảnh này. Chỉ trả về chuỗi ký tự, không có khoảng trắng, viết hoa toàn bộ. Nếu không đọc được trả về 'ERROR'."},
                {"inline_data": {"mime_type": "image/png", "data": base64_image}}
            ]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                text = result['candidates'][0]['content']['parts'][0]['text']
                clean_text = text.strip().replace(" ", "").upper().replace("\n", "")
                print(f"🤖 Gemini Decoded: {clean_text}")
                return clean_text
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")
    
    return None
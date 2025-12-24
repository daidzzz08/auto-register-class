import requests
import json
import os
import base64

# Lấy API Key từ Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

def solve_captcha_with_gemini(base64_image):
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    # Prompt tối ưu cho Gemini đọc số/chữ
    data = {
        "contents": [{
            "parts": [
                {"text": "Return only the alphanumeric characters visible in this image. No spaces, no explanations."},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64_image
                    }
                }
            ]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                text = result['candidates'][0]['content']['parts'][0]['text']
                clean_text = text.strip().replace(" ", "").upper()
                print(f"🤖 Gemini decoded: {clean_text}")
                return clean_text
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
    
    return None
from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
import numpy as np
from PIL import Image
import io
import base64

app = Flask(__name__)
CORS(app)  # برای اجازه دادن به درخواست‌ها از مرورگر

# ساخت reader برای زبان انگلیسی (فقط یکبار در ابتدا)
print("در حال بارگذاری EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)
print("EasyOCR آماده است!")

@app.route('/')
def home():
    return '''
    <h1>سرور EasyOCR فعال است! ✅</h1>
    <p>برای استفاده از OCR، به آدرس /ocr پست کنید.</p>
    '''

@app.route('/ocr', methods=['POST'])
def perform_ocr():
    try:
        # دریافت تصویر از درخواست
        if 'image' not in request.files:
            return jsonify({'error': 'تصویری ارسال نشده است'}), 400
        
        file = request.files['image']
        
        # خواندن تصویر
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # تبدیل به آرایه numpy برای EasyOCR
        image_np = np.array(image)
        
        # اطلاعات تصویر
        image_info = {
            'filename': file.filename,
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height
        }
        
        # انجام OCR
        print(f"در حال پردازش تصویر: {file.filename}")
        results = reader.readtext(image_np)
        
        # آماده‌سازی نتایج
        extracted_texts = []
        full_text = ""
        
        for detection in results:
            bbox, text, confidence = detection
            extracted_texts.append({
                'text': text,
                'confidence': float(confidence),
                'bbox': bbox
            })
            full_text += text + " "
        
        response = {
            'success': True,
            'image_info': image_info,
            'full_text': full_text.strip(),
            'detections': extracted_texts,
            'total_detections': len(extracted_texts)
        }
        
        print(f"✅ پردازش موفق: {len(extracted_texts)} متن پیدا شد")
        return jsonify(response)
    
    except Exception as e:
        print(f"❌ خطا: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'سرور در حال اجرا است'})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 سرور EasyOCR در حال اجرا...")
    print("📍 آدرس: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
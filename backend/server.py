from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
import numpy as np
from PIL import Image
import io
import cv2
import re
from collections import Counter

app = Flask(__name__)
CORS(app)

# ساخت reader برای EasyOCR
print("🔄 در حال بارگذاری EasyOCR...")
easyocr_reader = easyocr.Reader(['en'], gpu=False)
print("✅ EasyOCR آماده است!")

# تلاش برای بارگذاری Tesseract
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    print("✅ Tesseract آماده است!")
except:
    print("⚠️ Tesseract در دسترس نیست - فقط از EasyOCR استفاده میشه")

def preprocess_light(image):
    """پیش‌پردازش ملایم"""
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    return sharpened

def preprocess_medium(image):
    """پیش‌پردازش متوسط"""
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    return enhanced

def preprocess_strong(image):
    """پیش‌پردازش قوی"""
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def ocr_with_easyocr(image):
    """استخراج متن با EasyOCR - نسخه سریع"""
    try:
        results = easyocr_reader.readtext(
            image, 
            detail=1, 
            paragraph=False,
            batch_size=10,  # افزایش سرعت
            workers=0,  # بدون multi-threading برای سرعت بیشتر
            decoder='greedy'  # decoder سریع‌تر
        )
        texts = []
        for bbox, text, confidence in results:
            if confidence > 0.3:  # فقط نتایج خوب
                texts.append({
                    'text': text.strip(),
                    'confidence': float(confidence),
                    'bbox': bbox,
                    'engine': 'EasyOCR'
                })
        return texts
    except Exception as e:
        print(f"❌ EasyOCR خطا: {e}")
        return []

def ocr_with_tesseract(image):
    """استخراج متن با Tesseract"""
    if not TESSERACT_AVAILABLE:
        return []
    
    try:
        import pytesseract
        from pytesseract import Output
        
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        data = pytesseract.image_to_data(pil_image, output_type=Output.DICT)
        
        texts = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 20:
                text = data['text'][i].strip()
                if text:
                    texts.append({
                        'text': text,
                        'confidence': float(data['conf'][i]) / 100.0,
                        'bbox': None,
                        'engine': 'Tesseract'
                    })
        return texts
    except Exception as e:
        print(f"❌ Tesseract خطا: {e}")
        return []

def smart_combine_results(easyocr_results, tesseract_results):
    """
    ترکیب هوشمند نتایج از موتورهای مختلف
    """
    all_results = []
    
    # اضافه کردن نتایج EasyOCR
    for result in easyocr_results:
        all_results.append(result)
    
    # اضافه کردن نتایج Tesseract که در EasyOCR نیست
    for tres in tesseract_results:
        # چک کنیم آیا این متن در EasyOCR هست؟
        found = False
        for eres in easyocr_results:
            similarity = calculate_similarity(tres['text'], eres['text'])
            if similarity > 0.8:
                found = True
                break
        
        if not found:
            all_results.append(tres)
    
    # مرتب‌سازی بر اساس اعتماد
    all_results.sort(key=lambda x: x['confidence'], reverse=True)
    
    return all_results

def calculate_similarity(text1, text2):
    """محاسبه شباهت دو متن"""
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    if text1 == text2:
        return 1.0
    
    # محاسبه Levenshtein distance ساده
    if len(text1) < len(text2):
        text1, text2 = text2, text1
    
    if len(text2) == 0:
        return 0.0
    
    previous_row = range(len(text2) + 1)
    for i, c1 in enumerate(text1):
        current_row = [i + 1]
        for j, c2 in enumerate(text2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    distance = previous_row[-1]
    max_len = max(len(text1), len(text2))
    similarity = 1 - (distance / max_len)
    
    return similarity

def smart_post_process(text, all_results):
    """
    پست‌پردازش هوشمند بر اساس تشخیص نوع محتوا
    """
    if not text or not text.strip():
        return text
    
    # تشخیص نوع محتوا
    digit_count = sum(c.isdigit() for c in text)
    alpha_count = sum(c.isalpha() for c in text)
    upper_count = sum(c.isupper() for c in text)
    
    # محتوای عددی (مثل کد پستی، شماره تلفن)
    if digit_count > alpha_count:
        corrections = {
            'O': '0', 'o': '0', 'D': '0',
            'I': '1', 'l': '1', '|': '1',
            'Z': '2', 'B': '8', 'S': '5', 'G': '6'
        }
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
    
    # محتوای ترکیبی (مثل پارت نامبر IC، کد محصول)
    elif alpha_count > 0 and digit_count > 0:
        # M در کنار اعداد به N
        text = re.sub(r'M(\d)', r'N\1', text)
        text = re.sub(r'(\d)M(\d)', r'\1N\2', text)
        
        # 0 در ابتدای کلمات احتمالاً O است
        text = re.sub(r'\b0([A-Z])', r'O\1', text)
        
        # حذف فاصله‌های اضافی
        text = re.sub(r'(?<=[A-Z0-9])\s+(?=[A-Z0-9])', '', text)
    
    # تبدیل حروف کوچیک در کدهای فنی به بزرگ
    if upper_count > len(text) / 2:
        text = text.upper()
    
    return text.strip()

@app.route('/')
def home():
    engines = ['EasyOCR']
    if TESSERACT_AVAILABLE:
        engines.append('Tesseract')
    
    return f'''
    <div style="font-family: Arial; padding: 50px; text-align: center;">
        <h1 style="color: #667eea;">✅ سرور OCR چندموتوره فعال است!</h1>
        <p style="font-size: 18px;">موتورهای فعال: {", ".join(engines)}</p>
        <p style="color: #666;">پورت: 5000</p>
        <p style="color: #28a745; margin-top: 20px;">✨ قابلیت خواندن هر نوع متنی</p>
    </div>
    '''

@app.route('/ocr', methods=['POST'])
def perform_ocr():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'تصویری ارسال نشده است'}), 400
        
        file = request.files['image']
        use_multi_engine = request.form.get('multi_engine', 'false').lower() == 'true'
        use_fast_mode = request.form.get('fast_mode', 'false').lower() == 'true'
        preprocess_level = request.form.get('preprocess', 'none')
        
        # خواندن تصویر
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        original_info = {
            'filename': file.filename,
            'format': image.format if image.format else 'Unknown',
            'mode': image.mode,
            'width': image.width,
            'height': image.height
        }
        
        print(f"🔄 پردازش: {file.filename}")
        print(f"⚡ حالت سریع: {'بله' if use_fast_mode else 'خیر'}")
        
        # پیش‌پردازش
        if preprocess_level == 'none':
            processed_image = np.array(image)
        elif preprocess_level == 'light':
            processed_image = preprocess_light(image)
        elif preprocess_level == 'medium':
            processed_image = preprocess_medium(image)
        elif preprocess_level == 'strong':
            processed_image = preprocess_strong(image)
        else:
            processed_image = np.array(image)
        
        # انتخاب موتور OCR
        print("🔍 استخراج...")
        
        if use_fast_mode and TESSERACT_AVAILABLE:
            # حالت سریع: فقط Tesseract
            all_detections = ocr_with_tesseract(processed_image)
            print(f"⚡ Tesseract (سریع): {len(all_detections)}")
        elif use_multi_engine and TESSERACT_AVAILABLE:
            # حالت دقیق: هر دو
            easyocr_results = ocr_with_easyocr(processed_image)
            tesseract_results = ocr_with_tesseract(processed_image)
            all_detections = smart_combine_results(easyocr_results, tesseract_results)
            print(f"🎯 ترکیبی: {len(all_detections)}")
        else:
            # حالت معمولی: فقط EasyOCR
            all_detections = ocr_with_easyocr(processed_image)
            print(f"📊 EasyOCR: {len(all_detections)}")
        
        if not all_detections:
            return jsonify({
                'success': True,
                'image_info': original_info,
                'full_text': '',
                'detections': [],
                'total_detections': 0,
                'corrections_count': 0,
                'average_confidence': 0,
                'engines_used': [],
                'preprocessing': preprocess_level
            })
        
        # ساخت متن کامل
        full_text_parts = []
        processed_detections = []
        
        for detection in all_detections:
            original_text = detection['text']
            processed_text = smart_post_process(original_text, all_detections)
            
            processed_detections.append({
                'text': processed_text,
                'original_text': original_text,
                'confidence': detection['confidence'],
                'engine': detection['engine'],
                'corrected': original_text != processed_text
            })
            
            full_text_parts.append(processed_text)
        
        full_text = ' '.join(full_text_parts)
        
        # محاسبه آمار
        avg_confidence = sum(d['confidence'] for d in processed_detections) / len(processed_detections) if processed_detections else 0
        corrections_count = sum(1 for d in processed_detections if d['corrected'])
        
        engines_used = list(set(d['engine'] for d in processed_detections))
        
        print(f"📊 میانگین اعتماد: {avg_confidence*100:.1f}%")
        print(f"🔧 تصحیحات: {corrections_count}")
        
        return jsonify({
            'success': True,
            'image_info': original_info,
            'full_text': full_text,
            'detections': processed_detections,
            'total_detections': len(processed_detections),
            'corrections_count': corrections_count,
            'average_confidence': float(avg_confidence),
            'engines_used': engines_used,
            'preprocessing': preprocess_level
        })
    
    except Exception as e:
        print(f"❌ خطا: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    engines = ['EasyOCR']
    if TESSERACT_AVAILABLE:
        engines.append('Tesseract')
    
    return jsonify({
        'status': 'healthy',
        'message': 'سرور در حال اجرا است',
        'engines': engines,
        'multi_engine': TESSERACT_AVAILABLE
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 سرور OCR چندموتوره با قابلیت خواندن هر نوع متن")
    print("📍 آدرس: http://localhost:5000")
    print("=" * 70)
    print("✨ موتورهای OCR:")
    print("   • EasyOCR ✅")
    if TESSERACT_AVAILABLE:
        print("   • Tesseract ✅")
    else:
        print("   • Tesseract ❌ (نصب نشده)")
    print("-" * 70)
    print("🎯 قابلیت‌ها:")
    print("   • خواندن هر نوع متن (IC، خازن، مقاومت، متن معمولی)")
    print("   • ترکیب هوشمند نتایج از چند موتور")
    print("   • تصحیح خودکار بر اساس نوع محتوا")
    print("   • پیش‌پردازش قابل تنظیم")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# فقط در توسعه: CORS همه دامین‌ها. در پروداکشن محدودش کنید.
CORS(app)

@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify(ok=True, source="python", message="Hello from Python!"), 200

@app.route("/api/process", methods=["POST"])
def process():
    """
    ورودی‌ها:
      - متن: field با نام 'text'
      - فایل اختیاری: field با نام 'file'
    خروجی: JSON شامل echo متن + متادیتای فایل (اگر بود)
    """
    text = request.form.get("text", "")
    file_info = None

    if "file" in request.files:
        f = request.files["file"]
        # اینجا هر پردازشی خواستید انجام دهید (OCR، …)
        file_info = {
            "filename": f.filename,
            "content_type": f.content_type,
            "size_bytes": len(f.read())  # فقط برای دمو؛ نخوانید اگر نیاز به داده دارید
        }

    return jsonify(
        ok=True,
        source="python",
        received_text=text,
        file=file_info,
        note="You can plug your real logic (OCR, ML, etc.) here."
    ), 200

if __name__ == "__main__":
    # برای توسعه
    app.run(host="127.0.0.1", port=5001, debug=True)

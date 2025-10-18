from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)

# CORS: اجازه می‌دهد frontend روی پورت 5173 به این API وصل شود
CORS(app)

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "itt-backend",
        "time": datetime.utcnow().isoformat() + "Z"
    }), 200

if __name__ == "__main__":
    # dev server
    app.run(host="0.0.0.0", port=5000, debug=True)

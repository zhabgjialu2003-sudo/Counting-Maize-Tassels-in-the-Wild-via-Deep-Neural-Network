from flask import Flask, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# --- Mock Data ---
MOCK_RESULTS = [
    {"image_name": "maize_001.jpg", "count": 37, "confidence": 0.89, "processing_time": 2.4},
    {"image_name": "maize_002.jpg", "count": 42, "confidence": 0.91, "processing_time": 2.1},
    {"image_name": "maize_003.jpg", "count": 29, "confidence": 0.85, "processing_time": 3.0},
    {"image_name": "maize_004.jpg", "count": 35, "confidence": 0.93, "processing_time": 1.8},
    {"image_name": "maize_005.jpg", "count": 31, "confidence": 0.87, "processing_time": 2.6},
]

MOCK_HISTORY = [
    {"result_id": i+1, "image_name": r["image_name"], "tassel_count": r["count"],
     "confidence_score": r["confidence"], "processing_time": r["processing_time"],
     "created_at": f"2026-06-{10+i:02d}", "annotated_image_path": f"/mock/annotated_{r['image_name']}"}
    for i, r in enumerate(MOCK_RESULTS)
]

# --- API Endpoints ---

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "Maize Detector API", "version": "0.1.0"})

@app.route('/api/upload', methods=['POST'])
def upload():
    # Mock: does not actually save file
    return jsonify({"status": "success", "message": "Image uploaded", "image_id": random.randint(100, 999)})

@app.route('/api/predict', methods=['POST'])
def predict():
    result = random.choice(MOCK_RESULTS)
    return jsonify({**result, "status": "success"})

@app.route('/api/history', methods=['GET'])
def history():
    return jsonify({"records": MOCK_HISTORY, "total": len(MOCK_HISTORY)})

@app.route('/api/report/daily', methods=['GET'])
def report_daily():
    return jsonify({
        "date": "2026-06-13",
        "total_uploads": 24, "successful_detections": 22, "failed_detections": 2,
        "average_tassel_count": 31, "system_status": "Normal"
    })

@app.route('/api/report/weekly', methods=['GET'])
def report_weekly():
    return jsonify({
        "week": "2026-06-07 to 2026-06-13",
        "total_uploads": 148, "successful_detections": 139, "failed_detections": 9,
        "most_active_day": "Friday", "average_processing_time": 2.8
    })

@app.route('/api/report/monthly', methods=['GET'])
def report_monthly():
    return jsonify({
        "month": "June 2026",
        "total_uploads": 520, "successful_detections": 496, "failed_detections": 24,
        "average_tassel_count": 34, "model_accuracy_estimate": 0.88
    })

if __name__ == '__main__':
    print("Maize Detector API running at http://localhost:5000")
    print("Test: GET http://localhost:5000/api/health")
    app.run(debug=True, port=5000)

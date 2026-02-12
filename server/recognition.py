# recognition.py
import os
import sys

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

from flask import Blueprint, request, jsonify, session
from .database import db
from .models import Attendance, User, Face
from datetime import datetime, timedelta
from flask import current_app
import pytz
import dlib

DLIB_PREDICTOR_PATH = resource_path(
    "device/shape_predictor_68_face_landmarks.dat"
)
try:
    DLIB_PREDICTOR = dlib.shape_predictor(DLIB_PREDICTOR_PATH)
    print("[SERVER] dlib predictor loaded OK")
except Exception as e:
    print("[SERVER] dlib predictor FAILED:", e)
    DLIB_PREDICTOR = None
    
recognition_bp = Blueprint("recognition", __name__)
KNOWN_FACE_ENCS = []
KNOWN_FACE_IDS = []
FACE_CACHE_READY = False
COOLDOWN = timedelta(minutes=5)



#   CHECK-IN 
@recognition_bp.route("/api/checkin", methods=["POST"])
def api_checkin():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "Invalid user"}), 400

    rec = Attendance(
        user_id=user_id,
        action="checkin",
        timestamp=now_vn()
    )
    db.session.add(rec)
    db.session.commit()
    return jsonify({
        "message": "Check-in recorded",
        "user_id": user_id,
        "time": rec.timestamp.isoformat()
    })


#   CHECK-OUT 
@recognition_bp.route("/api/checkout", methods=["POST"])
def api_checkout():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "Invalid user"}), 400

    rec = Attendance(
        user_id=user_id,
        action="checkout",
        timestamp=now_vn()
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({
        "message": "Check-out recorded",
        "user_id": user_id,
        "time": rec.timestamp.isoformat()
    })


#   AUTO ATTENDANCE 
@recognition_bp.route("/api/auto_attendance", methods=["POST"])
def api_auto_attendance():
    data = request.get_json(silent=True)
    user_id = data.get("user_id") if data else None

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "Invalid user"}), 400
    
    now = now_vn()
    last = Attendance.query \
        .filter_by(user_id=user_id) \
        .order_by(Attendance.timestamp.desc()) \
        .first()
    if last and last.timestamp.tzinfo is None:
        last.timestamp = pytz.timezone("Asia/Ho_Chi_Minh").localize(last.timestamp)


    # CHƯA CÓ BẢN GHI → CHECK-IN
    if not last:
        rec = Attendance(
            user_id=user_id,
            action="checkin",
            timestamp=now
        )
        db.session.add(rec)
        db.session.commit()

        return jsonify({
            "action": "checkin",
            "user_id": user_id,
            "time": rec.timestamp.isoformat()
        })

    # CHƯA ĐỦ COOLDOWN → TỪ CHỐI
    if now - last.timestamp < COOLDOWN:
        remain = COOLDOWN - (now - last.timestamp)
        return jsonify({
            "status": "WAIT",
            "remain_seconds": int(remain.total_seconds())
        }), 429

    # ĐỦ COOLDOWN → ĐẢO TRẠNG THÁI
    next_action = "checkout" if last.action == "checkin" else "checkin"

    rec = Attendance(
        user_id=user_id,
        action=next_action,
        timestamp=now
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({
        "action": next_action,
        "user_id": user_id,
        "time": rec.timestamp.isoformat()
    })
def now_vn():
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
#   UPLOAD FACEFACE
@recognition_bp.route("/api/upload_face", methods=["POST"])
def upload_face():
    user_id = session.get("user_id")
    role = session.get("role")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    target_user_id = request.form.get("user_id", user_id)
    target_user_id = int(target_user_id)

    if role != "admin" and int(user_id) != target_user_id:
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get(target_user_id)
    if not user:
        return jsonify({"error": "Invalid user"}), 400

    f = request.files["file"]
    data = f.read()

    import cv2
    import numpy as np

    img_arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Invalid image"}), 400

    from .security_utils import cipher
    encrypted = cipher.encrypt(data)
    Face.query.filter_by(user_id=target_user_id).delete()

    face = Face(
        user_id=target_user_id,
        image_encrypted=encrypted,
        created_at=now_vn()
        )
    db.session.add(face)

    user.has_face_registered = True
    db.session.commit()
    
    with current_app.app_context():
        preload_face_cache()

    return jsonify({
        "message": "Face uploaded successfully",
        "user_id": target_user_id
    })


#   HISTORY
@recognition_bp.route("/api/history", methods=["GET"])
def api_history():
    role = session.get("role")
    user_id = session.get("user_id")

    if not user_id:
        return jsonify([])

    if role == "admin":
        q = Attendance.query.order_by(Attendance.timestamp.desc())
    else:
        q = Attendance.query.filter_by(user_id=user_id) \
            .order_by(Attendance.timestamp.desc())

    data = []
    for r in q.limit(500).all():
        data.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": r.user.username if r.user else "Unknown",
            "action": r.action,
            "time": r.timestamp.isoformat()
        })

    return jsonify(data)
@recognition_bp.route("/api/recognize", methods=["POST"])
def api_recognize():
    if "image" not in request.files:
        return jsonify({"user_id": None})

    file = request.files["image"]
    img_bytes = file.read()

    import cv2
    import numpy as np
    import face_recognition

    img_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"user_id": None})

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    encs = face_recognition.face_encodings(rgb)
    if not encs:
        return jsonify({"user_id": None})

    face_enc = encs[0]

    if not FACE_CACHE_READY:
        return jsonify({"user_id": None})

    if len(KNOWN_FACE_ENCS) == 0:
        return jsonify({"user_id": None})


    dists = face_recognition.face_distance(KNOWN_FACE_ENCS, face_enc)
    best_idx = int(np.argmin(dists))

    THRESHOLD = 0.45  # hoặc 0.48

    if dists[best_idx] <= THRESHOLD:
        return jsonify({"user_id": KNOWN_FACE_IDS[best_idx]})

    return jsonify({"user_id": None})
def preload_face_cache():
    global KNOWN_FACE_ENCS, KNOWN_FACE_IDS, FACE_CACHE_READY

    print("[SERVER] Preloading face encodings...")

    KNOWN_FACE_ENCS.clear()
    KNOWN_FACE_IDS.clear()

    import cv2
    import numpy as np
    import face_recognition
    from .security_utils import cipher

    faces = Face.query.all()
    for f in faces:
        try:
            raw = cipher.decrypt(f.image_encrypted)
            arr = np.frombuffer(raw, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encs = face_recognition.face_encodings(rgb)
            if not encs:
                continue

            KNOWN_FACE_ENCS.append(encs[0])
            KNOWN_FACE_IDS.append(f.user_id)

        except Exception as e:
            print(f"[CACHE] Face {f.user_id} failed:", e)

    FACE_CACHE_READY = True
    print(f"[SERVER] Face cache ready: {len(KNOWN_FACE_IDS)} faces")

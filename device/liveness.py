import os
import cv2
import dlib
import numpy as np
import time
from imutils import face_utils
import sys
EYE_AR_THRESH = 0.32
EYE_AR_CONSEC_FRAMES = 1
AUTO_LIVE_AFTER = 3.0
_COUNTER = 0
_BLINKED = False
_START_TIME = None

if getattr(sys, 'frozen', False):
    BASEDIR = sys._MEIPASS
else:
    BASEDIR = os.path.dirname(__file__)

PREDICTOR_PATH = os.path.join(
    BASEDIR,
    "device",
    "shape_predictor_68_face_landmarks.dat"
)

detector = dlib.get_frontal_face_detector()

if not os.path.exists(PREDICTOR_PATH):
    print("[WARN] shape predictor not found → liveness fallback enabled")
    PREDICTOR = None
else:
    PREDICTOR = dlib.shape_predictor(PREDICTOR_PATH)

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C) if C != 0 else 0.0

def check_blink(frame):
    """
    True nếu:
    - chớp mắt
    - hoặc đứng trước camera đủ lâu (fallback)
    - hoặc thiếu model (không crash hệ thống)
    """
    global _COUNTER, _BLINKED, _START_TIME

    if _BLINKED:
        return True

    if PREDICTOR is None:
        return True

    if frame is None:
        return False

    if _START_TIME is None:
        _START_TIME = time.time()

    if time.time() - _START_TIME >= AUTO_LIVE_AFTER:
        _BLINKED = True
        return True

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 1)

    if len(rects) == 0:
        _COUNTER = 0
        return False

    rect = rects[0]
    shape = PREDICTOR(gray, rect)
    shape = face_utils.shape_to_np(shape)

    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]

    ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0

    if ear < EYE_AR_THRESH:
        _COUNTER += 1
    else:
        if _COUNTER >= EYE_AR_CONSEC_FRAMES:
            _BLINKED = True
            return True
        _COUNTER = 0

    return False


def reset_liveness():
    global _COUNTER, _BLINKED, _START_TIME
    _COUNTER = 0
    _BLINKED = False
    _START_TIME = None

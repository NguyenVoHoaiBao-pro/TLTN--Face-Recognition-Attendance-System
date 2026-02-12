# device.py
import ctypes
import sys
import os  

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if sys.platform == "win32":
    myappid = u'ace.attendance.face.1'  
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
import cv2

def open_camera():
    for i in range(0, 3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

        if cap.isOpened():
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ret, frame = cap.read()
            if ret:
                print(f"[INFO] Camera {i} OK {frame.shape}")
                return cap

        cap.release()
    return None
import os
os.environ["FACE_RECOGNITION_MODELS"] = resource_path(".")
import threading
import time
import traceback
import webbrowser
import requests
import winsound
import numpy as np
import face_recognition
from PIL import Image, ImageTk
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from scipy.spatial import distance as dist
from dotenv import load_dotenv

if getattr(sys, 'frozen', False):
    BASEDIR = sys._MEIPASS
else:
    BASEDIR = os.path.dirname(__file__)

ENV_PATH = os.path.join(BASEDIR, ".env")
load_dotenv(ENV_PATH)

SERVER_URL = os.getenv("SERVER_URL")
FERNET_KEY = os.getenv("FERNET_KEY")

print("[DEVICE] ENV PATH =", ENV_PATH)
print("[DEVICE] SERVER_URL =", SERVER_URL)
# Ngưỡng Eye Aspect Ratio: dưới mức này coi là mắt nhắm
EYE_AR_THRESH = 0.20
# Số frame liên tiếp mắt nhắm để coi là đã chớp mắt
EYE_AR_CONSEC_FRAMES = 2
# File model dlib 68 điểm landmark cho phát hiện mắt (liveness)
PREDICTOR_PATH = resource_path("shape_predictor_68_face_landmarks.dat")

cipher = None
if FERNET_KEY:
    try:
        from cryptography.fernet import Fernet
        cipher = Fernet(FERNET_KEY.encode())
        print("[INFO] Fernet key loaded successfully")
    except Exception as e:
        cipher = None
        print("[WARN] Fernet init failed:", e)
else:
    cipher = None
    print("[INFO] No Fernet key found in .env")

_have_dlib = True
try:
    import dlib
except Exception:
    _have_dlib = False
detector = None
predictor = None
if _have_dlib:
    try:
        detector = dlib.get_frontal_face_detector()
        if os.path.exists(PREDICTOR_PATH):
            predictor = dlib.shape_predictor(PREDICTOR_PATH)
        else:
            predictor = None
    except Exception:
        detector = None
        predictor = None


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)
class FaceAttendanceDevice:
    def __init__(self):
        self.server_url = SERVER_URL or "http://127.0.0.1:5000"
        print("[DEVICE] SERVER_URL =", self.server_url)
        self.cap = None
        self.running = False
        self.current_user = None
        self.eye_blink_counter = 0
        self.liveness_last_checked = 0
        self.liveness_interval = 0.4
        self.live_user = None
        self.is_live = False
        self.attendance_lock = threading.Lock()
        self._build_ui()
        self.last_recognize = 0
        self.last_detected_user = None
        self.RECOGNIZE_INTERVAL = 1.0
        self.last_face_seen = 0
        self.recognize_running = False
        self.user_lock = threading.Lock()
        self.attended_user = None
        self.last_face_detect = 0
        self.FACE_DETECT_INTERVAL = 0.3
        self.last_bbox = None
        self.last_locations = []
        self.USER_HOLD_TIME = 4.0
        self.auto_attendance_running = False
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.last_ui_update = 0
        self.video_target_width = 800
        self.last_cooldown_log = 0
        self.COOLDOWN_LOG_INTERVAL = 5
        self._ui_last_status = None
        self.eye_closed_frames = 0
        self.eye_was_closed = False
        self._ui_last_user = None
        self.liveness_started = False
        self.display_frame = None




    def _ui_loop(self):
        if not self.running:
            return

        with self.frame_lock:
            if self.display_frame is not None:
                frame = self.display_frame.copy()
            elif self.latest_frame is not None:
                frame = self.latest_frame.copy()
            else:
                frame = None


        if frame is not None:
            self._update_video_label(frame)

        # ~30 FPS
        self.app.after(33, self._ui_loop)
    def _reset_liveness_state(self):
        self.eye_blink_counter = 0
        self.eye_closed_frames = 0
        self.eye_was_closed = False
        self.liveness_started = False

    def draw_corner_box(self, img, l, t, r, b, color):
        d = 25
        thickness = 3

        cv2.line(img, (l, t), (l+d, t), color, thickness)
        cv2.line(img, (l, t), (l, t+d), color, thickness)

        cv2.line(img, (r, t), (r-d, t), color, thickness)
        cv2.line(img, (r, t), (r, t+d), color, thickness)

        cv2.line(img, (l, b), (l+d, b), color, thickness)
        cv2.line(img, (l, b), (l, b-d), color, thickness)

        cv2.line(img, (r, b), (r-d, b), color, thickness)
        cv2.line(img, (r, b), (r, b-d), color, thickness)

        
    def start_camera(self):
        if self.cap is None:
            self.cap = open_camera()
            if self.cap is None:
                messagebox.showerror("Camera", "Không tìm thấy camera!")
                return

        self.running = True

        threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._process_loop, daemon=True).start()

        # BẮT ĐẦU VẼ VIDEO
        self.app.after(0, self._ui_loop)


    def stop_camera(self):
        self.running = False
        time.sleep(0.2)
        if self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            with self.frame_lock:
                self.latest_frame = frame
    def _process_loop(self):
        while self.running:
            try:
                with self.frame_lock:
                    if self.latest_frame is None:
                        time.sleep(0.005)
                        continue
                    frame = self.latest_frame.copy()

                orig_frame = frame.copy()

                h, w = frame.shape[:2]
                if frame is None or frame.size == 0:
                    continue
    
                small = cv2.resize(frame, (640, 360))
                scale_x = frame.shape[1] / small.shape[1]
                scale_y = frame.shape[0] / small.shape[0]

                rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                now = time.time()
                if now - self.last_face_detect > self.FACE_DETECT_INTERVAL:
                    locations = face_recognition.face_locations(
                        rgb_small,
                        model="hog",
                        number_of_times_to_upsample=1
                    )
                    self.last_face_detect = now
                    self.last_locations = locations
                else:
                    locations = self.last_locations
                bbox = None

                if len(locations) > 1:
                    areas = [
                        (bottom - top) * (right - left)
                        for (top, right, bottom, left) in locations
                    ]
                    idx = int(np.argmax(areas))
                    locations = [locations[idx]]

                if locations:
                    self.last_face_seen = time.time()   
                    (top, right, bottom, left) = locations[0]
                    t = int(top * scale_y)
                    b = int(bottom * scale_y)
                    l = int(left * scale_x)
                    r = int(right * scale_x)
            
                    # Clamp an toàn
                    h, w = frame.shape[:2]
                    t = max(0, t)
                    l = max(0, l)
                    b = min(h, b)
                    r = min(w, r)
                    bbox = (l, t, r, b)
                    self.last_bbox = bbox
                    face_img = frame[t:b, l:r]
                    # if predictor and self.current_user:
                    # if predictor and (self.current_user or self.last_detected_user):
                    # if predictor and self.current_user and self.current_user == self.last_detected_user:
                    if (
                        predictor
                        and self.current_user
                        and self.current_user == self.last_detected_user
                        and self.attended_user != self.current_user
                    ):
                        now = time.time()
                        if now - self.liveness_last_checked > self.liveness_interval:
                            try:
                                gray_full = cv2.cvtColor(orig_frame, cv2.COLOR_BGR2GRAY)
                                rect = dlib.rectangle(l, t, r, b)

                                live = self._detect_liveness_from_rect(gray_full, rect)

                                if live:
                                    self.is_live = True
                                    self.live_user = self.current_user

                                    self.app.after(0, lambda: self.status_live.config(
                                        text="Liveness: LIVE",
                                        bootstyle="success"
                                    ))
                                    if not self.auto_attendance_running:
                                        self.auto_attendance_running = True
                                        threading.Thread(
                                            target=self._auto_attendance,
                                            args=(self.current_user,),
                                            daemon=True
                                        ).start()

                                elif self.liveness_started:
                                    self.app.after(0, lambda: self.status_live.config(
                                        text="Liveness: checking...",
                                        bootstyle="warning"
                                    ))

                                else:
                                    self.app.after(0, lambda: self.status_live.config(
                                        text="Liveness: ---",
                                        bootstyle="secondary"
                                    ))
                            except Exception:
                                pass
                            self.liveness_last_checked = now
                    if (
                        face_img.size > 0
                        and not self.recognize_running
                        and (
                            self.current_user is None
                            or time.time() - self.last_face_seen > self.USER_HOLD_TIME
                        )
                    ):
                        if time.time() - self.last_recognize > self.RECOGNIZE_INTERVAL:
                            self.recognize_running = True
                            self.last_recognize = time.time()

                            threading.Thread(
                                target=self._do_recognize,
                                args=(face_img.copy(),),
                                daemon=True
                            ).start()
                else:
                    self.last_bbox = None
                    self.current_user = None
                    self.last_detected_user = None
                    self.is_live = False
                    self.live_user = None
                    self.liveness_last_checked = 0
                    self._reset_liveness_state()
                    self.live_time = None

                    if time.time() - self.last_face_seen > self.USER_HOLD_TIME:
                        self.attended_user = None
                        self.auto_attendance_running = False
                    self.eye_blink_counter = 0
                    self.liveness_last_checked = 0
                    self.eye_closed_frames = 0
                    self.eye_was_closed = False
                    self.liveness_started = False
                    self.is_live = False
                    self.app.after(0, lambda: self.status_live.config(
                        text="Liveness: ---",
                        bootstyle="secondary"
                    ))
                    self.app.after(0, lambda: self.status_action.config(
                        text="Action: ---",
                        bootstyle="secondary"
                    ))
                if self.last_bbox and (time.time() - self.last_face_seen < 0.08):
                    l, t, r, b = self.last_bbox
                    uid = self.last_detected_user or self.current_user
                    color = (0, 255, 0) if uid else (0, 0, 255)
                    label = f"ID: {uid}" if uid else "Detecting..."

                    self.draw_corner_box(frame, l, t, r, b, color)
                    cv2.putText(frame, label, (l, t - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                with self.frame_lock:
                    self.display_frame = frame.copy()
            except Exception:
                traceback.print_exc()
                time.sleep(0.01)
    def _detect_liveness_from_rect(self, gray, rect):
        try:
            shape = predictor(gray, rect)
        except Exception:
            return False
        coords = np.array([[p.x, p.y] for p in shape.parts()])
        leftEye = coords[36:42]
        rightEye = coords[42:48]
        ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0
        if ear < EYE_AR_THRESH:
            self.liveness_started = True
            self.eye_closed_frames += 1

            if self.eye_closed_frames >= EYE_AR_CONSEC_FRAMES:
                self.eye_was_closed = True
            return False
        else:
            if self.eye_was_closed:
                print("[LIVENESS] BLINK OK")
                self.eye_closed_frames = 0
                self.eye_was_closed = False
                return True

            self.eye_closed_frames = 0
            return False
    def _do_recognize(self, img):
        try:
            uid = self.recognize_from_server(img)
            if uid:
                with self.user_lock:
                    self.last_detected_user = uid
                    if self.current_user != uid:
                        self.current_user = uid
                        self.attended_user = None
                        self.last_face_seen = time.time()
                        self.liveness_last_checked = 0
                        self.auto_attendance_running = False
                        self.attended_user = None

                        self.eye_blink_counter = 0
                        self.is_live = False
                        self.live_user = None
                        self.live_time = None
                        self.liveness_started = False
                self.app.after(0, lambda: self.status_user.config(
                    text=f"User: {uid}"
                ))
        except Exception as e:
            print("[RECOGNIZE THREAD ERROR]", e)
        finally:
            with self.user_lock:
                self.recognize_running = False
    def recognize_from_server(self, frame):
        try:
            frame = cv2.resize(frame, (224, 224))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            ok, buf = cv2.imencode(
                ".jpg",
                rgb,
                [cv2.IMWRITE_JPEG_QUALITY, 90]
            )
            if not ok:
                return None

            res = requests.post(
                f"{self.server_url}/api/recognize",
                files={"image": buf.tobytes()},
                timeout=4
            )
            if res.status_code == 200:
                return res.json().get("user_id")
        except Exception as e:
            self.last_network_error = time.time()
            print("[RECOGNIZE ERROR]", e)
        return None
    def _safe_message(self, func, *args, **kwargs):
        self.app.after(0, lambda: func(*args, **kwargs))
    def _post_action(self, action):
        import requests
        url = f"{self.server_url}/api/{action}"
        payload = {"user_id": self.current_user}
        try:
            res = requests.post(url, json=payload, timeout=4)
            if res.status_code == 200:
                data = res.json()
                self._play_sound(action)
                self.is_live = False
                self.live_user = None
                self.live_time = None
                self.eye_blink_counter = 0
            else:
                self._safe_message(messagebox.showerror, "Lỗi server",
                                   f"Server trả lỗi: {res.status_code}\n{res.text}")
        except Exception as e:
            self.last_network_error = time.time()
            self._safe_message(messagebox.showerror, "Lỗi kết nối",
                               f"Không kết nối được server: {e}\nURL={url}")
    def _auto_attendance(self, user_id):
        acquired = self.attendance_lock.acquire(blocking=False)
        if not acquired:
            return
        try:
            res = requests.post(
                f"{self.server_url}/api/auto_attendance",
                json={"user_id": user_id},
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                print(f"[AUTO] {data['action']} success")

                self.attended_user = user_id
                self.current_user = None
                self.last_detected_user = None
                self.is_live = False
                self.eye_blink_counter = 0
                self.liveness_last_checked = 0
                self.last_face_seen = 0
                self.last_bbox = None
                self.last_locations = []
                self.app.after(0, lambda: self.status_live.config(
                    text="Liveness: ---",
                    bootstyle="secondary"
                ))
                self.app.after(0, lambda: self.status_user.config(
                    text="User: ---"
                ))
                self.app.after(0, lambda: self.status_label.config(
                    text="Đưa mặt vào camera",
                    bootstyle="secondary"
                ))
                self._play_sound(data["action"])
                self.app.after(0, lambda: self.status_action.config(
                    text=f"Action: {data['action'].upper()}",
                    bootstyle="info"
                ))
            elif res.status_code == 429:
                data = res.json()
                now = time.time()
                if now - self.last_cooldown_log > self.COOLDOWN_LOG_INTERVAL:
                    print(f"[AUTO] cooldown {data['remain_seconds']}s")
                    self.last_cooldown_log = now
        except Exception as e:
            print("[AUTO] network error:", e)
        finally:
            self.auto_attendance_running = False
            if acquired:
                self.attendance_lock.release()
    def check_in(self):
        if not self.current_user:
            messagebox.showerror("Lỗi", "Không nhận diện được khuôn mặt!")
            return
        if not self.is_live:
            messagebox.showwarning("Liveness", "Vui lòng chớp mắt để xác thực!")
            return
        uid = self.current_user
        threading.Thread(
            target=self._auto_attendance,
            args=(uid,),
            daemon=True
        ).start()
        self._play_sound("checkin")
    def check_out(self):
        if not self.current_user:
            messagebox.showerror("Lỗi", "Không nhận diện được khuôn mặt!")
            return
        threading.Thread(target=self._post_action, args=("checkout",), daemon=True).start()
    def _build_ui(self):
        FONT_TITLE = ("Segoe UI", 14, "bold")
        FONT_LABEL = ("Segoe UI", 12)
        FONT_SMALL = ("Segoe UI", 10)
        self.app = ttk.Window(themename="flatly")
        self.app.title("Face Attendance (Optimized)")
        self.app.geometry("1000x640")
        try:
            icon_path = os.path.join(BASEDIR, "face.ico")
            self.app.iconbitmap(icon_path)
        except Exception as e:
            print("[ICON] load failed:", e)
        left = ttk.Frame(self.app)
        left.grid(row=0, column=0, padx=20, pady=20, sticky="ns")
        self.right = ttk.Frame(self.app)
        self.right.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.app.columnconfigure(1, weight=1)
        self.app.rowconfigure(0, weight=1)
        def on_resize(event):
            self.video_target_width = max(400, event.width - 40)
        self.right.bind("<Configure>", on_resize)
        card = ttk.Frame(left, padding=18, bootstyle="light")
        card.pack(fill=X, pady=15)
        ttk.Label(card, text="👤 NHÂN VIÊN",
                font=("Segoe UI", 14, "bold")).pack(anchor=W)
        self.status_user = ttk.Label(
            card,
            text="---",
            font=("Segoe UI", 13, "bold"),
            bootstyle="primary"
        )
        self.status_user.pack(anchor=W, pady=4)
        self.status_action = ttk.Label(
            card,
            text="Hành động: ---",
            font=FONT_LABEL
        )
        self.status_action.pack(anchor=W, pady=2)
        self.status_live = ttk.Label(
            card,
            text="Liveness: ---",
            font=FONT_LABEL
        )
        self.status_live.pack(anchor=W, pady=2)
        ttk.Button(left, text="Xem Lịch Sử (Web)",
                   command=lambda: webbrowser.open(self.server_url),
                   bootstyle="secondary outline", width=20).pack(pady=5)
        self.video_label = ttk.Label(self.right)
        self.video_label.pack(fill="both", expand=True)
        self.status_label = ttk.Label(
            self.app,
            text="Đưa mặt vào camera",
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, pady=10)
        self.app.protocol("WM_DELETE_WINDOW", self._on_close)
    def _update_video_label(self, frame):
        now = time.time()
        if now - self.last_ui_update < 0.08:
            return
        self.last_ui_update = now
        try:
            right_w = self.video_target_width
            h, w = frame.shape[:2]
            scale = right_w / w
            display_h = int(h * scale)
            frame_disp = cv2.resize(frame, (right_w, display_h))
            img = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=pil)
            def setter():
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)

                if self.current_user != self._ui_last_user:
                    self.status_user.config(
                        text=f"User: {self.current_user}" if self.current_user else "User: ---"
                    )
                    self._ui_last_user = self.current_user
                if self.current_user and self.is_live:
                    status = ("Xác thực thành công", "success")
                elif self.current_user:
                    status = ("Vui lòng chớp mắt", "warning")
                else:
                    status = ("Đưa mặt vào camera", "secondary")

                if status != self._ui_last_status:
                    self.status_label.config(text=status[0], bootstyle=status[1])
                    self._ui_last_status = status
            self.app.after(0, setter)
        except Exception:
            traceback.print_exc()
    def _play_sound(self, action):
        try:
            base = os.path.join(BASEDIR, "sounds")
            if action == "checkin":
                winsound.PlaySound(
                    os.path.join(base, "checkin.wav"),
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            elif action == "checkout":
                winsound.PlaySound(
                    os.path.join(base, "checkout.wav"),
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
        except Exception as e:
            print("[SOUND] error:", e)
    def _on_close(self):
        self.stop_camera()
        try:
            self.app.destroy()
        except:
            pass
    def run(self):
        try:
            self.start_camera()
            self.app.mainloop()
        finally:
            self.stop_camera()
if __name__ == "__main__":
    app = FaceAttendanceDevice()
    app.run()

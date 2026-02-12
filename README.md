# ACE ATTENDANCE SYSTEM

ACE Attendance System là hệ thống chấm công thông minh bằng nhận diện khuôn mặt (Face Recognition Attendance System), được xây dựng theo mô hình Client – Server, phục vụ đồ án hoặc tiểu luận tốt nghiệp.

Hệ thống tập trung vào xử lý realtime, độ trễ thấp, có cơ chế chống gian lận cơ bản và trải nghiệm người dùng tương tự máy chấm công thực tế.

---

## Environment Configuration

Dự án sử dụng biến môi trường để cấu hình hệ thống.

Người dùng cần tạo file `.env` dựa trên file `.env.example` có sẵn trong từng thư mục `device` và `server`.

Các file `.env` chứa thông tin môi trường như:
- Địa chỉ server
- Khoá mã hoá
- Thông tin kết nối cơ sở dữ liệu

Vì lý do bảo mật, các file `.env` **không được đưa lên GitHub** và đã được khai báo trong `.gitignore`.

---

## Tổng quan

ACE Attendance System cho phép:

- Tự động check-in / check-out không cần thao tác thủ công
- Nhận diện khuôn mặt realtime với độ trễ thấp
- Chống gian lận cơ bản bằng liveness detection (chớp mắt)
- Quản lý dữ liệu tập trung thông qua server
- Giao diện trực quan, mô phỏng thiết bị chấm công thực tế

Hệ thống phù hợp cho:
- Đồ án môn học
- Tiểu luận / đồ án tốt nghiệp
- Demo các hệ thống AI và Computer Vision

---

## Kiến trúc hệ thống (Client – Server)

Hệ thống được thiết kế theo mô hình Client – Server, tách biệt rõ ràng trách nhiệm giữa các thành phần.

### Device (Client)
- Camera
- Giao diện người dùng
- Liveness detection
- Gửi dữ liệu khuôn mặt lên server thông qua HTTP API

### Server
- Nhận ảnh từ device
- Trích xuất face encoding
- So khớp với dữ liệu trong database
- Xử lý logic chấm công (check-in / check-out)

### Database
- Lưu thông tin người dùng
- Lưu dữ liệu khuôn mặt
- Lưu lịch sử chấm công

Luồng xử lý:

Device không lưu ảnh khuôn mặt và không truy cập trực tiếp database.

---

## Công nghệ sử dụng

- Ngôn ngữ: Python 3.10 – 3.11
- Backend: Flask (REST API)
- Database: MySQL
- ORM: SQLAlchemy
- Face Recognition: face_recognition (dlib)
- Liveness Detection: Eye Blink Detection
- Giao diện: Tkinter + ttkbootstrap
- Mã hoá dữ liệu: Fernet
- Đóng gói ứng dụng: PyInstaller, Inno Setup

---

## Tính năng chính

### Nhận diện khuôn mặt
- Sử dụng face encoding (vector 128 chiều)
- So khớp encoding thay vì ảnh gốc để tăng tốc độ xử lý
- Nhận diện ổn định trong thời gian ngắn với độ trễ thấp

### Tự động check-in / check-out
- Sau khi nhận diện thành công và vượt qua liveness detection
- Device tự động gửi yêu cầu chấm công lên server
- Server quyết định hành động check-in hoặc check-out
- Có cơ chế cooldown để chống spam

### Liveness Detection
- Phát hiện chớp mắt
- Ngăn chặn việc sử dụng ảnh in hoặc ảnh chụp màn hình
- Có thể mở rộng thêm các phương pháp nâng cao

### Realtime và tối ưu hiệu năng
- Resize frame trước khi xử lý
- Bỏ frame cũ để giảm độ trễ
- FPS trung bình 25–30 trong môi trường LAN

### Giao diện người dùng
- Hiển thị camera realtime
- Hiển thị trạng thái nhận diện
- Hiển thị trạng thái liveness
- Hiển thị kết quả check-in / check-out
- Có âm thanh phản hồi khi chấm công

---

## Cấu trúc thư mục
ace_attendance_system
|
|-- device
| |-- device.py
| |-- liveness.py
| |-- sounds/
| |-- shape_predictor_68_face_landmarks.dat
| |-- .env.example
|
|-- server
| |-- app.py
| |-- recognition.py
| |-- models.py
| |-- database.py
| |-- .env.example
|
|-- requirements.txt
|-- README.md

---

## Hướng dẫn cài đặt và chạy

### Yêu cầu hệ thống
- Windows 10 hoặc Windows 11
- Python 3.10 hoặc mới hơn
- Webcam
- MySQL Server
- Các máy chạy chung mạng LAN

### Cài đặt thư viện

Cài đặt các thư viện cần thiết:

---

## Cấu hình môi trường

### Server (`server/.env`)

Tạo file `.env` dựa trên `.env.example`:

### Device (`device/.env`)

Tạo file `.env` dựa trên `.env.example`:


---

## Chạy hệ thống

### Chạy server


Server sẽ khởi động tại địa chỉ:

### Chạy device


Sau khi chạy, giao diện camera sẽ hiển thị và hệ thống bắt đầu nhận diện khuôn mặt realtime.

---

## Database (tóm tắt)

### User
- id
- username

### Face
- user_id
- encoding hoặc image_encrypted

### Attendance
- user_id
- action (checkin / checkout)
- timestamp

---

## Bảo mật và chống gian lận

- Device không lưu ảnh khuôn mặt
- Nhận diện tập trung tại server
- Có liveness detection
- Có cooldown phía server để chống spam

---

## Điểm mạnh cho đồ án

- Kiến trúc Client – Server rõ ràng
- Áp dụng AI và Computer Vision thực tế
- Hệ thống hoạt động realtime
- Có cơ chế chống gian lận
- Có thể mở rộng và đóng gói thành sản phẩm hoàn chỉnh

---

## Hướng phát triển

- Nhận diện nhiều khuôn mặt cùng lúc
- Anti-spoof nâng cao
- Hỗ trợ thiết bị IoT hoặc mobile
- Dashboard thống kê
- Triển khai trên cloud

---

## Tác giả

Nguyễn Võ Hoài Bảo  
GitHub: https://github.com/NguyenVoHoaiBao-pro

---

## Giấy phép

Dự án phục vụ mục đích học tập và nghiên cứu.

---

Chỉ cần làm theo README là có thể chạy toàn bộ hệ thống.


=======
# TLTN--Face-Recognition-Attendance-System
Attendance System is a client–server face recognition attendance system using real-time camera input and liveness detection (eye blink). The system is designed for academic projects and graduation theses, focusing on low latency, anti-spoofing, and real-world attendance workflow.


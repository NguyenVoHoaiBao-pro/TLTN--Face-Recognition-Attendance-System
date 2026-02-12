from datetime import datetime
import pytz
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash
from .security_utils import cipher
def now_vn():
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    _full_name = db.Column("full_name", db.LargeBinary)
    _age = db.Column("age", db.LargeBinary)
    dob = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    position = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)

    role = db.Column(db.String(20), default="employee") 
    has_face_registered = db.Column(db.Boolean, default=False)

    faces = db.relationship("Face", backref="user", lazy=True)
    attendances = db.relationship("Attendance", backref="user", lazy=True)
    complaints = db.relationship("Complaint", backref="user", lazy=True)
    notifications_sent = db.relationship(
        "Notification",
        foreign_keys="Notification.sender_id",
        back_populates="sender",
        lazy=True
    )
    notifications_received = db.relationship(
        "Notification",
        foreign_keys="Notification.receiver_id",
        back_populates="receiver",
        lazy=True
    )

    @property
    def full_name(self):
        return cipher.decrypt(self._full_name).decode() if self._full_name else None

    @full_name.setter
    def full_name(self, value):
        self._full_name = cipher.encrypt(value.encode())

    @property
    def age(self):
        return int(cipher.decrypt(self._age).decode()) if self._age else None

    @age.setter
    def age(self, value):
        self._age = cipher.encrypt(str(value).encode())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




class Face(db.Model):
    __tablename__ = "face"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_encrypted = db.Column(db.LargeBinary(length=(2**32)-1), nullable=False) 
    created_at = db.Column(db.DateTime, default=now_vn)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(20), nullable=False) 
    timestamp = db.Column(db.DateTime, default=now_vn)


# class Complaint(db.Model):
#     __tablename__ = "complaint"

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#     attendance_id = db.Column(db.Integer, db.ForeignKey("attendance.id"), nullable=False)
#     reason = db.Column(db.String(255), nullable=False)
#     status = db.Column(db.String(20), default="pending") 
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     attendance = db.relationship("Attendance", backref="complaints", lazy=True)



# class Notification(db.Model):
#     __tablename__ = "notification"

#     id = db.Column(db.Integer, primary_key=True)
#     message = db.Column(db.String(255), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#     receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) 

#     sender = db.relationship("User", foreign_keys=[sender_id], back_populates="notifications_sent")
#     receiver = db.relationship("User", foreign_keys=[receiver_id], back_populates="notifications_received")
class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)

    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="notifications_sent"
    )
    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="notifications_received"
    )


class Complaint(db.Model):
    __tablename__ = "complaint"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    attendance_id = db.Column(db.Integer, db.ForeignKey("attendance.id"), nullable=False)

    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=now_vn)

    attendance = db.relationship("Attendance", backref="complaints", lazy=True)

from server.app import create_app
from server.database import db
from server.models import User, Attendance, Face
from datetime import datetime
from server.security_utils import cipher 

app = create_app()

with app.app_context():

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        print("Created admin: admin / admin123")
    else:
        print("Admin existed")

    emp = User.query.filter_by(username="employee").first()
    if not emp:
        emp = User(username="employee", role="employee")
        emp.set_password("123456")
        db.session.add(emp)
        db.session.commit()
        print("Created employee: employee / 123456")
    else:
        print("Employee existed")

    if emp:
        if Attendance.query.filter_by(user_id=emp.id).count() == 0:
            log1 = Attendance(user_id=emp.id, action="checkin", timestamp=datetime.utcnow())
            log2 = Attendance(user_id=emp.id, action="checkout", timestamp=datetime.utcnow())
            db.session.add_all([log1, log2])
            db.session.commit()
            print("Added sample attendance logs")
        else:
            print("Attendance already existed")

    if emp:
        if Face.query.filter_by(user_id=emp.id).count() == 0:
            
            print("Added sample encrypted face data")
        else:
            print("Face data already existed")

#init_users
from .app import create_app
from .database import db
from .models import User

def init_users():
    app = create_app()
    with app.app_context():
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", password="123", role="manager")
            employee = User(username="employee", password="123", role="employee")
            db.session.add(admin)
            db.session.add(employee)
            db.session.commit()
            print("User mẫu đã được tạo: admin/123 (manager), employee/123 (employee)")
        else:
            print("User mẫu đã tồn tại, không tạo lại.")

if __name__ == "__main__":
    init_users()

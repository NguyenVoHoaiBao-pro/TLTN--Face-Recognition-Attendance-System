from datetime import datetime, time
from server.database import db
from server.models import Attendance

AUTO_CHECKOUT_TIME = time(21, 0)

def auto_checkout_if_needed():
    now = datetime.now()
    today = now.date()

    if now.time() < AUTO_CHECKOUT_TIME:
        print("[AUTO CHECKOUT] Not time yet")
        return
    checkout_dt = datetime.combine(today, AUTO_CHECKOUT_TIME)
    # Lấy danh sách user có phát sinh hôm nay
    user_ids = db.session.query(Attendance.user_id).filter(
        db.func.date(Attendance.timestamp) == today
    ).distinct().all()
    count = 0
    for (user_id,) in user_ids:
        last = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.timestamp) == today
        ).order_by(Attendance.timestamp.desc()).first()
        if last and last.action == "checkin":
            duration = (checkout_dt - last.timestamp).total_seconds() / 3600

            checkout = Attendance(
                user_id=user_id,
                action="checkout",
                timestamp=checkout_dt,
            )

            db.session.add(checkout)
            count += 1
    if count:
        db.session.commit()
        print(f"[AUTO CHECKOUT] {count} users auto checked-out at 21:00")
    else:
        print("[AUTO CHECKOUT] No users to checkout")

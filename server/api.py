from flask import Blueprint, session, jsonify
from datetime import datetime
from .models import Notification
from .database import db
from .security_utils import login_required

api = Blueprint("api", __name__)

@api.route("/api/notifications/read", methods=["POST"])
@login_required
def mark_notifications_read():
    user_id = session.get("user_id")

    Notification.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).update({
        Notification.is_read: True,
        Notification.read_at: datetime.utcnow()
    })

    db.session.commit()
    return jsonify({"status": "ok"})

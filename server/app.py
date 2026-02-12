import os
import threading
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, session

# ===== LOAD ENV =====
load_dotenv()

# ===== IMPORT SERVER MODULES =====
from server.database import init_db
from server.discovery import start_discovery
from server.auth import auth_bp
from server.web_ui import web_ui
from server.api import api
from server.recognition import recognition_bp

# ===== AUTO LOGIC =====
from server.auto_logic import auto_checkout_if_needed



def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(recognition_bp)
    app.register_blueprint(web_ui)
    app.register_blueprint(api)

    @app.route("/")
    def home():
        if session.get("user_id"):
            return redirect(url_for("web_ui.dashboard"))
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()

    # import trễ để tránh circular
    from server.recognition import preload_face_cache

    with app.app_context():
        preload_face_cache()

        # ⭐ AUTO CHECKOUT KHI SERVER START
        auto_checkout_if_needed()


    threading.Thread(
        target=start_discovery,
        daemon=True
    ).start()

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    print(f"[SERVER] Running on {HOST}:{PORT}")

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )

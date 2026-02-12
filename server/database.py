import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def init_db(app: Flask):

    DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    DB_USER = os.getenv("MYSQL_USER", "root")
    DB_PASS = os.getenv("MYSQL_PASS", "12345")
    DB_NAME = os.getenv("MYSQL_DB", "attendance_db")

    app.config["SQLALCHEMY_DATABASE_URI"] = \
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

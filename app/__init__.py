from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()  # Mới: Cho real-time và chat

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.config['JSON_AS_ASCII'] = False  # Hỗ trợ Unicode trong JSON responses

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    socketio.init_app(app)  # Mới: Khởi tạo SocketIO với ứng dụng Flask

    # Đăng ký các Blueprints (Modules nghiệp vụ)
    from app.routes.auth import auth_bp
    from app.routes.reception import reception_bp
    from app.routes.doctor import doctor_bp
    from app.routes.pharmacist import pharmacist_bp
    from app.routes.admin import admin_bp
    from app.routes.nurse import nurse_bp
    from app.routes.patient import patient_bp
    from app.routes.search import search_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reception_bp, url_prefix='/reception')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(pharmacist_bp, url_prefix='/pharmacist')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(nurse_bp, url_prefix='/nurse')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(search_bp, url_prefix='/search')

    from app import events  # Mới: Import module sự kiện SocketIO

    @socketio.on('connect')
    def handle_connect():
        print('User connected')

    return app
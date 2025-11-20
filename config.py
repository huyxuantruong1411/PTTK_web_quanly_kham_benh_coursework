import os

class Config:
    # Render sẽ tự động cung cấp biến môi trường DATABASE_URL
    # Nếu chạy local thì dùng SQLite cho nhẹ (hoặc Postgres local nếu bạn cài)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///antamclinic.db')
    
    # Fix lỗi postgres:// của Render (SQLAlchemy yêu cầu postgresql://)
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SECRET_KEY = os.environ.get('SECRET_KEY', 'Key_Bao_Mat_Cua_An_Tam_Clinic')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email config cũng nên lấy từ env
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'huy.tx.1411.@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '@Huydeptrai1411')
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "SOMETHING_SECURE"


    # Email config cũng nên lấy từ env
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'huy.tx.1411.@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '@Huydeptrai1411')
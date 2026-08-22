import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:123456@localhost:3306/message_board'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

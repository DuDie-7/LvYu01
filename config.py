import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    # 修改为你的 MySQL 用户名和密码，数据库名为 message_board
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/message_board'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
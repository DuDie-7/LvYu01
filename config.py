import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:123456@localhost:3306/message_board'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== 新增：跨域场景下的 Session Cookie 配置 =====
    SESSION_COOKIE_SAMESITE = 'None'   # 允许跨站发送 Cookie
    SESSION_COOKIE_SECURE = True       # 仅 HTTPS 环境下发送（Vercel 和 Railway 都是 HTTPS）

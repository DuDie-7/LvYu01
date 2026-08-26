from flask import Flask
from .exts import db, migrate, login_manager
from config import Config
from flask_cors import CORS

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # ===== CORS 配置：允许前端跨域请求 =====
    CORS(app, supports_credentials=True, origins=[
        'https://lv-yu02.vercel.app',   # Vue 前端（生产）
        'http://localhost:5173'         # Vue 前端（本地开发）
    ])
    # ========================================

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'   # 未登录时跳转

    # 导入模型（重要：让 Alembic 能发现这些模型）
    from . import models

    # 注册蓝图
    from .auth import auth_bp
    from .message import message_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(message_bp, url_prefix='/')

    # 用户加载回调（flask-login 需要）
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    return app

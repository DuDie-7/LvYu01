from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from .exts import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 查询用户是否存在
        user = User.query.filter_by(username=username).first()
        if user:
            # 用户存在，验证密码
            if user.password == password:
                login_user(user)
                return redirect(url_for('message.index'))
            else:
                flash('密码错误', 'danger')
        else:
            # 用户不存在，自动创建新用户并登录
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash(f'欢迎 {username}，账号已自动创建并登录', 'success')
            return redirect(url_for('message.index'))
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.password == old_password:
            flash('原密码错误', 'danger')
        elif new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
        elif len(new_password) < 4:
            flash('密码长度至少4位', 'danger')
        else:
            current_user.password = new_password
            db.session.commit()
            flash('密码修改成功，请重新登录', 'success')
            logout_user()
            return redirect(url_for('auth.login'))
    return render_template('change_password.html')
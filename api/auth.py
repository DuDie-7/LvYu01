from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from .exts import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 优先从 JSON 获取数据（Vue 前端使用）
        data = request.get_json()
        if data:
            username = data.get('username')
            password = data.get('password')
        else:
            # 如果没有 JSON，回退到表单数据（兼容原网页版）
            username = request.form.get('username')
            password = request.form.get('password')

        # 检查用户名和密码是否为空
        if not username or not password:
            if data:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            else:
                flash('用户名和密码不能为空', 'danger')
                return render_template('login.html')

        # 查询用户是否存在
        user = User.query.filter_by(username=username).first()
        if user:
            # 用户存在，验证密码
            if user.password == password:
                login_user(user)
                if data:
                    # JSON 请求返回成功信息（前端通过路由跳转，但这里返回状态码让前端处理）
                    return jsonify({'message': '登录成功', 'username': username}), 200
                else:
                    return redirect(url_for('message.index'))
            else:
                if data:
                    return jsonify({'error': '密码错误'}), 401
                else:
                    flash('密码错误', 'danger')
                    return render_template('login.html')
        else:
            # 用户不存在，自动创建新用户并登录
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            if data:
                return jsonify({'message': f'欢迎 {username}，账号已自动创建并登录', 'username': username}), 201
            else:
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
        # 优先从 JSON 获取数据
        data = request.get_json()
        if data:
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
        else:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

        if not current_user.password == old_password:
            if data:
                return jsonify({'error': '原密码错误'}), 401
            else:
                flash('原密码错误', 'danger')
        elif new_password != confirm_password:
            if data:
                return jsonify({'error': '两次输入的新密码不一致'}), 400
            else:
                flash('两次输入的新密码不一致', 'danger')
        elif len(new_password) < 4:
            if data:
                return jsonify({'error': '密码长度至少4位'}), 400
            else:
                flash('密码长度至少4位', 'danger')
        else:
            current_user.password = new_password
            db.session.commit()
            if data:
                return jsonify({'message': '密码修改成功，请重新登录'}), 200
            else:
                flash('密码修改成功，请重新登录', 'success')
                logout_user()
                return redirect(url_for('auth.login'))
    return render_template('change_password.html')

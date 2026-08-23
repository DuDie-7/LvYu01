from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
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
            username = request.form.get('username')
            password = request.form.get('password')

        if not username or not password:
            if data:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            else:
                flash('用户名和密码不能为空', 'danger')
                return render_template('login.html')

        # 查询用户
        user = User.query.filter_by(username=username).first()

        if user:
            # ============================================================
            # 双模验证：先试哈希，再试明文（兼容老用户）
            # ============================================================
            password_ok = False
            is_upgraded = False

            # 1. 尝试哈希验证
            try:
                if check_password_hash(user.password, password):
                    password_ok = True
            except (ValueError, TypeError):
                # 如果密码字段不是哈希格式（如旧明文），跳过
                pass

            # 2. 如果哈希验证失败，尝试明文匹配（兼容旧数据）
            if not password_ok and user.password == password:
                password_ok = True
                is_upgraded = True  # 标记需要升级

            if not password_ok:
                if data:
                    return jsonify({'error': '密码错误'}), 401
                else:
                    flash('密码错误', 'danger')
                    return render_template('login.html')

            # 自动升级：如果明文匹配成功，立即升级为哈希存储
            if is_upgraded:
                try:
                    user.password = generate_password_hash(password)
                    db.session.commit()
                except Exception as e:
                    # 升级失败不影响登录，只是下次验证会继续走明文路径
                    db.session.rollback()
                    pass

            # 登录成功
            login_user(user)
            if data:
                return jsonify({'message': '登录成功', 'username': username}), 200
            else:
                return redirect(url_for('message.index'))

        else:
            # 用户不存在，自动创建（新用户直接使用哈希）
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw)
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
        data = request.get_json()
        if data:
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
        else:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

        # 验证原密码（双模：先试哈希，再试明文）
        password_ok = False
        try:
            if check_password_hash(current_user.password, old_password):
                password_ok = True
        except (ValueError, TypeError):
            pass

        if not password_ok and current_user.password == old_password:
            password_ok = True

        if not password_ok:
            if data:
                return jsonify({'error': '原密码错误'}), 401
            else:
                flash('原密码错误', 'danger')
                return render_template('change_password.html')

        # 检查新密码
        if new_password != confirm_password:
            if data:
                return jsonify({'error': '两次输入的新密码不一致'}), 400
            else:
                flash('两次输入的新密码不一致', 'danger')
                return render_template('change_password.html')

        if len(new_password) < 4:
            if data:
                return jsonify({'error': '密码长度至少4位'}), 400
            else:
                flash('密码长度至少4位', 'danger')
                return render_template('change_password.html')

        # 更新为哈希密码
        current_user.password = generate_password_hash(new_password)
        db.session.commit()

        if data:
            return jsonify({'message': '密码修改成功，请重新登录'}), 200
        else:
            flash('密码修改成功，请重新登录', 'success')
            logout_user()
            return redirect(url_for('auth.login'))

    return render_template('change_password.html')

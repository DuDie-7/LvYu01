from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .models import User
from .exts import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(silent=True)
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

        user = User.query.filter_by(username=username).first()

        # ===== 如果用户存在，先检查锁定状态 =====
        if user:
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining = (user.locked_until - datetime.utcnow()).seconds // 60
                if remaining <= 0:
                    # 锁定已过期，自动解除
                    user.locked_until = None
                    user.login_fail_count = 0
                    db.session.commit()
                else:
                    msg = f'账号已被锁定，请等待 {remaining + 1} 分钟后重试'
                    if data:
                        return jsonify({'error': msg}), 401
                    else:
                        flash(msg, 'danger')
                        return render_template('login.html')

        # ===== 验证密码 =====
        password_ok = False
        is_upgraded = False

        if user:
            try:
                if check_password_hash(user.password, password):
                    password_ok = True
            except (ValueError, TypeError):
                pass

            if not password_ok and user.password == password:
                password_ok = True
                is_upgraded = True

        # ===== 处理验证结果 =====
        if not user or not password_ok:
            if user:
                # 用户名存在，密码错误 → 增加失败计数
                user.login_fail_count += 1
                if user.login_fail_count >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=5)
                    db.session.commit()
                    msg = '密码错误次数过多，账号已锁定 5 分钟'
                else:
                    db.session.commit()
                    msg = f'密码错误，剩余尝试次数 {5 - user.login_fail_count}'
            else:
                # 用户名不存在，不记录失败次数（防止用户名枚举）
                msg = '用户名或密码错误'

            if data:
                return jsonify({'error': msg}), 401
            else:
                flash(msg, 'danger')
                return render_template('login.html')

        # ===== 密码正确 =====
        # 升级哈希（如果是明文）
        if is_upgraded:
            try:
                user.password = generate_password_hash(password)
            except Exception:
                db.session.rollback()

        # 重置失败计数和锁定状态
        user.login_fail_count = 0
        user.locked_until = None
        db.session.commit()

        login_user(user)
        if data:
            return jsonify({
                'message': '登录成功',
                'username': username,
                'user_id': user.id,        # 新增：返回用户ID
                'is_admin': user.is_admin
            }), 200
        else:
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
        data = request.get_json(silent=True)
        if data:
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
        else:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

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

        current_user.password = generate_password_hash(new_password)
        db.session.commit()

        if data:
            return jsonify({'message': '密码修改成功，请重新登录'}), 200
        else:
            flash('密码修改成功，请重新登录', 'success')
            logout_user()
            return redirect(url_for('auth.login'))

    return render_template('change_password.html')

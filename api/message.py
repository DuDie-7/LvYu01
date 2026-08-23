from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import Message
from .exts import db

message_bp = Blueprint('message', __name__)


# 首页：留言列表
@message_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    pagination = Message.query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    messages = pagination.items
    
    # 如果请求头包含 Accept: application/json，说明是 Vue 前端在请求，返回 JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'messages': [{
                'id': m.id,
                'title': m.title,
                'content': m.content,
                'author_id': m.author_id,
                'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
            } for m in messages],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
    
    # 否则返回原来的网页（兼容旧版）
    return render_template('index.html', messages=messages, pagination=pagination)


# 新增留言
@message_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        # 判断是不是 JSON 请求（Vue 前端）
        data = request.get_json()
        if data:
            title = data.get('title')
            content = data.get('content')
        else:
            # 兼容旧的网页表单
            title = request.form.get('title')
            content = request.form.get('content')

        if not title or not content:
            if data:
                return jsonify({'error': '标题和内容不能为空'}), 400
            else:
                flash('标题和内容不能为空', 'danger')
                return render_template('add.html')
        
        msg = Message(title=title, content=content, author_id=current_user.id)
        db.session.add(msg)
        db.session.commit()
        
        if data:
            return jsonify({'message': '留言添加成功'}), 201
        else:
            flash('留言添加成功', 'success')
            return redirect(url_for('message.index'))
    
    return render_template('add.html')


# 编辑留言
@message_bp.route('/edit/<int:msg_id>', methods=['GET', 'POST'])
@login_required
def edit(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.author_id != current_user.id:
        data = request.get_json()
        if data:
            return jsonify({'error': '无权编辑此留言'}), 403
        else:
            flash('无权编辑此留言', 'danger')
            return redirect(url_for('message.index'))
    
    if request.method == 'POST':
        data = request.get_json()
        if data:
            msg.title = data.get('title')
            msg.content = data.get('content')
        else:
            msg.title = request.form.get('title')
            msg.content = request.form.get('content')
        db.session.commit()
        
        if data:
            return jsonify({'message': '留言修改成功'}), 200
        else:
            flash('留言修改成功', 'success')
            return redirect(url_for('message.index'))
    
    return render_template('edit.html', msg=msg)


# 删除留言
@message_bp.route('/delete/<int:msg_id>')
@login_required
def delete(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.author_id != current_user.id:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': '无权删除此留言'}), 403
        else:
            flash('无权删除此留言', 'danger')
            return redirect(url_for('message.index'))
    
    db.session.delete(msg)
    db.session.commit()
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'message': '留言已删除'}), 200
    else:
        flash('留言已删除', 'success')
        return redirect(url_for('message.index'))


# 查看留言详情
@message_bp.route('/detail/<int:msg_id>')
@login_required
def detail(msg_id):
    msg = Message.query.get_or_404(msg_id)
    return render_template('detail.html', msg=msg)

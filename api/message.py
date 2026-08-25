from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from .models import Message
from .exts import db

message_bp = Blueprint('message', __name__)


@message_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    pagination = Message.query.options(joinedload(Message.author)).order_by(
        Message.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    messages = pagination.items

    if request.headers.get('Accept') == 'application/json':
        messages_data = []
        for m in messages:
            author_name = m.author.username if m.author else '匿名'
            messages_data.append({
                'id': m.id,
                'title': m.title,
                'content': m.content,
                'author_id': m.author_id,
                'author_username': author_name,
                'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({
            'messages': messages_data,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
    return render_template('index.html', messages=messages, pagination=pagination)


@message_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data:
            title = data.get('title')
            content = data.get('content')
        else:
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


@message_bp.route('/edit/<int:msg_id>', methods=['GET', 'POST'])
@login_required
def edit(msg_id):
    msg = Message.query.get_or_404(msg_id)

    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data:
            new_title = data.get('title')
            new_content = data.get('content')
        else:
            new_title = request.form.get('title')
            new_content = request.form.get('content')

        if msg.author_id != current_user.id:
            if data:
                return jsonify({'error': '无权编辑此留言'}), 403
            else:
                flash('无权编辑此留言', 'danger')
                return redirect(url_for('message.index'))

        if not new_title or not new_content:
            if data:
                return jsonify({'error': '标题和内容不能为空'}), 400
            else:
                flash('标题和内容不能为空', 'danger')
                return render_template('edit.html', msg=msg)

        msg.title = new_title
        msg.content = new_content
        db.session.commit()
        if data:
            return jsonify({'message': '留言修改成功'}), 200
        else:
            flash('留言修改成功', 'success')
            return redirect(url_for('message.index'))

    # GET 请求
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'id': msg.id,
            'title': msg.title,
            'content': msg.content,
            'author_id': msg.author_id,
            'author_username': msg.author.username if msg.author else '匿名',
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': msg.updated_at.strftime('%Y-%m-%d %H:%M')
        }), 200
    return render_template('edit.html', msg=msg)


@message_bp.route('/delete/<int:msg_id>')
@login_required
def delete(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if not (current_user.is_admin or msg.author_id == current_user.id):
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


@message_bp.route('/detail/<int:msg_id>')
@login_required
def detail(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'id': msg.id,
            'title': msg.title,
            'content': msg.content,
            'author_id': msg.author_id,
            'author_username': msg.author.username if msg.author else '匿名',
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': msg.updated_at.strftime('%Y-%m-%d %H:%M')
        }), 200
    return render_template('detail.html', msg=msg)

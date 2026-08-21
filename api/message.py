from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Message
from .exts import db

message_bp = Blueprint('message', __name__)

# 首页：留言列表（分页）
@message_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5   # 每页5条
    pagination = Message.query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    messages = pagination.items
    return render_template('index.html', messages=messages, pagination=pagination)

# 新增留言
@message_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash('标题和内容不能为空', 'danger')
        else:
            msg = Message(title=title, content=content, author_id=current_user.id)
            db.session.add(msg)
            db.session.commit()
            flash('留言添加成功', 'success')
            return redirect(url_for('message.index'))
    return render_template('add.html')

# 编辑留言
@message_bp.route('/edit/<int:msg_id>', methods=['GET', 'POST'])
@login_required
def edit(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.author_id != current_user.id:
        flash('无权编辑此留言', 'danger')
        return redirect(url_for('message.index'))
    if request.method == 'POST':
        msg.title = request.form.get('title')
        msg.content = request.form.get('content')
        db.session.commit()
        flash('留言修改成功', 'success')
        return redirect(url_for('message.index'))
    return render_template('edit.html', msg=msg)

# 删除留言
@message_bp.route('/delete/<int:msg_id>')
@login_required
def delete(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.author_id != current_user.id:
        flash('无权删除此留言', 'danger')
    else:
        db.session.delete(msg)
        db.session.commit()
        flash('留言已删除', 'success')
    return redirect(url_for('message.index'))

# 查看留言详情
@message_bp.route('/detail/<int:msg_id>')
@login_required
def detail(msg_id):
    msg = Message.query.get_or_404(msg_id)
    return render_template('detail.html', msg=msg)
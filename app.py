from api import create_app
from api.exts import db
from api.models import User, Message   # 导入模型以确保它们被注册

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # 这会根据模型定义创建所有缺失的表
        print("数据库表创建成功！")
        # 可选：插入一个测试用户（如果 user 表为空）
        if User.query.count() == 0:
            test_user = User(username='admin', password='123456')
            db.session.add(test_user)
            db.session.commit()
            print("测试用户 admin 已创建")
    app.run(debug=True, port=5000)
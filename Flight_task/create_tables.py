
from Flight import create_app, db
# 暂时不在这里导入模型

app = create_app() # 调用应用工厂创建应用

with app.app_context():
    # 在应用上下文内部，从你的包中的 models 模块导入模型
    from Flight.models import User, Flight
    db.create_all()
    print("数据库表创建成功！")
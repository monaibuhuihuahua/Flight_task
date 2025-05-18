from . import db
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey # 确保导入 ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(512), nullable=False)
    role = Column(String(20), default='user')
    def __repr__(self):
        return f'<User {self.username}>'

# ... (Flight 模型定义保持不变)
class Flight(db.Model):
    __tablename__ = 'flights'
    id = Column(Integer, primary_key=True)
    flight_number = Column(String(20), unique=True, nullable=False)
    aircraft_number = Column(String(20), nullable=False)
    origin = Column(String(50), nullable=False)
    destination = Column(String(50), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # 添加与 Order 模型的关系
    orders = relationship('Order', backref='flight', lazy=True)


    def __repr__(self):
        return f'<Flight {self.flight_number} from {self.origin} to {self.destination}>'

# 定义 Customer 模型 (客户信息)
class Customer(db.Model):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    id_card_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 添加与 User 模型的关系 (可选，但有助于反向查找)
    user = relationship("User", backref="customer", uselist=False) # uselist=False 表示一个用户最多关联一个客户

    # 添加与 Order 模型的关系
    orders = relationship('Order', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name} ({self.id_card_number})>'

# 定义 Order 模型 (订单信息)
class Order(db.Model):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)

    # 外键关联到 flights 表的 id 列
    flight_id = Column(Integer, ForeignKey('flights.id'), nullable=False)

    # 外键关联到 customers 表的 id 列
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)

    booking_time = Column(DateTime, default=datetime.utcnow, nullable=False) # 订票时间，默认为当前 UTC 时间
    seat_number = Column(String(10), nullable=True) # 座位号 (可选字段，暂时不实现复杂的座位分配逻辑，但保留字段)

    # backref='flight' 和 backref='customer' 已经在 Flight 和 Customer 模型中定义了

    def __repr__(self):
        return f'<Order {self.id} for Flight {self.flight_id} by Customer {self.customer_id}>'
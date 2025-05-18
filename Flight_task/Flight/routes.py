from flask import render_template, request, redirect, url_for, flash, session, Blueprint
from . import db # 从当前包导入 db 对象
from .models import User, Flight, Customer, Order # 从当前包导入模型
from werkzeug.security import generate_password_hash, check_password_hash # 用于密码哈希
from datetime import datetime
from functools import wraps
# 创建一个蓝图实例
main_bp = Blueprint('main', __name__)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        # 如果用户未登录
        if user_id is None:
            flash('请先登录才能访问此页面。', 'warning')
            return redirect(url_for('main.login'))

        # 如果用户已登录，获取用户对象
        user = db.session.query(User).get(user_id)

        # 如果用户不存在或用户不是管理员
        if user is None or user.role != 'admin':
            flash('您没有权限访问此页面。', 'danger')
            # 重定向到主页或其他合适的页面
            return redirect(url_for('main.index'))

        # 如果是管理员，继续执行被装饰的函数
        return f(*args, **kwargs)
    return decorated_function

# 需要登录才能访问的装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录才能访问此页面。', 'warning')
            # 重定向到登录页
            # 可以添加 next 参数以便登录后跳回原页面，这里简单重定向
            return redirect(url_for('main.login'))
        # 如果已登录，继续执行被装饰的函数
        return f(*args, **kwargs)
    return decorated_function

# 主页路由
@main_bp.route('/')
def index():
    user = None # 默认用户为 None
    is_admin = False # 默认不是管理员

    user_id = session.get('user_id')
    if user_id:
        # 如果用户已登录，获取用户对象
        user = db.session.query(User).get(user_id)
        # 如果用户存在且角色为管理员
        if user and user.role == 'admin':
            is_admin = True

    # 渲染主页模板，并将 user 和 is_admin 传递给模板
    return render_template('index.html', user=user, is_admin=is_admin)


# 用户注册路由
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('用户名和密码不能为空！', 'danger')
            # 注册失败时回填用户名
            return render_template('register.html', username=username)

        # 检查用户名是否已存在
        existing_user = db.session.query(User).filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在！', 'warning')
             # 注册失败时回填用户名
            return render_template('register.html', username=username)

        # 对密码进行哈希处理
        hashed_password = generate_password_hash(password)

        # 创建新用户
        new_user = User(username=username, password=hashed_password, role='user') # 默认角色为 'user'

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录！', 'success')
            # 注册成功后重定向到登录页面
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback() # 出现错误时回滚
            flash('注册失败，请稍后重试。', 'danger')
            print(f"注册失败错误: {e}") # 打印错误信息方便调试
            # 注册失败时回填用户名
            return render_template('register.html', username=username)
    return render_template('register.html', username=request.form.get('username', ''))


# 用户登录路由
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
             flash('用户名和密码不能为空！', 'danger')
             return render_template('login.html', username=username)


        # 查找用户
        user = db.session.query(User).filter_by(username=username).first()

        # 检查用户是否存在且密码正确
        if user and check_password_hash(user.password, password):
            # 登录成功，将用户ID存入session
            session['user_id'] = user.id
            flash(f'欢迎回来，{user.username}！', 'success')
            # 登录成功后重定向到主页
            return redirect(url_for('main.index'))
        else:
            flash('用户名或密码错误！', 'danger')
            # 登录失败时回填用户名
            return render_template('login.html', username=username)
    return render_template('login.html', username=request.form.get('username', ''))


# 用户退出登录路由
@main_bp.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('您已退出登录。', 'info')
    return redirect(url_for('main.index'))

# 管理员添加航班路由
@main_bp.route('/admin/add_flight', methods=['GET', 'POST'])
@admin_required
def add_flight():
    if request.method == 'POST':
        # 从表单获取数据
        flight_number = request.form.get('flight_number')
        aircraft_number = request.form.get('aircraft_number')
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        departure_time_str = request.form.get('departure_time')
        arrival_time_str = request.form.get('arrival_time')
        total_seats_str = request.form.get('total_seats')
        price_str = request.form.get('price')

        # 简单验证数据 (非空)
        if not all([flight_number, aircraft_number, origin, destination,
                    departure_time_str, arrival_time_str, total_seats_str, price_str]):
            flash('所有字段都不能为空！', 'danger')
             # 添加失败时回填数据
            return render_template('add_flight.html',
                                   flight_number=flight_number, aircraft_number=aircraft_number,
                                   origin=origin, destination=destination,
                                   departure_time=departure_time_str, arrival_time=arrival_time_str,
                                   total_seats=total_seats_str, price=price_str)

        try:
            # 类型转换和更详细的验证
            departure_time = datetime.fromisoformat(departure_time_str)
            arrival_time = datetime.fromisoformat(arrival_time_str)
            total_seats = int(total_seats_str)
            price = float(price_str)

             # 检查总座位数是否有效
            if total_seats < 0:
                 flash('总座位数必须为非负数！', 'danger')
                 # 添加失败时回填数据
                 return render_template('add_flight.html',
                                   flight_number=flight_number, aircraft_number=aircraft_number,
                                   origin=origin, destination=destination,
                                   departure_time=departure_time_str, arrival_time=arrival_time_str,
                                   total_seats=total_seats_str, price=price_str)

            # 检查起飞时间是否早于到达时间
            if departure_time >= arrival_time:
                flash('起飞时间必须早于到达时间！', 'danger')
                # 添加失败时回填数据
                return render_template('add_flight.html',
                                   flight_number=flight_number, aircraft_number=aircraft_number,
                                   origin=origin, destination=destination,
                                   departure_time=departure_time_str, arrival_time=arrival_time_str,
                                   total_seats=total_seats_str, price=price_str)


            # 检查航班号是否已存在
            existing_flight = db.session.query(Flight).filter_by(flight_number=flight_number).first()
            if existing_flight:
                flash('航班号已存在！', 'warning')
                 # 添加失败时回填数据
                return render_template('add_flight.html',
                                   flight_number=flight_number, aircraft_number=aircraft_number,
                                   origin=origin, destination=destination,
                                   departure_time=departure_time_str, arrival_time=arrival_time_str,
                                   total_seats=total_seats_str, price=price_str)

            # 创建新的 Flight 对象
            new_flight = Flight(
                flight_number=flight_number,
                aircraft_number=aircraft_number,
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                arrival_time=arrival_time,
                total_seats=total_seats,
                available_seats=total_seats,
                price=price
            )

            # 添加到数据库会话并提交
            db.session.add(new_flight)
            db.session.commit()

            flash('航班添加成功！', 'success')

            return redirect(url_for('main.list_flights'))

        except ValueError as e:
            flash(f'输入数据格式错误：{e}', 'danger')
            db.session.rollback()
             # 添加失败时回填数据
            return render_template('add_flight.html',
                                   flight_number=flight_number, aircraft_number=aircraft_number,
                                   origin=origin, destination=destination,
                                   departure_time=departure_time_str, arrival_time=arrival_time_str,
                                   total_seats=total_seats_str, price=price_str)
        except Exception as e:
            flash('航班添加失败，请稍后重试。', 'danger')
            db.session.rollback()
            print(f"添加航班失败错误: {e}") # 打印错误信息方便调试
             # 添加失败时回填数据
            return render_template('add_flight.html',
                                   flight_number=flight_number, aircraft_number=aircraft_number,
                                   origin=origin, destination=destination,
                                   departure_time=departure_time_str, arrival_time=arrival_time_str,
                                   total_seats=total_seats_str, price=price_str)
    return render_template('add_flight.html',
                           flight_number=request.form.get('flight_number', ''),
                           aircraft_number=request.form.get('aircraft_number', ''),
                           origin=request.form.get('origin', ''),
                           destination=request.form.get('destination', ''),
                           departure_time=request.form.get('departure_time', ''),
                           arrival_time=request.form.get('arrival_time', ''),
                           total_seats=request.form.get('total_seats', ''),
                           price=request.form.get('price', ''))


# 航班查询和显示路由 (所有用户可见)
@main_bp.route('/flights', methods=['GET'])
def list_flights():
    # 获取搜索参数
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date_str = request.args.get('date')
    # *** 添加获取航班号参数 ***
    flight_number = request.args.get('flight_number') # 获取航班号参数

    # 构建查询
    query = db.session.query(Flight)
    if flight_number:
        query = query.filter(Flight.flight_number.ilike(f'%{flight_number}%'))


    if origin:
        query = query.filter(Flight.origin.ilike(f'%{origin}%'))
    if destination:
        query = query.filter(Flight.destination.ilike(f'%{destination}%'))
    if date_str:
        try:
            search_date = datetime.strptime(date_str, '%Y-%m-%d')
            # 注意：这里只按日期匹配起飞时间
            query = query.filter(db.func.date(Flight.departure_time) == search_date.date())
        except ValueError:
            flash('日期格式无效，请使用YYYY-MM-DD格式。', 'danger')
            pass # 错误时继续查询，但不应用无效日期过滤


    flights = query.order_by(Flight.departure_time).all()

    is_admin = False # 默认不是管理员
    user_id = session.get('user_id')
    if user_id:
        user = db.session.query(User).get(user_id)
        if user and user.role == 'admin':
            is_admin = True

    # 渲染模板并传递航班数据、搜索参数和管理员状态
    return render_template(
        'flights.html',
        flights=flights,
        origin=origin,
        destination=destination,
        date=date_str, # 将日期字符串传回
        flight_number=flight_number, # 将航班号参数传回
        is_admin=is_admin
    )

# 管理员修改航班路由 (需要管理员权限)
@main_bp.route('/admin/edit_flight/<int:flight_id>', methods=['GET', 'POST'])
@admin_required # 应用管理员权限检查装饰器
def edit_flight(flight_id):
    flight = db.session.query(Flight).get_or_404(flight_id)

    if request.method == 'POST':
        # 从表单获取更新后的数据
        flight_number = request.form.get('flight_number')
        aircraft_number = request.form.get('aircraft_number')
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        departure_time_str = request.form.get('departure_time')
        arrival_time_str = request.form.get('arrival_time')
        total_seats_str = request.form.get('total_seats')
        price_str = request.form.get('price')

        # 简单验证数据 (非空)
        if not all([flight_number, aircraft_number, origin, destination,
                    departure_time_str, arrival_time_str, total_seats_str, price_str]):
             flash('所有字段都不能为空！', 'danger')
             # 渲染编辑页面并回填数据
             return render_template('edit_flight.html', flight=flight) # 注意这里传递 flight 对象本身用于回填

        try:
            # 类型转换和更详细的验证
            departure_time = datetime.fromisoformat(departure_time_str)
            arrival_time = datetime.fromisoformat(arrival_time_str)
            total_seats = int(total_seats_str)
            price = float(price_str)

             # 检查总座位数是否有效
            if total_seats < 0:
                 flash('总座位数必须为非负数！', 'danger')
                 return render_template('edit_flight.html', flight=flight)


            # 检查起飞时间是否早于到达时间
            if departure_time >= arrival_time:
                flash('起飞时间必须早于到达时间！', 'danger')
                return render_template('edit_flight.html', flight=flight)


            # 处理修改航班号时的唯一性检查
            # 如果修改了航班号，需要检查新的航班号是否已存在于其他航班中
            if flight.flight_number != flight_number:
                existing_flight = db.session.query(Flight).filter_by(flight_number=flight_number).first()
                if existing_flight:
                     flash('修改后的航班号已存在！', 'danger')
                     return render_template('edit_flight.html', flight=flight)
            booked_seats = flight.total_seats - flight.available_seats
            new_available_seats = total_seats - booked_seats

            # 检查新的总座位数是否小于已预订数量
            if new_available_seats < 0:
                flash(f'新的总座位数 ({total_seats}) 小于已预订座位数 ({booked_seats})！', 'danger')
                return render_template('edit_flight.html', flight=flight)


            flight.flight_number = flight_number
            flight.aircraft_number = aircraft_number
            flight.origin = origin
            flight.destination = destination
            flight.departure_time = departure_time
            flight.arrival_time = arrival_time
            flight.total_seats = total_seats
            flight.available_seats = new_available_seats # 更新可用座位数
            flight.price = price

            # 提交修改到数据库
            db.session.commit()
            flash('航班信息更新成功！', 'success')
            # 更新成功后重定向到航班列表页面
            return redirect(url_for('main.list_flights'))

        except ValueError as e:
            flash(f'输入数据格式错误：{e}', 'danger')
            db.session.rollback()
            return render_template('edit_flight.html', flight=flight) # 渲染编辑页面并回填数据 (传递 flight 对象本身)
        except Exception as e:
            flash('航班信息更新失败，请稍后重试。', 'danger')
            db.session.rollback()
            print(f"更新航班失败错误: {e}") # 打印错误信息方便调试
            return render_template('edit_flight.html', flight=flight) # 渲染编辑页面并回填数据 (传递 flight 对象本身)
    flight.departure_time_str = flight.departure_time.strftime('%Y-%m-%dT%H:%M')
    flight.arrival_time_str = flight.arrival_time.strftime('%Y-%m-%dT%H:%M')

    return render_template('edit_flight.html', flight=flight)
@main_bp.route('/admin/delete_flight/<int:flight_id>', methods=['POST'])
@admin_required # 应用管理员权限检查装饰器
def delete_flight(flight_id):
    # 根据 flight_id 获取航班对象
    flight = db.session.query(Flight).get_or_404(flight_id) # 找不到航班则返回 404

    try:
        db.session.delete(flight) # 从数据库会话中删除航班对象
        db.session.commit() # 提交删除操作

        flash('航班删除成功！', 'success')

    except Exception as e:
        db.session.rollback()
        if "IntegrityError" in str(e): # 检查是否是完整性错误，通常是外键约束
             flash('航班删除失败，该航班有关联的订单，请先处理订单。', 'danger')
        else:
             flash('航班删除失败，请稍后重试。', 'danger')

        print(f"删除航班失败错误: {e}") # 打印错误信息方便调试


    # 删除成功或失败后，重定向回航班列表页面
    return redirect(url_for('main.list_flights'))


@main_bp.route('/book/<int:flight_id>', methods=['GET', 'POST'])
@login_required # 需要登录才能预订
def book_flight(flight_id):
    flight = db.session.query(Flight).get_or_404(flight_id)
    if request.method == 'POST':
        # 从表单获取客户姓名和身份证号
        customer_name = request.form.get('customer_name')
        id_card_number = request.form.get('id_card_number')

        # 验证客户信息是否完整
        if not customer_name or not id_card_number:
            flash('姓名和身份证号不能为空！', 'danger')
            # 返回预订页面，并回填用户输入的姓名和身份证号
            return render_template('book_flight.html', flight=flight, customer_name=customer_name, id_card_number=id_card_number)

        # 检查航班是否有可用座位
        if flight.available_seats <= 0:
            flash(f'航班 {flight.flight_number} 已售罄。', 'danger')
            return redirect(url_for('main.list_flights'))

        # 尝试执行数据库操作
        try:
            # 根据身份证号查找现有客户，或创建新客户
            customer = db.session.query(Customer).filter_by(id_card_number=id_card_number).first()
            if not customer:
                # 如果客户不存在，创建新的客户记录
                new_customer = Customer(name=customer_name, id_card_number=id_card_number)
                db.session.add(new_customer)
                customer = new_customer # 使用新创建的客户对象
            user_id = session.get('user_id')
            if user_id:
                 logged_in_user = db.session.query(User).get(user_id)
                 # 只有在客户记录还没有关联用户时才进行关联
                 if customer.user_id is None:
                      customer.user_id = logged_in_user.id
            # 创建新的订单记录
            new_order = Order(
                flight_id=flight.id, # 关联到当前航班
                customer_id=customer.id, # 关联到找到或创建的客户
                seat_number=f"Seat {flight.total_seats - flight.available_seats + 1}"
            )
            db.session.add(new_order)
            flight.available_seats -= 1
            db.session.commit()
            flash(f'航班 {flight.flight_number} 预订成功！您的座位号是 {new_order.seat_number}。', 'success')
            return redirect(url_for('main.list_flights'))
        except Exception as e:
            # 如果在数据库操作过程中发生任何错误，回滚所有未提交的更改
            db.session.rollback()
            flash('预订失败，请稍后重试。', 'danger')
            print(f"预订失败错误: {e}")
            return render_template('book_flight.html', flight=flight, customer_name=customer_name, id_card_number=id_card_number)
    return render_template(
        'book_flight.html',
        flight=flight,
        customer_name=request.form.get('customer_name', ''),
        id_card_number=request.form.get('id_card_number', '')
    )
@main_bp.route('/my_orders')
@login_required # 确保用户登录才能访问此页面
def my_orders():
    user_id = session.get('user_id')
    # 获取当前登录用户对象
    logged_in_user = db.session.query(User).get(user_id)
    # 初始化订单列表
    orders = []
    # 根据当前登录用户的 ID 查找关联的客户记录
    customers = db.session.query(Customer).filter_by(user_id=user_id).all()
    # 遍历这些客户，收集他们的所有订单
    for customer in customers:
        orders.extend(customer.orders)
    return render_template('my_orders.html', orders=orders)
# --- 退票路由 ---
@main_bp.route('/refund/<int:order_id>', methods=['POST'])
@login_required # 需要登录才能退票
def refund_ticket(order_id):
    user_id = session.get('user_id')
    logged_in_user = db.session.query(User).get(user_id)
    order = db.session.query(Order).get_or_404(order_id)
    is_admin = (logged_in_user.role == 'admin')
    # 查找与当前登录用户关联的客户记录
    is_order_owner = False
    if order.customer and order.customer.user_id == user_id:
        is_order_owner = True
    if not is_admin and not is_order_owner:
        flash('您没有权限退订此机票。', 'danger')
        return redirect(url_for('main.my_orders'))

    try:
        # 获取关联的航班，以便更新可用座位数
        flight = db.session.query(Flight).get_or_404(order.flight_id)
        db.session.delete(order) # 删除订单记录
        flight.available_seats += 1
        db.session.commit() # 提交删除和更新
        flash(f'订单 {order.id} 退票成功！航班 {flight.flight_number} 可用座位数已恢复。', 'success')
    except Exception as e:
        db.session.rollback() # 如果发生错误，回滚
        flash(f'退票失败，请稍后重试。', 'danger')
        print(f"退票失败错误: {e}")
    return redirect(url_for('main.my_orders'))
@main_bp.route('/admin/orders', methods=['GET']) # 只接受 GET 请求用于显示和搜索
@admin_required # 应用管理员权限检查装饰器
def admin_list_orders():
    # 获取搜索参数
    search_flight_number = request.args.get('search_flight_number')
    search_customer_name = request.args.get('search_customer_name')
    search_id_card = request.args.get('search_id_card')
    query = db.session.query(Order)
    filters = [] # 使用列表存储所有的过滤条件
    if search_flight_number:
        query = query.join(Order.flight)
        filters.append(Flight.flight_number.ilike(f'%{search_flight_number}%'))
    customer_filter_needed = False
    if search_customer_name:
        customer_filter_needed = True
        filters.append(Customer.name.ilike(f'%{search_customer_name}%'))

    if search_id_card:
        customer_filter_needed = True
        filters.append(Customer.id_card_number.ilike(f'%{search_id_card}%'))

    if customer_filter_needed:
        query = query.join(Order.customer)

    # 应用所有收集的过滤条件
    if filters:
        query = query.filter(*filters)
    orders = query.order_by(Order.booking_time.desc()).all()

    return render_template(
        'admin_orders.html',
        orders=orders,
        search_flight_number=search_flight_number,
        search_customer_name=search_customer_name,
        search_id_card=search_id_card
    )
import string
import time
from urllib.request import urlopen
from flask import Flask, json, render_template, request, redirect, session, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import httpx
import requests
from models import Asset, Bardasht, Shaba, db, User, Investment ,init_extensions
import jdatetime
from datetime import datetime
import pymysql
from sqlalchemy import select
from waitress import serve
import threading
from flask_caching import Cache

pymysql.install_as_MySQLdb()
app = Flask(__name__)


app.config['SECRET_KEY'] = 'yorsyb57$%W&*%^bvere'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Z5Q8aQg1yYytIKJb@services.irn13.chabokan.net:32061/loving_hugle'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_extensions(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from routes.message import message_blueprint
from routes.nazar import nazar

app.register_blueprint(nazar)
app.register_blueprint(message_blueprint)

@login_manager.user_loader
def load_user(user_id):
    # استفاده از روش جدید SQLAlchemy 2.0
    return db.session.get(User, int(user_id))

def get_shamsi_datetime():
    now = jdatetime.datetime.now()
    return now.strftime('%Y/%m/%d'), now.strftime('%H:%M:%S')

cache = Cache(app)

def fetch_api_data():
    """دریافت داده از API و ذخیره در کش"""
    
      #  response = requests.get(
       #     'http://api.navasan.tech/latest/?api_key=premts4574hRpl4xfqgf2WxfGzoU5wSc&item=sekkeh',
        #    timeout=120
        #)
        #data = response.json()

    url = 'http://api.navasan.tech/latest/?api_key=premts4574hRpl4xfqgf2WxfGzoU5wSc&item=sekkeh'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    
 
    response = requests.get(
            url,
            headers=headers,
            timeout=60,
            verify=False  # اگر SSL مشکل داشت
        )
        
        

    print(response, 'API Data Fetched$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    return response
   

@app.route('/')
def index():
    # تلاش برای دریافت داده از کش
    data = cache.get('sekkeh_price')
    
    # اگر داده در کش نبود، دریافت کن (با timeout)
    if data is None:
        data = fetch_api_data()  # ✅ دریافت همزمان با timeout
    
    # حالا داده رو داری، می‌تونی استفاده کنی
 
    
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

# Routes
""" @app.route('/')
def index():
    response = requests.get('http://api.navasan.tech/latest/?api_key=premts4574hRpl4xfqgf2WxfGzoU5wSc&item=sekkeh')
    data = response.json()
    print(data,'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH')
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login')) """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'] 
        password = request.form['password']
        user = db.session.scalar(select(User).where(User.username == username))
        
        if user and user.password==password and user.is_delete != 'true':
            login_user(user)
            session['user_id'] = user.id
            flash('ورود موفقیت‌آمیز بود', 'success')
            return redirect(url_for('index'))
        else:
            flash('نام کاربری یا رمز عبور نادرست', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        full_name = request.form['full_name']
        is_delete = 'false'
        user = User(username=username,password=password,phone=phone,full_name=full_name,is_delete=is_delete)
        
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# پنل مدیریت
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    
    users = db.session.scalars(select(User).where(User.is_admin == False,User.is_delete == 'false')).all()
    nd = db.session.scalars(select(Asset)).all()
    return render_template('admin/dashboard.html', users=users, nd=nd)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    
   # users = db.session.scalars(select(User)).all()
    users = User.query.filter_by(is_delete='false').all()
    return render_template('admin/users.html', users=users)

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error') 
        return redirect(url_for('user_dashboard'))
    
    user = User.query.filter_by(id=user_id).first()
    user.is_delete='true'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_management(user_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    
    user = db.session.get(User, user_id)
    if not user:
        flash('کاربر یافت نشد', 'error')
        return redirect(url_for('admin_users'))
    
    assets = db.session.scalars(select(Asset).where(Asset.is_active == True)).all()
    
    if request.method == 'POST':
        print('1111')
     
        new_asset_type = request.form['asset_type']
        
        ass = Asset.query.filter_by(asset_type=new_asset_type).first()
        print('2222')
        if not ass:
            print('3333')
            asset = Asset(
                asset_type=new_asset_type,
            )
            db.session.add(asset)
            db.session.commit()
            flash('دارایی جدید با موفقیت اضافه شد', 'success')
                
        # اضافه کردن سرمایه جدید برای کاربر
        asset_type = request.form['asset_type']
        amount = float(request.form['amount'])
        transaction_type = request.form['transaction_type']
        notes = request.form.get('notes', '')
        
        shamsi_date, shamsi_time = get_shamsi_datetime()
        
        unit = Asset.query.filter_by(asset_type=asset_type).first()
        price_for_unit = unit.current_price()
       
        investment = Investment(
            user_id=user_id,
            asset_type=asset_type,
            amount=amount,
            transaction_type=transaction_type,
            shamsi_date=shamsi_date,
            shamsi_time=shamsi_time,
            notes=notes,
            price_per_unit=price_for_unit*unit.zarib
        )
      
        db.session.add(investment)
        db.session.commit()
        flash('سرمایه با موفقیت اضافه شد', 'success')
        return redirect(url_for('user_management', user_id=user_id))
    
    investments = db.session.scalars(
        select(Investment).where(Investment.user_id == user_id)
    ).all()
    
    return render_template('admin/user_detail.html', user=user, investments=investments, assets=assets)

# پنل کاربر
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('user/dashboard.html')

# فیلتر سفارشی برای نمایش زیبای اعداد
@app.template_filter('format_float')
def format_float(value):
    """
    نمایش زیبای اعداد float - اگر عدد صحیح است بدون اعشار نمایش دهد
    """
    if value is None:
        return "0"
    
    try:
        float_value = float(value)
        # اگر عدد صحیح است
        if float_value.is_integer():
            return str(int(float_value))
        else:
            # نمایش حداکثر ۳ رقم اعشار
            return "{:.3f}".format(float_value).rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)
    
@app.route('/user/portfolio')
@login_required
def user_portfolio():
    # محاسبه مجموع هر نوع دارایی
    investments = db.session.scalars(
        select(Investment).where(Investment.user_id == current_user.id)
    ).all()
     
    portfolio_data = {}  # تغییر نام به portfolio_data برای شفافیت بیشتر
    
    for inv in investments:
        if inv.asset_type not in portfolio_data:
            portfolio_data[inv.asset_type] = {
                'amount': 0,
                'current_value': 0,  
                'unit': '',
                'kh': 0,
                'fr':0,
                'khk':0
            }

        if inv.price_per_unit == None:
            inv.price_per_unit=1
        if inv.transaction_type == 'buy':
            portfolio_data[inv.asset_type]['amount'] += inv.amount
            portfolio_data[inv.asset_type]['kh'] += (inv.amount * inv.price_per_unit) # خرید کل به تومان
        else:  # sell
            portfolio_data[inv.asset_type]['amount'] -= inv.amount
            portfolio_data[inv.asset_type]['fr'] += (inv.amount * inv.price_per_unit) # فروش کل به تومان

        khk=portfolio_data[inv.asset_type]['kh']-portfolio_data[inv.asset_type]['fr'] # خرید کل به تومان در زمان خودش
        print(khk,'oooooooooooooooooooo')
        unit = Asset.query.filter_by(asset_type=inv.asset_type).first()
        if unit:
            price_for_unit = unit.current_price()
            if price_for_unit == None:
                return redirect(url_for('error'))
            
            print(price_for_unit,'66666666666666')
            zarib = unit.zarib if unit.zarib else 1
            current_value = price_for_unit * portfolio_data[inv.asset_type]['amount'] * zarib
            portfolio_data[inv.asset_type]['current_value'] = current_value
            portfolio_data[inv.asset_type]['khk'] = current_value - khk # سود یا زیان مقدار   # قیمت الان منهای قیمت در زمان خودش
            portfolio_data[inv.asset_type]['unit'] = unit.vahed if unit.vahed else ''

    return render_template('user/portfolio.html', portfolio_data=portfolio_data)


@app.route('/user/history/<asset_type>')
@login_required
def investment_history(asset_type):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    investments = db.session.scalars(
        select(Investment).where(
            Investment.user_id == current_user.id,
            Investment.asset_type == asset_type
        ).order_by(Investment.created_at.desc())
    ).all()
    
    return render_template('user/history.html', 
                         investments=investments, 
                         asset_type=asset_type)

# API برای دریافت داده‌ها
@app.route('/api/user/investments')
@login_required
def api_user_investments():
    investments = db.session.scalars(
        select(Investment).where(Investment.user_id == current_user.id)
    ).all()
    
    data = []
    for inv in investments:
        data.append({
            'id': inv.id,
            'asset_type': inv.asset_type,
            'amount': inv.amount,
            'price_per_unit': inv.price_per_unit,
            'transaction_type': inv.transaction_type,
            'shamsi_date': inv.shamsi_date,
            'shamsi_time': inv.shamsi_time,
            'notes': inv.notes,
            'created_at': inv.created_at.isoformat() if inv.created_at else None
        })
    
    return jsonify(data)

# اضافه کردن jdatetime به context تمام templateها
@app.context_processor
def utility_processor():
    def get_shamsi_date():
        return jdatetime.datetime.now().strftime('%Y/%m/%d')
    
    def get_shamsi_datetime():
        now = jdatetime.datetime.now()
        return now.strftime('%Y/%m/%d'), now.strftime('%H:%M:%S')
    
    return dict(
        jdatetime=jdatetime,
        get_shamsi_date=get_shamsi_date,
        get_shamsi_datetime=get_shamsi_datetime
    )

@app.route('/vira/<int:user_id>', methods=['GET', 'POST'])
@login_required  # اگر نیاز به لاگین دارد
def vira(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # پردازش فرم ویرایش
        user.full_name = request.form['full_name']
        user.username = request.form['username']
        user.address = request.form['address']
        user.phone = request.form['phone']
        
        # اگر پسورد جدید وارد شده
        new_password = request.form.get('password')
        if new_password:
            user.password = new_password
        
        try:
            db.session.commit()
            flash('اطلاعات کاربر با موفقیت ویرایش شد', 'success')
            return redirect(url_for('users_list'))  # یا صفحه مورد نظر
        except Exception as e:
            db.session.rollback()
            flash('خطا در ویرایش اطلاعات', 'error')
    
    return render_template('vira.html', user=user)


from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_

# ==================== #
# مدیریت کارت و شبا
# ==================== #

@app.route('/error', methods=['GET'])
def error():
    return render_template('error_page.html')

@app.route('/user/shaba', methods=['GET'])
@login_required
def user_shaba():
    """صفحه مدیریت کارت‌های کاربر"""
    shabas = Shaba.query.filter_by(user_id=current_user.id).all()
    return render_template('user_shaba.html', shabas=shabas)

@app.route('/user/shaba/add', methods=['POST'])
@login_required
def add_shaba():
    """افزودن کارت جدید"""
    try:
        shaba_number = request.form.get('shaba')
        card_number = request.form.get('card_number')
        tozihat = request.form.get('tozihat', '')

        # اعتبارسنجی
        if not shaba_number and not card_number:
            flash('حداقل یکی از فیلدهای شبا یا شماره کارت باید پر شود', 'error')
            return redirect(url_for('user_shaba'))

        new_shaba = Shaba(
            user_id=current_user.id,
            shaba=shaba_number,
            card_number=card_number,
            tozihat=tozihat
        )
        
        db.session.add(new_shaba)
        db.session.commit()
        flash('کارت با موفقیت اضافه شد', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('خطا در ثبت کارت', 'error')
    
    return redirect(url_for('user_shaba'))

@app.route('/user/shaba/delete/<int:shaba_id>', methods=['POST'])
@login_required
def delete_shaba(shaba_id):
    """حذف کارت"""
    shaba = Shaba.query.filter_by(id=shaba_id, user_id=current_user.id).first()
    if shaba:
        db.session.delete(shaba)
        db.session.commit()
        flash('کارت با موفقیت حذف شد', 'success')
    else:
        flash('کارت پیدا نشد', 'error')
    
    return redirect(url_for('user_shaba'))

# ==================== #
# درخواست‌های برداشت
# ==================== #

@app.route('/user/bardasht', methods=['GET'])
@login_required
def user_bardasht():
    """صفحه درخواست‌های برداشت کاربر"""
    # بررسی موجودی کاربر
    investments = Investment.query.filter_by(user_id=current_user.id).all()
    
    # محاسبه موجودی هر دارایی
    portfolio = {}
    for inv in investments:
        if inv.asset_type not in portfolio:
            portfolio[inv.asset_type] = 0
        
        if inv.transaction_type == 'buy':
            portfolio[inv.asset_type] += inv.amount
        else:  # sell
            portfolio[inv.asset_type] -= inv.amount
    
    # حذف دارایی‌های با موجودی صفر یا منفی
    portfolio = {k: v for k, v in portfolio.items() if v > 0}
    
    bardashts = Bardasht.query.filter_by(user_id=current_user.id).order_by(Bardasht.created_at.desc()).all()
    shabas = Shaba.query.filter_by(user_id=current_user.id).all()
    
    return render_template('user_bardasht.html', 
                         portfolio=portfolio, 
                         bardashts=bardashts, 
                         shabas=shabas)

@app.route('/user/bardasht/request', methods=['POST'])
@login_required
def request_bardasht():
    """ثبت درخواست برداشت جدید"""
    try:
        asset_type = request.form.get('asset_type')
        amount = float(request.form.get('amount'))
        shaba_id = request.form.get('shaba_id')
        tozihat = request.form.get('tozihat', '')
        
        # بررسی وجود کارت
        shaba = Shaba.query.filter_by(id=shaba_id, user_id=current_user.id).first()
        if not shaba:
            flash('کارت انتخاب شده معتبر نیست', 'error')
            return redirect(url_for('user_bardasht'))
        
        # بررسی موجودی
        investments = Investment.query.filter_by(user_id=current_user.id, asset_type=asset_type).all()
        total_buy = sum(inv.amount for inv in investments if inv.transaction_type == 'buy')
        total_sell = sum(inv.amount for inv in investments if inv.transaction_type == 'sell')
        available = total_buy - total_sell
        
        # بررسی درخواست‌های pending
        pending_bardashts = Bardasht.query.filter_by(
            user_id=current_user.id, 
            asset_type=asset_type,
            position='در انتظار بررسی'
        ).all()
        pending_amount = sum(b.amount for b in pending_bardashts)
        
        if amount > (available - pending_amount):
            flash('موجودی کافی نیست', 'error')
            return redirect(url_for('user_bardasht'))
        
        # ثبت درخواست
        new_bardasht = Bardasht(
            user_id=current_user.id,
            shaba=shaba.shaba,
            card_number=shaba.card_number,
            asset_type=asset_type,
            amount=amount,
            tozihat=tozihat
        )
        
        db.session.add(new_bardasht)
        db.session.commit()
        flash('درخواست برداشت با موفقیت ثبت شد', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('خطا در ثبت درخواست', 'error')
    
    return redirect(url_for('user_bardasht'))

# ==================== #
# مدیریت ادمین - برداشت‌ها
# ==================== #

@app.route('/admin/bardasht')
@login_required
def admin_bardasht():
    """صفحه مدیریت درخواست‌های برداشت برای ادمین"""
    if not current_user.is_admin:
        flash('دسترسی غیر مجاز', 'error')
        return redirect(url_for('index'))
    
    position_filter = request.args.get('position', 'all')
    
    query = Bardasht.query.join(User).order_by(Bardasht.created_at.desc())
    
    if position_filter != 'all': 
        query = query.filter(Bardasht.position == position_filter)
    
    bardashts = query.all()
    for bardasht in bardashts:
        user=User.query.filter_by(id=bardasht.user_id).first()
        bardasht.name=user.full_name
    return render_template('admin_bardasht.html', bardashts=bardashts)

@app.route('/admin/update_bardasht/<int:bardasht_id>', methods=['POST','GET'])
@login_required
def update_bardasht(bardasht_id):
    
    """بروزرسانی وضعیت درخواست برداشت توسط ادمین"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'دسترسی غیر مجاز'})


    if request.method == 'GET':
        print('uuuuuu')
        bardasht = Bardasht.query.filter_by(id=bardasht_id).first()
        return render_template('update_bardasht.html', bardasht=bardasht)

    if request.method == 'POST':
        print('pppppp')
        bardasht = Bardasht.query.get_or_404(bardasht_id)
        position = request.form.get('position')
        response_admin = request.form.get('response_admin', '')
        
        bardasht.position = position
        bardasht.response_admin = response_admin
        
        db.session.commit()
        return redirect(url_for('admin_bardasht'))


  

#33333333333333333333333333333333333
import logging
from flask import session, request, redirect, url_for, flash, render_template
import requests

ZIBAL_MERCHANT = '6702a62f6f3803000ccdd067'
ZIBAL_START_PAYMENT = 'https://gateway.zibal.ir/v1/request'
ZIBAL_REDIRECT_PAYMENT = 'https://gateway.zibal.ir/start/'
ZIBAL_VERIFY_PAYMENT = 'https://gateway.zibal.ir/v1/verify'
CALLBACK_URL = 'http://sab.softexchange.ir/verify_payment'
            #https://sarmaye.liara.run/payment_method
            #https://sab.softexchange.ir/login
@app.route('/payment_method')
@login_required
def payment_method():
    """صفحه انتخاب روش پرداخت"""
    return render_template('payment_method.html')

@app.route('/bank_transfer')
@login_required
def bank_transfer():
    """صفحه پرداخت کارت به کارت"""
    # اطلاعات کارت بانکی مقصد
    bank_info = {
        'card_number': '6037 9911 2345 6789',  # شماره کارت مقصد
        'bank_name': 'بانک ملی',
        'account_owner': 'شرکت سرمایه گستر'
    }
    return render_template('bank_transfer.html', bank_info=bank_info)

@app.route('/start_payment', methods=['POST'])
@login_required
def start_payment():
    try:
        total_price = request.form.get('total_price')
        if not total_price or not total_price.isdigit():
            flash("مبلغ پرداخت معتبر نیست", 'danger')
            return redirect(url_for('payment_method'))
        
        amount = int(total_price)  # زیبال مبلغ را به ریال می‌خواهد (نه تومان)
        
        # ذخیره اطلاعات در session
        session['payment_amount'] = amount
        session['total_price'] = total_price

        # داده‌های درخواست به زیبال
        data = {
            'merchant': ZIBAL_MERCHANT,
            'amount': amount * 10,  # تبدیل تومان به ریال
            'callbackUrl': CALLBACK_URL,
            'description': 'پرداخت در سامانه سرمایه',
            'orderId': f"ORDER_{session.get('user_id')}_{int(time.time())}",  # شماره سفارش
            'mobile': session.get('user_phone', '')  # اختیاری
        }
        
        # ارسال درخواست به زیبال
        response = requests.post(ZIBAL_START_PAYMENT, json=data, timeout=10)
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('result') == 100:  # کد موفقیت زیبال
                track_id = response_data['trackId']
                session['payment_trackId'] = track_id
                
                # هدایت کاربر به درگاه زیبال
                return redirect(f"{ZIBAL_REDIRECT_PAYMENT}{track_id}")
            else:
                error_code = response_data.get('result', 'نامشخص')
                error_message = get_zibal_error_message(error_code)
                flash(f"خطا در اتصال به درگاه پرداخت: {error_message}", 'danger')
                logging.error(f"Zibal error {error_code}: {error_message}")
        else:
            flash("خطا در ارتباط با درگاه پرداخت", 'danger')
        
        return redirect(url_for('failed'))
        
    except Exception as e:
        logging.error(f"Error in start_payment: {str(e)}")
        flash("خطای داخلی سرور", 'danger')
        return redirect(url_for('failed'))

@app.route('/verify_payment', methods=['GET'])
@login_required
def verify_payment():
    try:
        track_id = request.args.get('trackId')
        success = request.args.get('success')
        status = request.args.get('status')
        
        # اگر کاربر از پرداخت انصراف داده
        if success and success == '0':
            flash("پرداخت لغو شد", 'warning')
            return redirect(url_for('user_portfolio'))
        
        amount = session.get('payment_amount')
        if not amount or not track_id:
            flash("اطلاعات پرداخت نامعتبر است", 'danger')
            return redirect(url_for('failed'))

        # داده‌های تأیید پرداخت
        data = {
            'merchant': ZIBAL_MERCHANT,
            'trackId': track_id
        }

        # ارسال درخواست تأیید به زیبال
        response = requests.post(ZIBAL_VERIFY_PAYMENT, json=data, timeout=10)
        
        if response.status_code == 200:
            response_data = response.json()
            result_code = response_data.get('result')

            print(response_data)

            if result_code == 100:  # پرداخت موفق
                payment_data = response_data
                print('pmpmpmpm')
                return handle_successful_payment(payment_data, amount, track_id)
            
            else:
                error_message = get_zibal_error_message(result_code)
                flash(f"پرداخت ناموفق: {error_message}", 'danger')
                logging.error(f"Zibal verification error {result_code}: {error_message}")
        else:
            flash("خطا در ارتباط با درگاه پرداخت", 'danger')
        
        return redirect(url_for('failed'))
        
    except Exception as e:
        logging.error(f"Error in verify_payment: {str(e)}")
        flash("خطای داخلی سرور", 'danger')
        return redirect(url_for('failed'))

def handle_successful_payment(payment_data, amount, track_id):
    """مدیریت پرداخت موفق"""
    try:
        shamsi_date, shamsi_time = get_shamsi_datetime()
        user_id = session.get('user_id')
        
        # بررسی وجود asset
        ass = Asset.query.filter_by(asset_type='وجه نقد تومان').first()
        if not ass:
            ass = Asset(asset_type='وجه نقد تومان')
            db.session.add(ass)
            db.session.commit()

        # ایجاد رکورد سرمایه‌گذاری
        investment = Investment(
            user_id=user_id,
            asset_type='وجه نقد تومان',
            amount=amount,  # مبلغ به تومان
            transaction_type='buy',
            shamsi_date=shamsi_date,
            shamsi_time=shamsi_time,
            
            notes=f'پرداخت آنلاین زیبال - کد رهگیری: {track_id} - شماره کارت: {payment_data.get("cardNumber", "نامشخص")}'
        )
        
        db.session.add(investment)
        db.session.commit()
        
        # پاک کردن session payments
        session.pop('payment_amount', None)
        session.pop('payment_trackId', None)
        
        flash("پرداخت با موفقیت انجام شد", 'success')
        return redirect(url_for('user_portfolio'))
        
    except Exception as e:
        logging.error(f"Error in handle_successful_payment: {str(e)}")
        db.session.rollback()
        flash("خطا در ثبت اطلاعات پرداخت", 'danger')
        return redirect(url_for('failed'))

def get_zibal_error_message(error_code):
    """تبدیل کد خطای زیبال به پیام قابل فهم"""
    error_messages = {
        102: 'مرچنت کد نامعتبر',
        103: 'مرچنت کد غیرفعال',
        104: 'مرچنت کد نامعتبر',
        105: 'مبلغ نامعتبر',
        106: 'آدرس بازگشت نامعتبر',
        107: 'IP مرچنت نامعتبر',
        108: 'زمان بیش از حد انتظار',
        201: 'تراکنش قبلا تأیید شده',
        202: 'سفارش پرداخت نشده یا لغو شده',
        203: 'trackId نامعتبر'
    }
    return error_messages.get(error_code, f'خطای نامشخص (کد: {error_code})')

@app.route('/failed')
def failed():
    return render_template('failed.html')

#333333333333333333333333333
if __name__ == "__main__":
    app.run(debug=True)

""" if __name__ == "__main__":
    serve(
        app,
        host="0.0.0.0",
        port=5000,
        threads=4,  # افزایش تعداد threadها
        channel_timeout=60  # افزایش زمان انتظار
    ) """ 

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jdatetime
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_delete = db.Column(db.String(20), nullable=True)

    investments = db.relationship('Investment', backref='user', lazy=True)
 
class Shaba(db.Model):    # کارت و شبا
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shaba = db.Column(db.String(50), nullable=True)  # طلا، دلار، بیت‌کوین، ...
    card_number = db.Column(db.String(50), nullable=True)
    tozihat = db.Column(db.Text)

class Bardasht(db.Model):    # برداشت 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shaba = db.Column(db.String(50), nullable=True)  # طلا، دلار، بیت‌کوین، ...
    card_number = db.Column(db.String(50), nullable=True)
    asset_type = db.Column(db.String(50), nullable=False)  # طلا، دلار، بیت‌کوین، ...
    amount = db.Column(db.Float, nullable=False)
    tozihat = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response_admin = db.Column(db.Text, nullable=True)
    position = db.Column(db.String(50), default='در انتظار بررسی')  # وضعیت پیش‌فرض

class Investment(db.Model):    # سرمایه ها
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)  # طلا، دلار، بیت‌کوین، ...
    amount = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float)  # قیمت هر واحد در زمان خرید
    transaction_type = db.Column(db.String(20), nullable=False)  # buy, sell
    shamsi_date = db.Column(db.String(10), nullable=False)  # تاریخ شمسی
    shamsi_time = db.Column(db.String(8), nullable=False)  # ساعت
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_type = db.Column(db.String(50), nullable=False)  # طلا، دلار، بیت‌کوین، ...
    price_for_unit = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    symbol = db.Column(db.String(50), nullable=True)   # مثلا usd_sell برای دلار
    vahed = db.Column(db.String(50), nullable=True)
    zarib = db.Column(db.Integer, nullable=True)

    def current_price(self):  # به جای @property
        print(self.symbol, 'ppppp')
        """قیمت فعلی را از وب‌سرویس می‌گیرد"""
        if not self.symbol:
            print('nnnnnn')
            return 1
             
        try:
            print('eeeeee')
            #free3bP2CIilkCsEQtAmZ9xKG0KoJud3
            #premts4574hRpl4xfqgf2WxfGzoU5wSc
            response = requests.get('http://api.navasan.tech/latest/?api_key=premts4574hRpl4xfqgf2WxfGzoU5wSc'
                                    ,timeout=60
                                    )
            data = response.json()
            print('ddddddd')
            if self.symbol in data:
                print('ssssss')
                return float(data[self.symbol]['value'])
            else:
                print('bbbbbbbb')
                return self.price_for_unit
                
        except Exception as e:
            print('mmmmm')
            print(f"Error fetching price: {e}")
            return self.price_for_unit
    
        
class Resid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link = db.Column(db.String(255), nullable=True)  # افزایش طول برای لینک‌ها
    text = db.Column(db.Text, nullable=True)  # تغییر به Text برای پیام‌های طولانی
    response = db.Column(db.Text, nullable=True)
    position = db.Column(db.String(50), default='در انتظار بررسی')  # وضعیت پیش‌فرض
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('resids', lazy=True))


#3333333333333333333333

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure each user can answer each question only once
    __table_args__ = (db.UniqueConstraint('user_id', 'question_id', name='unique_user_question'),)
LIARA_BUCKET_NAME = "sssb"
S3_BUCKET = "sssb"
S3_KEY = "b3h91nmuamngeag2"
S3_SECRET = "37fa7944-15ba-4502-9dc5-f7b72fdc1980"
S3_ENDPOINT = 'https://storage.c2.liara.space'


from datetime import datetime
import uuid
from flask import Blueprint, jsonify, render_template, request, session
from models import *
from flask import Flask, flash, json, make_response, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename


message_blueprint = Blueprint('message', __name__)

from botocore.exceptions import NoCredentialsError
from botocore.client import Config
import os
import boto3
 

s3 = boto3.client(
    's3',
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
    endpoint_url=S3_ENDPOINT,
  
)

# Utility functions for S3
def upload_to_s3(file, bucket_name, object_name):
    try:
        s3.upload_fileobj(file, bucket_name, object_name)
        return True
    except NoCredentialsError:
        return False
    
def generate_presigned_url(bucket_name, object_name, expiration=3600):
    try:
        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': bucket_name, 'Key': object_name},
                                             ExpiresIn=expiration)
        return response
    except NoCredentialsError:
        return None



message_blueprint = Blueprint('message', __name__)

# تنظیمات آپلود
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@message_blueprint.route('/send_message', methods=['GET', 'POST'])
def send_message():
    if 'user_id' not in session:
        flash('لطفاً ابتدا وارد حساب کاربری خود شوید', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        text = request.form.get('text', '').strip()
        file = request.files.get('file')
        
        # اعتبارسنجی
        if not text and not file:
            flash('لطفاً پیام یا فایل ارسال کنید', 'error')
            return render_template('send_message.html')
        
        link = None
        if file and file.filename != '':
            if file.content_length > MAX_FILE_SIZE:
                flash('حجم فایل نباید بیشتر از ۱۶ مگابایت باشد', 'error')
                return render_template('send_message.html')
            
            if allowed_file(file.filename):
                # تولید نام یکتا برای فایل
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                
                # آپلود به S3
                if upload_to_s3(file, S3_BUCKET, unique_filename):
                    link = generate_presigned_url(S3_BUCKET, unique_filename)
                else:
                    flash('خطا در آپلود فایل', 'error')
                    return render_template('send_message.html')
            else:
                flash('فرمت فایل مجاز نیست', 'error')
                return render_template('send_message.html')
        
        # ذخیره در دیتابیس
        new_message = Resid(
            user_id=user_id,
            text=text,
            link=link,
            position='در انتظار بررسی'
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        flash('پیام شما با موفقیت ارسال شد', 'success')
        return redirect(url_for('message.my_messages'))
    
    return render_template('send_message.html')

@message_blueprint.route('/my_messages')
def my_messages():
    if 'user_id' not in session:
        flash('لطفاً ابتدا وارد حساب کاربری خود شوید', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    messages = Resid.query.filter_by(user_id=user_id).order_by(Resid.created_at.desc()).all()
    
    return render_template('my_messages.html', messages=messages)

@message_blueprint.route('/admin/messages')
def admin_messages():
   
    
    status_filter = request.args.get('status', 'all')
    
    query = Resid.query
    
    if status_filter != 'all':
        query = query.filter_by(position=status_filter)
    
    messages = query.order_by(Resid.created_at.desc()).all()
    
    return render_template('admin_messages.html', 
                         messages=messages, 
                         status_filter=status_filter)

@message_blueprint.route('/admin/respond_message/<int:message_id>', methods=['POST'])
def respond_message(message_id):
   
    message = Resid.query.get_or_404(message_id)
    response_text = request.form.get('response', '').strip()
    new_position = request.form.get('position', 'بررسی شده')
    
    if not response_text:
        return jsonify({'success': False, 'message': 'لطفاً پاسخ را وارد کنید'})
    
    message.response = response_text
    message.position = new_position
    message.responded_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'پاسخ با موفقیت ثبت شد'})

@message_blueprint.route('/delete_message/<int:message_id>')
def delete_message(message_id):
    if 'user_id' not in session:
        flash('لطفاً ابتدا وارد حساب کاربری خود شوید', 'error')
        return redirect(url_for('auth.login'))
    
    message = Resid.query.get_or_404(message_id)
    
    # کاربر فقط می‌تواند پیام‌های خودش را حذف کند
    if message.user_id != session['user_id'] and session.get('user_role') != 'admin':
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('message.my_messages'))
    
    db.session.delete(message)
    db.session.commit()
    
    flash('پیام با موفقیت حذف شد', 'success')
    
    if session.get('user_role') == 'admin':
        return redirect(url_for('message.admin_messages'))
    else:
        return redirect(url_for('message.my_messages'))
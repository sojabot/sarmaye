from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from models import db, Survey, Question, Answer, User
from sqlalchemy import distinct
from datetime import datetime

class SurveyForm(FlaskForm):
    title = StringField('عنوان نظرسنجی', validators=[DataRequired()])
    description = TextAreaField('توضیحات')
    submit = SubmitField('ذخیره')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('متن سوال', validators=[DataRequired()])
    option1 = StringField('گزینه ۱', validators=[DataRequired()])
    option2 = StringField('گزینه ۲', validators=[DataRequired()])
    option3 = StringField('گزینه ۳', validators=[DataRequired()])
    option4 = StringField('گزینه ۴', validators=[DataRequired()])
    submit = SubmitField('ذخیره')

nazar = Blueprint('nazar', __name__)

# تابع کمکی برای شمارش شرکت‌کنندگان
def get_survey_participants_count(survey_id):
    participant_count = db.session.query(
        distinct(Answer.user_id)
    ).join(Question).filter(
        Question.survey_id == survey_id
    ).count()
    return participant_count

# صفحه اصلی نظرسنجی‌ها
@nazar.route('/surveys')
@login_required
def nazars():
    surveys = Survey.query.filter_by(is_active=True).all()
    return render_template('surveys.html', surveys=surveys)

# صفحه نمایش یک نظرسنجی خاص
@nazar.route('/survey/<int:survey_id>')
@login_required
def survey_detail(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    questions = Question.query.filter_by(survey_id=survey_id).order_by(Question.order).all()
    
    # بررسی آیا کاربر قبلاً به این نظرسنجی پاسخ داده است
    user_answers = {}
    for question in questions:
        answer = Answer.query.filter_by(user_id=current_user.id, question_id=question.id).first()
        if answer:
            user_answers[question.id] = answer.selected_option
    
    return render_template('survey_detail.html', 
                         survey=survey, 
                         questions=questions, 
                         user_answers=user_answers)

# ثبت پاسخ کاربر
@nazar.route('/survey/<int:survey_id>/answer', methods=['POST'])
@login_required
def answer_survey(survey_id):
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            selected_option = int(value)
            
            # بررسی آیا کاربر قبلاً به این سوال پاسخ داده است
            existing_answer = Answer.query.filter_by(
                user_id=current_user.id, 
                question_id=question_id
            ).first()
            
            if existing_answer:
                existing_answer.selected_option = selected_option
            else:
                new_answer = Answer(
                    user_id=current_user.id,
                    question_id=question_id,
                    selected_option=selected_option
                )
                db.session.add(new_answer)
    
    db.session.commit()
    flash('پاسخ‌های شما با موفقیت ثبت شد.', 'success')
    return redirect(url_for('nazar.nazars'))

# بخش مدیریت - ایجاد نظرسنجی جدید
@nazar.route('/admin/survey/new', methods=['GET', 'POST'])
@login_required
def new_survey():
    form = SurveyForm()
    if form.validate_on_submit():
        survey = Survey(
            title=form.title.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(survey)
        db.session.commit()
        flash('نظرسنجی جدید ایجاد شد.', 'success')
        return redirect(url_for('nazar.manage_surveys'))
    
    return render_template('new_survey.html', form=form)

# بخش مدیریت - اضافه کردن سوال
@nazar.route('/admin/survey/<int:survey_id>/add_question', methods=['GET', 'POST'])
@login_required
def add_question(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        # پیدا کردن آخرین ترتیب سوال
        last_question = Question.query.filter_by(survey_id=survey_id).order_by(Question.order.desc()).first()
        new_order = last_question.order + 1 if last_question else 1
        
        question = Question(
            survey_id=survey_id,
            question_text=form.question_text.data,
            option1=form.option1.data,
            option2=form.option2.data,
            option3=form.option3.data,
            option4=form.option4.data,
            order=new_order
        )
        db.session.add(question)
        db.session.commit()
        flash('سوال جدید اضافه شد.', 'success')
        return redirect(url_for('nazar.manage_survey', survey_id=survey_id))
    
    return render_template('add_question.html', form=form, survey=survey)

# مشاهده نتایج نظرسنجی
@nazar.route('/admin/survey/<int:survey_id>/results')
@login_required
def survey_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    questions = Question.query.filter_by(survey_id=survey_id).order_by(Question.order).all()
    
    results = []
    for question in questions:
        answers = Answer.query.filter_by(question_id=question.id).all()
        option_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for answer in answers:
            option_counts[answer.selected_option] += 1
        
        total_votes = len(answers)
        results.append({
            'question': question,
            'option_counts': option_counts,
            'total_votes': total_votes,
            'percentage': {
                1: (option_counts[1] / total_votes * 100) if total_votes > 0 else 0,
                2: (option_counts[2] / total_votes * 100) if total_votes > 0 else 0,
                3: (option_counts[3] / total_votes * 100) if total_votes > 0 else 0,
                4: (option_counts[4] / total_votes * 100) if total_votes > 0 else 0
            }
        })
    
    return render_template('survey_results.html', 
                         survey=survey, 
                         results=results,
                         get_survey_participants_count=get_survey_participants_count)

# مدیریت نظرسنجی‌ها
@nazar.route('/admin/surveys')
@login_required
def manage_surveys():
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    
    surveys = Survey.query.filter_by(created_by=current_user.id).order_by(Survey.created_at.desc()).all()
    return render_template('manage_surveys.html', 
                         surveys=surveys, 
                         get_survey_participants_count=get_survey_participants_count)

# مدیریت یک نظرسنجی خاص
@nazar.route('/admin/survey/<int:survey_id>')
@login_required
def manage_survey(survey_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    
    survey = Survey.query.get_or_404(survey_id)
    questions = Question.query.filter_by(survey_id=survey_id).order_by(Question.order).all()
    return render_template('manage_survey.html', survey=survey, questions=questions)

# حذف نظرسنجی
@nazar.route('/admin/survey/<int:survey_id>/delete', methods=['POST'])
@login_required
def delete_survey(survey_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    survey = Survey.query.get_or_404(survey_id)
    
    # بررسی مالکیت نظرسنجی
    if survey.created_by != current_user.id:
        flash('شما مجوز حذف این نظرسنجی را ندارید.', 'error')
        return redirect(url_for('nazar.manage_surveys'))
    
    # حذف پاسخ‌های مرتبط
    questions = Question.query.filter_by(survey_id=survey_id).all()
    for question in questions:
        Answer.query.filter_by(question_id=question.id).delete()
    
    # حذف سوالات
    Question.query.filter_by(survey_id=survey_id).delete()
    
    # حذف نظرسنجی
    db.session.delete(survey)
    db.session.commit()
    
    flash('نظرسنجی با موفقیت حذف شد.', 'success')
    return redirect(url_for('nazar.manage_surveys'))

# فعال/غیرفعال کردن نظرسنجی
@nazar.route('/admin/survey/<int:survey_id>/toggle', methods=['POST'])
@login_required
def toggle_survey(survey_id):
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('user_dashboard'))
    survey = Survey.query.get_or_404(survey_id)
    
    # بررسی مالکیت نظرسنجی
    if survey.created_by != current_user.id:
        flash('شما مجوز تغییر این نظرسنجی را ندارید.', 'error')
        return redirect(url_for('nazar.manage_surveys'))
    
    activate = request.form.get('activate') == 'true'
    survey.is_active = activate
    db.session.commit()
    
    status = 'فعال' if activate else 'غیرفعال'
    flash(f'نظرسنجی با موفقیت {status} شد.', 'success')
    return redirect(url_for('nazar.manage_surveys'))

# حذف سوال
@nazar.route('/admin/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    survey_id = question.survey_id
    survey = Survey.query.get(survey_id)
    
    # بررسی مالکیت نظرسنجی
    if survey.created_by != current_user.id:
        flash('شما مجوز حذف این سوال را ندارید.', 'error')
        return redirect(url_for('nazar.manage_survey', survey_id=survey_id))
    
    # حذف پاسخ‌های مرتبط
    Answer.query.filter_by(question_id=question_id).delete()
    
    # حذف سوال
    db.session.delete(question)
    db.session.commit()
    
    flash('سوال با موفقیت حذف شد.', 'success')
    return redirect(url_for('nazar.manage_survey', survey_id=survey_id))


# مشاهده پاسخ‌های هر کاربر
@nazar.route('/admin/survey/<int:survey_id>/user_answers')
@login_required
def user_answers(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    # بررسی مالکیت نظرسنجی
    if survey.created_by != current_user.id:
        flash('شما مجوز مشاهده این اطلاعات را ندارید.', 'error')
        return redirect(url_for('nazar.manage_surveys'))
    
    # دریافت تمام کاربرانی که در این نظرسنجی شرکت کرده‌اند
    participants = db.session.query(
        User
    ).join(Answer).join(Question).filter(
        Question.survey_id == survey_id
    ).distinct().all()
    
    # دریافت تمام سوالات نظرسنجی
    questions = Question.query.filter_by(survey_id=survey_id).order_by(Question.order).all()
    
    # ایجاد ساختار داده برای پاسخ‌ها
    user_responses = []
    for user in participants:
        user_data = {
            'user': user,
            'answers': {}
        }
        for question in questions:
            answer = Answer.query.filter_by(
                user_id=user.id, 
                question_id=question.id
            ).first()
            if answer:
                user_data['answers'][question.id] = {
                    'selected_option': answer.selected_option,
                    'option_text': getattr(question, f'option{answer.selected_option}'),
                    'answered_at': answer.answered_at
                }
        user_responses.append(user_data)
    
    return render_template('user_answers.html', 
                         survey=survey, 
                         user_responses=user_responses,
                         questions=questions)

# مشاهده پاسخ‌های یک کاربر خاص
@nazar.route('/admin/survey/<int:survey_id>/user/<int:user_id>')
@login_required
def user_survey_answers(survey_id, user_id):
    survey = Survey.query.get_or_404(survey_id)
    user = User.query.get_or_404(user_id)
    
    # بررسی مالکیت نظرسنجی
    if survey.created_by != current_user.id:
        flash('شما مجوز مشاهده این اطلاعات را ندارید.', 'error')
        return redirect(url_for('nazar.manage_surveys'))
    
    # دریافت سوالات و پاسخ‌های کاربر
    questions = Question.query.filter_by(survey_id=survey_id).order_by(Question.order).all()
    user_answers = {}
    
    for question in questions:
        answer = Answer.query.filter_by(
            user_id=user.id, 
            question_id=question.id
        ).first()
        if answer:
            user_answers[question.id] = {
                'selected_option': answer.selected_option,
                'option_text': getattr(question, f'option{answer.selected_option}'),
                'answered_at': answer.answered_at
            }
    
    return render_template('user_survey_detail.html', 
                         survey=survey, 
                         user=user, 
                         questions=questions, 
                         user_answers=user_answers)
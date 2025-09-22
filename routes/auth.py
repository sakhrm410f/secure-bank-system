from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models.user import User, LoginAttempt, db
from utils.security import SecurityUtils
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Secure login with rate limiting and account lockout"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = SecurityUtils.sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        # Input validation
        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'error')
            return render_template('auth/login.html')
        
        # Get client info for logging
        client_ip = SecurityUtils.get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Check for user
        user = User.query.filter_by(username=username).first()
        
        # Log login attempt
        login_attempt = LoginAttempt(
            ip_address=client_ip,
            username=username,
            success=False,
            user_agent=user_agent
        )
        
        if user and user.is_active:
            # Check if account is locked
            if user.is_account_locked():
                flash('الحساب مقفل مؤقتاً. يرجى المحاولة لاحقاً', 'error')
                db.session.add(login_attempt)
                db.session.commit()
                return render_template('auth/login.html')
            
            # Verify password
            if user.check_password(password):
                # Successful login
                user.unlock_account()
                user.update_last_login()
                login_attempt.success = True
                
                db.session.add(login_attempt)
                db.session.commit()
                
                login_user(user, remember=False)
                flash('تم تسجيل الدخول بنجاح', 'success')
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard.index'))
            else:
                # Failed login
                user.lock_account()
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        
        # Log failed attempt
        db.session.add(login_attempt)
        db.session.commit()
    
    # CSRF token is provided by Flask-WTF via csrf_token() in templates
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Secure user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Get and sanitize form data
        username = SecurityUtils.sanitize_input(request.form.get('username', ''))
        email = SecurityUtils.sanitize_input(request.form.get('email', ''))
        full_name = SecurityUtils.sanitize_input(request.form.get('full_name', ''))
        phone = SecurityUtils.sanitize_input(request.form.get('phone', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        # CSRF is validated by Flask-WTF CSRFProtect
        
        # Input validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('اسم المستخدم يجب أن يكون 3 أحرف على الأقل')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('اسم المستخدم يجب أن يحتوي على أحرف وأرقام فقط')
        
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('البريد الإلكتروني غير صحيح')
        
        if not full_name or len(full_name) < 2:
            errors.append('الاسم الكامل مطلوب')
        
        if password != confirm_password:
            errors.append('كلمات المرور غير متطابقة')
        
        # Password strength validation
        is_strong, password_msg = SecurityUtils.validate_password_strength(password)
        if not is_strong:
            errors.append(password_msg)
        
        # Check for existing users
        if User.query.filter_by(username=username).first():
            errors.append('اسم المستخدم موجود بالفعل')
        
        if User.query.filter_by(email=email).first():
            errors.append('البريد الإلكتروني موجود بالفعل')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                phone=phone
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول الآن', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء الحساب', 'error')
    
    # CSRF token is provided by Flask-WTF via csrf_token() in templates
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Secure logout"""
    logout_user()
    session.clear()  # Clear all session data
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login'))

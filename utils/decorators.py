from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role for access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def active_user_required(f):
    """Decorator to require active user account"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('حسابك غير نشط. يرجى التواصل مع الإدارة', 'error')
            return redirect(url_for('auth.logout'))
        
        return f(*args, **kwargs)
    return decorated_function

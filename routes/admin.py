from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models.user import db, User, Account, Transaction, LoginAttempt
from utils.decorators import admin_required
from utils.security import SecurityUtils
from decimal import Decimal, InvalidOperation

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with system overview"""
    # System statistics
    total_users = User.query.count()
    total_accounts = Account.query.count()
    total_transactions = Transaction.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Recent activity نشاط حديث
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_transactions = Transaction.query.order_by(desc(Transaction.created_at)).limit(10).all()
    
    # Security alerts تنبيهات امنية
    failed_logins_today = LoginAttempt.query.filter(
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= datetime.utcnow().date()
    ).count()
    
    locked_accounts = User.query.filter(
        User.account_locked_until > datetime.utcnow()
    ).count()
    
    # Financial statistics الاحصاءات الماليه
    total_balance = db.session.query(func.sum(Account.balance)).scalar() or 0
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_accounts=total_accounts,
                         total_transactions=total_transactions,
                         active_users=active_users,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions,
                         failed_logins_today=failed_logins_today,
                         locked_accounts=locked_accounts,
                         total_balance=total_balance)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage all users ادارة المستخدمين"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    # البحث او الفلترة عن مستخدم
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.full_name.contains(search))
        )
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """View specific user details"""
    user = User.query.get_or_404(user_id)
    accounts = Account.query.filter_by(user_id=user_id).all()
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(desc(Transaction.created_at)).limit(20).all()
    login_attempts = LoginAttempt.query.filter_by(username=user.username).order_by(desc(LoginAttempt.attempted_at)).limit(10).all()
    
    return render_template('admin/user_details.html',
                         user=user,
                         accounts=accounts,
                         transactions=transactions,
                         login_attempts=login_attempts)

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status تبديل الحالة النشط للمستخدم"""
    user = User.query.get_or_404(user_id)
    
    if user.username == 'admin':
        flash('لا يمكن تعطيل حساب المدير الرئيسي', 'error')
        return redirect(url_for('admin.user_details', user_id=user_id))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'تم تفعيل' if user.is_active else 'تم تعطيل'
    flash(f'{status} حساب المستخدم {user.username} بنجاح', 'success')
    
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@login_required
@admin_required
def unlock_user(user_id):
    """Unlock user account فتح حساب المستخدم"""
    user = User.query.get_or_404(user_id)
    user.unlock_account()
    db.session.commit()
    
    flash(f'تم إلغاء قفل حساب المستخدم {user.username} بنجاح', 'success')
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset user password اعادة تعيين كلمة السر للمستخدم وهذا بواسطة المسؤال فقط"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 8:
        flash('كلمة المرور يجب أن تكون 8 أحرف على الأقل', 'error')
        return redirect(url_for('admin.user_details', user_id=user_id))
    
    # Validate password strength التحقق من قوة الباسوورد
    is_strong, message = SecurityUtils.validate_password_strength(new_password)
    if not is_strong:
        flash(f'كلمة المرور ضعيفة: {message}', 'error')
        return redirect(url_for('admin.user_details', user_id=user_id))
    
    user.set_password(new_password)
    user.unlock_account()  # Unlock account when password is reset
    db.session.commit()
    
    flash(f'تم تغيير كلمة مرور المستخدم {user.username} بنجاح', 'success')
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/accounts')
@login_required
@admin_required
def accounts():
    """Manage all accounts  ادارة الحسابات"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Account.query.join(User)
    if search:
        query = query.filter(
            (Account.account_number.contains(search)) |
            (User.username.contains(search)) |
            (User.full_name.contains(search))
        )
    
    accounts = query.order_by(desc(Account.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/accounts.html', accounts=accounts, search=search)

@admin_bp.route('/accounts/<int:account_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_account_status(account_id):
    """Toggle account active status"""
    account = Account.query.get_or_404(account_id)
    account.is_active = not account.is_active
    db.session.commit()
    
    status = 'تم تفعيل' if account.is_active else 'تم تعطيل'
    flash(f'{status} الحساب {account.account_number} بنجاح', 'success')
    
    return redirect(url_for('admin.accounts'))

@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions():
    """View all transactions"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Transaction.query.join(User)
    if search:
        query = query.filter(
            (Transaction.description.contains(search)) |
            (User.username.contains(search))
        )
    
    transactions = query.order_by(desc(Transaction.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/transactions.html', transactions=transactions, search=search)

@admin_bp.route('/security')
@login_required
@admin_required
def security():
    """Security monitoring dashboard لوحة تحكم مراقبة الامان"""
    #الفلترة
    # Recent failed login attempts محاولات تسجيل الدخول الاخيرة الفاشله
    failed_logins = LoginAttempt.query.filter_by(success=False).order_by(desc(LoginAttempt.attempted_at)).limit(50).all()
    
    # Locked accounts حسابات مقفله
    locked_accounts = User.query.filter(User.account_locked_until > datetime.utcnow()).all()
    
    # Suspicious IP addresses (multiple failed attempts محاولات عديده لتسجيل الفاشل) عناوين مشبوهه 
    suspicious_ips = db.session.query(
        LoginAttempt.ip_address,
        func.count(LoginAttempt.id).label('attempt_count')
    ).filter(
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= datetime.utcnow() - timedelta(hours=24)
    ).group_by(LoginAttempt.ip_address).having(
        func.count(LoginAttempt.id) >= 5
    ).all()
    
    return render_template('admin/security.html',
                         failed_logins=failed_logins,
                         locked_accounts=locked_accounts,
                         suspicious_ips=suspicious_ips)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate system reports انشاء تقارير النظام"""
    # User registration trends (last 30 days) تسجيل المستخدم اخر 30 يوم
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(func.date(User.created_at)).all()
    
    # Transaction volume trends اتجاهات حجم المعاملات
    daily_transactions = db.session.query(
        func.date(Transaction.created_at).label('date'),
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('total_amount')
        #حجم المبالاغ الذي حدث عليها معاملات
    ).filter(
        Transaction.created_at >= thirty_days_ago
    ).group_by(func.date(Transaction.created_at)).all()
    
    # Account type distribution
    account_types = db.session.query(
        Account.account_type,
        func.count(Account.id).label('count')
    ).group_by(Account.account_type).all()
    
    return render_template('admin/reports.html',
                         daily_registrations=daily_registrations,
                         daily_transactions=daily_transactions,
                         account_types=account_types)

@admin_bp.route('/system_logs')
@login_required
@admin_required
def system_logs():
    """View system logs عرض سجلات النظام"""
    page = request.args.get('page', 1, type=int)
    
    # All login attempts with pagination كل محاولات تسجيل الدخول مع ترقيم الصفحات
    login_attempts = LoginAttempt.query.order_by(desc(LoginAttempt.attempted_at)).paginate(
        page=page, per_page=100, error_out=False
    )
    
    return render_template('admin/system_logs.html', login_attempts=login_attempts)

@admin_bp.route('/user/<int:user_id>/add_balance', methods=['POST'])
@login_required
@admin_required
def add_balance(user_id):
    """Add balance to user account (Admin only المسؤول فقط يقدر يضيف) اضافة زلط الى حساب المستخدم"""
    user = User.query.get_or_404(user_id)
    
    # Get form data
    amount_raw = (request.form.get('amount') or '').strip()
    description = (request.form.get('description') or '').strip()
    
    # Validate input and convert to Decimal with 2 dp التحقق من صحة الادخال وتحويله الى رقم عشري
    try:
        amount_dec = Decimal(amount_raw)
    except (InvalidOperation, ValueError):
        return jsonify({'success': False, 'message': 'قيمة المبلغ غير صحيحة'}), 400

    if amount_dec <= Decimal('0'):
        return jsonify({'success': False, 'message': 'يجب إدخال مبلغ صحيح أكبر من الصفر'}), 400

    # Ensure two decimal places ضمان منزلين عشرييين
    amount_dec = amount_dec.quantize(Decimal('0.01'))
    
    if not description:
        return jsonify({'success': False, 'message': 'يجب إدخال سبب الإيداع'}), 400
    
    if len(description) > 255:
        return jsonify({'success': False, 'message': 'الوصف يجب ألا يتجاوز 255 حرفاً'}), 400
    
    # Start transaction بداء المعامله
    try:
        # Get user's first active account or create one if none exists
        #احصل على اول حساب نشط للمستخدم او انشئ حساب اذا لم يكن هناك 
        account = Account.query.filter_by(user_id=user.id, is_active=True).first()
        
        if not account:
            # Create a new account if user has none انشاء حساب جديد اذا لم يكن لدى المستخدم اي حساب
            account = Account(
                user_id=user.id,
                account_type='checking',
                balance=Decimal('0.00')
            )
            db.session.add(account)
        
        # Update account balance تحديث رصيد الحساب
        account.balance = (account.balance or Decimal('0.00')) + amount_dec
        
        # Create transaction record انشاء سجل المعامله 
        #deposit = ايداع
        transaction = Transaction(
            transaction_type='deposit',
            amount=amount_dec,
            description=f'إيداع إداري: {description}',
            to_account_id=account.id,
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(transaction)
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم إضافة ${float(amount_dec):.2f} بنجاح إلى حساب المستخدم {user.username}',
            'new_balance': float(account.balance)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء معالجة الطلب: {str(e)}'
        }), 500

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models.user import User, Account, Transaction, db
from utils.security import SecurityUtils
from decimal import Decimal
from datetime import datetime
import re

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    # Get user's accounts
    accounts = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Get recent transactions المعاملات الحديثة
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                         .order_by(Transaction.created_at.desc())\
                                         .limit(10).all()
    
    # Calculate total balance
    total_balance = sum(account.balance for account in accounts)
    
    # CSRF token is provided in templates via csrf_token()
    return render_template('dashboard/index.html', 
                         accounts=accounts,
                         recent_transactions=recent_transactions,
                         total_balance=total_balance)

@dashboard_bp.route('/create_account', methods=['POST'])
@login_required
def create_account():
    """Create new bank account انشاء حساب جاري او توفير"""
    # CSRF is validated by Flask-WTF CSRFProtect
    
    account_type = SecurityUtils.sanitize_input(request.form.get('account_type', ''))
    
    # Validate account type
    if account_type not in ['checking', 'savings']:
        flash('نوع الحساب غير صحيح', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Check if user already has this type of account التحقق من انه لا يوجد حسابين من نفس النوع  توفير توفير
    existing_account = Account.query.filter_by(
        user_id=current_user.id, 
        account_type=account_type,
        is_active=True
    ).first()
    
    if existing_account:
        flash('لديك حساب من هذا النوع بالفعل', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Create new account
        account = Account(
            user_id=current_user.id,
            account_type=account_type,
            balance=Decimal('0.00')
        )
        
        db.session.add(account)
        db.session.commit()
        
        flash(f'تم إنشاء حساب {account_type} بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء إنشاء الحساب', 'error')
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    """Money transfer between accounts التحويلات بين الحسابات"""
    if request.method == 'POST':
        from_account_id = request.form.get('from_account_id')
        to_account_number = SecurityUtils.sanitize_input(request.form.get('to_account_number', ''))
        amount_str = SecurityUtils.sanitize_input(request.form.get('amount', ''))
        description = SecurityUtils.sanitize_input(request.form.get('description', ''))
        # CSRF is validated by Flask-WTF CSRFProtect
        
        # Input validation
        errors = []
        
        if not from_account_id:
            errors.append('يرجى اختيار الحساب المرسل')
        
        if not SecurityUtils.validate_account_number(to_account_number):
            errors.append('رقم الحساب المستقبل غير صحيح')
        
        if not SecurityUtils.validate_amount(amount_str):
            errors.append('المبلغ غير صحيح')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('dashboard.transfer'))
        
        try:
            amount = Decimal(amount_str)
            
            # Get accounts
            from_account = Account.query.filter_by(
                id=from_account_id, 
                user_id=current_user.id,
                is_active=True
            ).first()
            
            to_account = Account.query.filter_by(
                account_number=to_account_number,
                is_active=True
            ).first()
            
            if not from_account:
                flash('الحساب المرسل غير موجود', 'error')
                return redirect(url_for('dashboard.transfer'))
            
            if not to_account:
                flash('الحساب المستقبل غير موجود', 'error')
                return redirect(url_for('dashboard.transfer'))
            
            if from_account.id == to_account.id:
                flash('لا يمكن التحويل إلى نفس الحساب', 'error')
                return redirect(url_for('dashboard.transfer'))
            
            # Check balance
            if from_account.balance < amount:
                flash('الرصيد غير كافي', 'error')
                return redirect(url_for('dashboard.transfer'))
            
            # Perform transfer اجراء التحويل
            from_account.balance -= amount
            to_account.balance += amount
            
            # Create transaction record انشاء سجل المعامله
            transaction = Transaction(
                transaction_type='transfer',
                amount=amount,
                description=description or f'تحويل إلى {to_account.account_number}',
                from_account_id=from_account.id,
                to_account_id=to_account.id,
                user_id=current_user.id,
                ip_address=SecurityUtils.get_client_ip(),
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'تم تحويل {amount} بنجاح', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التحويل', 'error')
    
    # Get user's accounts for the form
    accounts = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # CSRF token is provided in templates via csrf_token()
    return render_template('dashboard/transfer.html', 
                         accounts=accounts)

@dashboard_bp.route('/transactions')
@login_required
def transactions():
    """View transaction history سجل المعاملات"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                  .order_by(Transaction.created_at.desc())\
                                  .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('dashboard/transactions.html', transactions=transactions)

@dashboard_bp.route('/account/<int:account_id>')
@login_required
def account_details(account_id):
    """View specific account details"""
    account = Account.query.filter_by(
        id=account_id, 
        user_id=current_user.id,
        is_active=True
    ).first_or_404()
    
    # Get account transactions
    transactions = Transaction.query.filter(
        (Transaction.from_account_id == account_id) | 
        (Transaction.to_account_id == account_id)
    ).order_by(Transaction.created_at.desc()).limit(50).all()
    
    from datetime import datetime, timedelta
    
    return render_template('dashboard/account_details.html', 
                         account=account,
                         transactions=transactions,
                         now=datetime.now(),
                         timedelta=timedelta)

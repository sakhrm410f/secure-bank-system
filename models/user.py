from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Security fields الحقول الأمنة
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile fields حقول الملف الشخصي
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user' الدور
    
    # Relationships العلاقات
    accounts = db.relationship('Account', backref='owner', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password with strong hashing تعيين كلمة مرور مع هااااش قوي """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:100000')
    
    def check_password(self, password):
        """Check password against hash التحقق من كلمة المرور مقابل الهاش"""
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        """Check if account is currently locked التحقق اذا كان الحساب مغلقا حاليا"""
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    def lock_account(self):
        """Lock account for 30 minutes after 3 failed attempts اغلاق الحساب بعد 30 دقيقه من عدم النشاط"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 3:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def unlock_account(self):
        """Unlock account and reset failed attempts فتح الحساب واعادة المحاوله"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    account_type = db.Column(db.String(20), nullable=False)  # 'checking', 'savings'
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    
    # Security and audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    transactions_from = db.relationship('Transaction', 
                                      foreign_keys='Transaction.from_account_id',
                                      backref='from_account', lazy=True)
    transactions_to = db.relationship('Transaction', 
                                    foreign_keys='Transaction.to_account_id',
                                    backref='to_account', lazy=True)
    
    def generate_account_number(self):
        """Generate unique account number"""
        while True:
            account_num = ''.join([str(secrets.randbelow(10)) for _ in range(10)])
            if not Account.query.filter_by(account_number=account_num).first():
                return account_num
    
    def __init__(self, **kwargs):
        super(Account, self).__init__(**kwargs)
        if not self.account_number:
            self.account_number = self.generate_account_number()
    
    def __repr__(self):
        return f'<Account {self.account_number}>'

class Transaction(db.Model):
    __tablename__ = 'transactions المعاملات'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'transfer', 'deposit', 'withdrawal'
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    # Account references
    from_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    to_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    
    # Security and audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.transaction_type} - {self.amount}>'

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<LoginAttempt {self.ip_address}: {self.success}>'

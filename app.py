from flask import Flask, render_template, request, session, redirect, url_for
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import os

# Import configurations
from config import config

# Import models
from models.user import db, User

# Import routes
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp

# Import utilities
from utils.security import SecurityUtils

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize CSRF Protection
    csrf = CSRFProtect(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize Rate Limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per hour"],
        storage_uri="memory://"
    )
    limiter.init_app(app)
    
    # Apply rate limiting to auth routes
    limiter.limit("5 per minute")(auth_bp)
    
    # Exempt authenticated admin users from rate limiting (e.g., on admin dashboard)
    @limiter.request_filter
    def skip_limits_for_admins():
        try:
            return current_user.is_authenticated and current_user.is_admin()
        except Exception:
            return False
    
    # Initialize Security Utils
    security = SecurityUtils(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in headers.items():
            response.headers[header] = value
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html'), 429
    
    # Home route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('dashboard.index'))
        return render_template('index.html')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@securebank.com',
                full_name='System Administrator',
                role='admin'
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
        
    # Set the login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Import models after initializing db to avoid circular imports
    from app import models
    from app.models import Notification  # Import Notification model

    # Define user_loader callback here
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Import and register the blueprints
    from app.main.routes import main as main_blueprint
    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    
    # Add the context processor at the application level
    @app.context_processor
    def inject_unread_notifications():
        if current_user.is_authenticated:
            unread_notifications = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            return dict(unread_notifications=unread_notifications)
        return dict(unread_notifications=0)
    
    return app

from flask import Blueprint
from flask_login import current_user
from app.models import Notification

main = Blueprint('main', __name__)

@main.app_context_processor
def inject_unread_notifications():
    if current_user.is_authenticated:
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()
        return dict(unread_notifications=unread_notifications)
    return dict(unread_notifications=0)

# Import your routes to register them with the blueprint
from app.main import routes

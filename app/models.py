from app import db
from flask_login import UserMixin
from datetime import datetime


user_genres = db.Table('user_genres',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'))
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Store hashed passwords
    email = db.Column(db.String(120), unique=True, nullable=False)
    favorite_genres = db.Column(db.String(200))
    genres = db.relationship('Genre', secondary=user_genres, backref='users')
    
    # Relationships
    books = db.relationship('Book', backref='owner', lazy=True)
    sent_requests = db.relationship('ExchangeRequest', foreign_keys='ExchangeRequest.from_user_id', backref='from_user', lazy=True)
    received_requests = db.relationship('ExchangeRequest', foreign_keys='ExchangeRequest.to_user_id', backref='to_user', lazy=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    genre = db.Column(db.String(100))
    isbn = db.Column(db.String(20))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'
    

exchange_books = db.Table('exchange_books',
    db.Column('exchange_request_id', db.Integer, db.ForeignKey('exchange_requests.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'), primary_key=True)
)

class ExchangeRequest(db.Model):
    __tablename__ = 'exchange_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_requested_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    book_offered_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # Possible values: pending, responded, accepted, declined
    
    # Relationships
    book_requested = db.relationship('Book', foreign_keys=[book_requested_id], backref='requested_in')
    book_offered = db.relationship('Book', foreign_keys=[book_offered_id], backref='offered_in')

    # Books that User B selects from User A's collection
    selected_books = db.relationship('Book', secondary='exchange_books', backref='exchange_requests')
    
    def __repr__(self):
        return f'<ExchangeRequest from {self.from_user_id} to {self.to_user_id}>'
    

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    link = db.Column(db.String(255))  # URL or route name

    user = db.relationship('User', backref='notifications')
    

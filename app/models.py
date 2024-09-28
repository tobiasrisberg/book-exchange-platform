from app import db
from flask_login import UserMixin
from datetime import datetime, timezone


user_genres = db.Table('user_genres',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id')),
    db.PrimaryKeyConstraint('user_id', 'genre_id', name='user_genres_pk')
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Store hashed passwords
    email = db.Column(db.String(120), unique=True, nullable=False)
    # favorite_genres = db.Column(db.String(200))
    genres = db.relationship('Genre', secondary=user_genres, backref='users')
    
    # Relationships
    books = db.relationship('Book', backref='owner', lazy='dynamic')
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
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'))
    genre = db.relationship('Genre', backref='books')
    isbn = db.Column(db.String(20))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'
    

exchange_books = db.Table('exchange_books',
    db.Column('exchange_request_id', db.Integer, db.ForeignKey('exchange_requests.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id')),
    db.PrimaryKeyConstraint('exchange_request_id', 'book_id', name='exchange_books_pk')
)

class ExchangeRequest(db.Model):
    __tablename__ = 'exchange_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_requested_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    book_offered_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # Possible values: pending, responded, accepted, declined
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
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

    def __repr__(self):
        return f'<Genre {self.name}>'

    def __str__(self):
        return self.name


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    link = db.Column(db.String(255))  # URL or route name

    user = db.relationship('User', backref='notifications')
    

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    
    user = db.relationship('User', backref='messages')
    book = db.relationship('Book', backref='messages')
    
    def __repr__(self):
        return f'<Message {self.content[:20]}... by {self.user.username}>'

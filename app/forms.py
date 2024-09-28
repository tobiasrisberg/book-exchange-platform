from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectMultipleField,
    RadioField,
    HiddenField,
    TextAreaField,
    BooleanField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app.models import User, Genre


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    # Add the favorite_genres field
    favorite_genres = SelectMultipleField('Favorite Genres', coerce=int, validators=[DataRequired()])
    
    submit = SubmitField('Register')
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Populate the choices for favorite_genres
        self.favorite_genres.choices = [(genre.id, genre.name) for genre in Genre.query.all()]
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=2, max=64)]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddBookForm(FlaskForm):
    isbn = StringField(
        'ISBN', validators=[DataRequired(), Length(min=10, max=13)]
    )
    submit = SubmitField('Add Book')

class ExchangeRequestForm(FlaskForm):
    submit = SubmitField('I Want to Exchange')

class SelectBooksForm(FlaskForm):
    selected_books = BooleanField(
        'Select Books', validators=[DataRequired()] # coerce=int,
    ) 
    submit = SubmitField('Send Selection')
    decline = SubmitField('Decline Exchange')

class ConfirmExchangeForm(FlaskForm):
    selected_book = RadioField(
        'Select a Book', coerce=int, validators=[DataRequired()]
    )
    confirm = SubmitField('Confirm Exchange')
    decline = SubmitField('Decline Exchange')

class SearchForm(FlaskForm):
    query = StringField('Search')
    submit = SubmitField('Search')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    genres = SelectMultipleField('Favorite Genres', coerce=int)
    submit = SubmitField('Update Profile')

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')
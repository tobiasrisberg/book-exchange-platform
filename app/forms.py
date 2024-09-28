from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectMultipleField,
    RadioField,
    HiddenField,
)
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=2, max=64)]
    )
    email = StringField('Email', validators=[DataRequired(), Email()])
    favorite_genres = StringField('Favorite Genres')
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField('Register')

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
    selected_books = SelectMultipleField(
        'Select Books', coerce=int, validators=[DataRequired()]
    )
    submit = SubmitField('Send Selection')

class ConfirmExchangeForm(FlaskForm):
    selected_book = RadioField(
        'Select a Book', coerce=int, validators=[DataRequired()]
    )
    confirm = SubmitField('Confirm Exchange')
    decline = SubmitField('Decline Exchange')

class SearchForm(FlaskForm):
    query = StringField('Search')
    submit = SubmitField('Search')
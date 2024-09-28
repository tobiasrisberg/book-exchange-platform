from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_required, current_user
from app.models import Book, ExchangeRequest, User, Genre, Notification, Message
from app import db
from app.utils import get_book_details
from app.forms import (
    AddBookForm,
    ExchangeRequestForm,
    SelectBooksForm,
    ConfirmExchangeForm,
    SearchForm,
    ProfileForm,
    MessageForm
)

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return redirect(url_for('main.discover'))


@main.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    form = AddBookForm()
    # genres = Genre.query.all()
    # form.genre.choices = [(genre.id, genre.name) for genre in genres]

    if form.validate_on_submit():
        isbn = form.isbn.data
        book_details = get_book_details(isbn)
        if book_details:
            # Find or create the Genre
            genre_name = book_details['genre']
            genre = Genre.query.filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.commit()

            new_book = Book(
                title=book_details['title'],
                author=book_details['author'],
                genre_id=genre.id,
                isbn=isbn,
                image_url=book_details['image_url'],
                owner=current_user
            )
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('main.my_books'))
        else:
            flash('Book not found. Please check the ISBN.', 'danger')
    return render_template('add_book.html', form=form)



@main.route('/my_books')
@login_required
def my_books():
    books = Book.query.filter_by(
        owner_id=current_user.id
    ).filter(
        Book.is_available == True
    ).all()
    return render_template('my_books.html', books=books)


@main.route('/books')
@login_required
def books():
    form = SearchForm(request.args)
    query = request.args.get('query', '')
    if query:
        books = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%')) |
            (Book.genre.has(name=query))
        ).filter(
            Book.owner_id != current_user.id,
            Book.is_available == True
        ).all()
    else:
        books = Book.query.filter(
            Book.owner_id != current_user.id,
            Book.is_available == True
        ).all()
    return render_template('books.html', books=books, form=form)


@main.route('/book/<int:book_id>')
@login_required
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    form = ExchangeRequestForm()
    # Check if an exchange request exists
    existing_request = ExchangeRequest.query.filter_by(
        from_user_id=current_user.id,
        to_user_id=book.owner_id,
        book_requested_id=book.id
    ).filter(ExchangeRequest.status.in_(['pending', 'responded'])).first()
    request_sent = existing_request is not None
    return render_template('book_details.html', book=book, form=form, request_sent=request_sent)



@main.route('/request_exchange/<int:book_id>', methods=['POST'])
@login_required
def request_exchange(book_id):
    form = ExchangeRequestForm()
    if form.validate_on_submit():
        book = Book.query.get_or_404(book_id)
        if book.owner == current_user:
            flash("You cannot request an exchange for your own book.", 'warning')
            return redirect(url_for('main.book_details', book_id=book_id))

        # Check for existing exchange requests regardless of status
        existing_request = ExchangeRequest.query.filter_by(
            from_user_id=current_user.id,
            to_user_id=book.owner_id,
            book_requested_id=book.id
        ).filter(ExchangeRequest.status.in_(['pending', 'responded'])).first()

        if existing_request:
            flash('You have already sent an exchange request for this book.', 'info')
        else:
            exchange_request = ExchangeRequest(
                from_user_id=current_user.id,
                to_user_id=book.owner_id,
                book_requested_id=book.id,
                status='pending'
            )
            db.session.add(exchange_request)
            db.session.commit()
            flash('Exchange request sent!', 'success')

            # Create a notification
            notification = Notification(
                message=f'{current_user.username} wants to exchange for your book "{book.title}".',
                user_id=book.owner_id,
                link=url_for('main.incoming_requests')
            )
            db.session.add(notification)
            db.session.commit()

        return redirect(url_for('main.book_details', book_id=book_id))
    else:
        flash('Invalid form submission.', 'danger')
        return redirect(url_for('main.book_details', book_id=book_id))


@main.route('/incoming_requests')
@login_required
def incoming_requests():
    requests = ExchangeRequest.query.filter_by(to_user_id=current_user.id, status='pending').all()
    return render_template('incoming_requests.html', requests=requests)

@main.route('/select_books/<int:request_id>', methods=['GET', 'POST'])
@login_required
def select_books(request_id):
    exchange_request = ExchangeRequest.query.get_or_404(request_id)
    if exchange_request.to_user_id != current_user.id:
        flash('You are not authorized to view this exchange request.', 'danger')
        return redirect(url_for('main.incoming_requests'))

    form = SelectBooksForm()
    offered_books = exchange_request.from_user.books.filter_by(is_available=True).all()
    form.selected_books.choices = [(book.id, f"{book.title} by {book.author}") for book in offered_books]

    if form.validate_on_submit():
        if 'submit' in request.form:
            selected_book_id = form.selected_books.data
            selected_book = Book.query.get_or_404(selected_book_id)

            # Update exchange request
            exchange_request.selected_books.append(selected_book)
            exchange_request.status = 'responded'
            db.session.commit()

            # Create a notification
            notification = Notification(
                message=f'{current_user.username} has responded to your exchange request.',
                user_id=exchange_request.from_user_id,
                link=url_for('main.responses')
            )
            db.session.add(notification)
            db.session.commit()

            flash('You have responded to the exchange request.', 'success')
            return redirect(url_for('main.incoming_requests'))
        elif 'decline' in request.form:
            exchange_request.status = 'declined'
            db.session.commit()

            # Create a notification
            notification = Notification(
                message=f'{current_user.username} has declined your exchange request.',
                user_id=exchange_request.from_user_id,
                link=url_for('main.sent_requests')
            )
            db.session.add(notification)
            db.session.commit()

            flash('You have declined the exchange request.', 'info')
            return redirect(url_for('main.incoming_requests'))

    return render_template('select_books.html', form=form, exchange_request=exchange_request, offered_books=offered_books)

@main.route('/responses')
@login_required
def responses():
    requests = ExchangeRequest.query.filter_by(
        from_user_id=current_user.id
    ).filter(ExchangeRequest.status == 'responded').all()
    return render_template('responses.html', requests=requests)

@main.route('/confirm_exchange/<int:request_id>', methods=['GET', 'POST'])
@login_required
def confirm_exchange(request_id):
    exchange_request = ExchangeRequest.query.get_or_404(request_id)
    if exchange_request.from_user != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.outgoing_requests'))

    if exchange_request.status != 'responded':
        flash('This exchange request is not ready for confirmation.', 'info')
        return redirect(url_for('main.outgoing_requests'))

    form = ConfirmExchangeForm()
    # Populate choices for the RadioField
    form.selected_book.choices = [
        (book.id, f"{book.title} by {book.author}") for book in exchange_request.selected_books
    ]

    if form.validate_on_submit():
        if form.confirm.data:
            selected_book_id = form.selected_book.data
            selected_book = Book.query.get_or_404(selected_book_id)

            # Swap ownership of the books
            exchange_request.book_requested.owner_id = current_user.id
            selected_book.owner_id = exchange_request.to_user_id

            # Mark books as unavailable
            exchange_request.book_requested.is_available = False
            selected_book.is_available = False

            exchange_request.status = 'accepted'
            db.session.commit()

            flash('Exchange completed successfully!', 'success')
            return redirect(url_for('main.history'))
        elif form.decline.data:
            exchange_request.status = 'declined'
            db.session.commit()
            flash('You have declined the exchange.', 'info')
            return redirect(url_for('main.responses'))

    return render_template('confirm_exchange.html', exchange_request=exchange_request, form=form)

@main.route('/search', methods=['GET', 'POST'])
@login_required
def search_books():
    form = SearchForm()
    books = []
    if form.validate_on_submit():
        query = form.query.data
        books = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%')) |
            (Book.genre.name.ilike(f'%{query}%'))
        ).filter(Book.owner_id != current_user.id, Book.is_available == True).all()
        return render_template('books.html', books=books, form=form)
    else:
        return redirect(url_for('main.books'))


@main.route('/discover')
@login_required
def discover():
    # Get the user's favorite genres
    favorite_genres = current_user.genres  # This should be a list of Genre objects

    if favorite_genres:
        # Get the genre IDs
        favorite_genre_ids = [genre.id for genre in favorite_genres]
        # Query books that match the favorite genres and are not owned by the user
        recommended_books = Book.query.filter(
            Book.genre_id.in_(favorite_genre_ids),
            Book.owner_id != current_user.id,
            Book.is_available == True
        ).all()
    else:
        recommended_books = []

    # Get recently added books
    recent_books = Book.query.filter(
        Book.owner_id != current_user.id,
        Book.is_available == True
    ).order_by(Book.id.desc()).limit(10).all()

    # Get popular books based on exchange requests
    popular_books = db.session.query(
        Book, db.func.count(ExchangeRequest.id).label('request_count')
    ).outerjoin(ExchangeRequest, ExchangeRequest.book_requested_id == Book.id)\
    .filter(Book.owner_id != current_user.id, Book.is_available == True)\
    .group_by(Book.id)\
    .order_by(db.desc('request_count'))\
    .limit(10)\
    .all()

    return render_template(
        'discover.html',
        recommended_books=recommended_books,
        recent_books=recent_books,
        popular_books=popular_books
    )



@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    editing = request.args.get('edit') == 'true'
    form = ProfileForm()
    genres = Genre.query.all()
    form.genres.choices = [(genre.id, genre.name) for genre in genres]

    if request.method == 'POST' and form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
        current_user.genres = selected_genres
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('main.profile'))

    if editing:
        # Pre-populate the form fields with current user data
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.genres.data = [genre.id for genre in current_user.genres]

    return render_template('profile.html', form=form, editing=editing)


@main.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    # Mark notifications as read
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifications)


@main.route('/sent_requests')
@login_required
def sent_requests():
    sent_requests = ExchangeRequest.query.filter_by(
        from_user_id=current_user.id,
        status='pending'
    ).all()
    return render_template('sent_requests.html', sent_requests=sent_requests)


@main.route('/history')
@login_required
def history():
    # Fetch accepted exchanges involving the current user
    exchanges = ExchangeRequest.query.filter(
        ExchangeRequest.status == 'accepted',
        (ExchangeRequest.from_user_id == current_user.id) | (ExchangeRequest.to_user_id == current_user.id)
    ).all()
    return render_template('history.html', exchanges=exchanges)


@main.route('/exchange/<int:exchange_id>')
@login_required
def exchange_details(exchange_id):
    exchange = ExchangeRequest.query.get_or_404(exchange_id)
    if current_user.id not in [exchange.from_user_id, exchange.to_user_id]:
        flash('You are not authorized to view this exchange.', 'danger')
        return redirect(url_for('main.history'))
    return render_template('exchange_details.html', exchange=exchange)


@main.route('/remove_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def remove_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.owner != current_user:
        flash('You are not authorized to remove this book.', 'danger')
        return redirect(url_for('main.my_books'))

    # Check if the book is involved in pending exchanges
    pending_requests = ExchangeRequest.query.filter(
        (ExchangeRequest.book_requested_id == book.id) |
        (ExchangeRequest.book_offered_id == book.id)
    ).filter(ExchangeRequest.status == 'pending').all()

    if pending_requests:
        flash('This book is involved in pending exchange requests and cannot be removed.', 'warning')
        return redirect(url_for('main.my_books'))

    # Remove the book
    db.session.delete(book)
    db.session.commit()
    flash('Book removed successfully.', 'success')
    return redirect(url_for('main.my_books'))


@main.route('/book/<int:book_id>/chat', methods=['GET', 'POST'])
@login_required
def book_chat(book_id):
    book = Book.query.get_or_404(book_id)
    messages = Message.query.filter_by(book_id=book.id).order_by(Message.timestamp.asc()).all()
    form = MessageForm()
    
    if form.validate_on_submit():
        content = form.message.data
        message = Message(content=content, user_id=current_user.id, book_id=book.id)
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('main.book_chat', book_id=book.id))
    
    return render_template('book_chat.html', book=book, messages=messages, form=form)




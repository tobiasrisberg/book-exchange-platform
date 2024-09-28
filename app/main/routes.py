from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_required, current_user
from app.models import Book, ExchangeRequest, User, Genre
from app import db
from app.utils import get_book_details
from app.forms import (
    AddBookForm,
    ExchangeRequestForm,
    SelectBooksForm,
    ConfirmExchangeForm,
    SearchForm,
    ProfileForm,
)

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('home.html')


@main.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        isbn = form.isbn.data
        book_details = get_book_details(isbn)
        if book_details:
            new_book = Book(
                title=book_details['title'],
                author=book_details['author'],
                genre=book_details['genre'],
                isbn=isbn,
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
    books = Book.query.filter_by(owner_id=current_user.id).all()
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
            (Book.genre.ilike(f'%{query}%'))
        ).filter(Book.owner_id != current_user.id).all()
    else:
        books = Book.query.filter(Book.owner_id != current_user.id).all()
    return render_template('books.html', books=books, form=form)


@main.route('/book/<int:book_id>')
@login_required
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    form = ExchangeRequestForm()
    return render_template('book_details.html', book=book, form=form)


@main.route('/request_exchange/<int:book_id>', methods=['POST'])
@login_required
def request_exchange(book_id):
    form = ExchangeRequestForm()
    if form.validate_on_submit():
        book = Book.query.get_or_404(book_id)
        if book.owner == current_user:
            flash("You cannot request an exchange for your own book.", 'warning')
            return redirect(url_for('main.book_details', book_id=book_id))

        existing_request = ExchangeRequest.query.filter_by(
            from_user_id=current_user.id,
            to_user_id=book.owner_id,
            book_requested_id=book.id,
            status='pending'
        ).first()

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
    if exchange_request.to_user != current_user:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.incoming_requests'))

    if exchange_request.status != 'pending':
        flash('This exchange request has already been responded to.', 'info')
        return redirect(url_for('main.incoming_requests'))

    user_a_books = Book.query.filter_by(owner_id=exchange_request.from_user_id).all()

    form = SelectBooksForm()
    # Populate choices for the SelectMultipleField
    form.selected_books.choices = [
        (book.id, f"{book.title} by {book.author}") for book in user_a_books
    ]

    if form.validate_on_submit():
        selected_book_ids = form.selected_books.data
        if not selected_book_ids:
            flash('You must select at least one book.', 'warning')
            return redirect(url_for('main.select_books', request_id=request_id))

        selected_books = Book.query.filter(Book.id.in_(selected_book_ids)).all()
        exchange_request.selected_books.extend(selected_books)
        exchange_request.status = 'responded'
        db.session.commit()

        flash('Your selection has been sent to the requester.', 'success')
        return redirect(url_for('main.incoming_requests'))

    return render_template('select_books.html', exchange_request=exchange_request, form=form)

@main.route('/outgoing_requests')
@login_required
def outgoing_requests():
    requests = ExchangeRequest.query.filter_by(from_user_id=current_user.id).filter(
        ExchangeRequest.status.in_(['responded', 'accepted', 'declined'])
    ).all()
    return render_template('outgoing_requests.html', requests=requests)

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

            exchange_request.status = 'accepted'
            db.session.commit()

            flash('Exchange completed successfully!', 'success')
            return redirect(url_for('main.outgoing_requests'))
        elif form.decline.data:
            exchange_request.status = 'declined'
            db.session.commit()
            flash('You have declined the exchange.', 'info')
            return redirect(url_for('main.outgoing_requests'))

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
            (Book.genre.ilike(f'%{query}%'))
        ).filter(Book.owner_id != current_user.id).all()
        return render_template('books.html', books=books, form=form)
    else:
        return redirect(url_for('main.books'))


@main.route('/discover')
@login_required
def discover():
    # Fetch user's favorite genres
    favorite_genres = [genre.strip() for genre in current_user.favorite_genres.split(',')]
    # Query books that match favorite genres and are not owned by the user
    recommended_books = Book.query.filter(
        Book.genre.in_(favorite_genres),
        Book.owner_id != current_user.id
    ).all()
    # Get recently added books
    recent_books = Book.query.filter(
        Book.owner_id != current_user.id
    ).order_by(Book.id.desc()).limit(10).all()
    # (Optional) Get popular books based on exchange requests
    popular_books = db.session.query(
        Book, db.func.count(ExchangeRequest.id).label('request_count')
    ).join(ExchangeRequest, ExchangeRequest.book_requested_id == Book.id)\
    .filter(Book.owner_id != current_user.id)\
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
    form = ProfileForm(obj=current_user)
    genres = Genre.query.all()
    form.genres.choices = [(genre.id, genre.name) for genre in genres]

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
        current_user.genres = selected_genres
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('main.profile'))

    # Pre-select the user's genres
    form.genres.data = [genre.id for genre in current_user.genres]

    return render_template('profile.html', form=form)



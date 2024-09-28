# remove_incorrect_genres.py

from app import create_app, db
from app.models import Genre, Book, User

app = create_app()
with app.app_context():
    # Replace with the names of the incorrect genres
    incorrect_genre_names = ['Science Fiction', 'Mystery', 'Horror', 'Fantasy', 'Romance', 'Non-fiction', 'Historical', 'Thriller', 'Biography', 'Classics']
    
    for genre_name in incorrect_genre_names:
        genre = Genre.query.filter_by(name=genre_name).first()
        if genre:
            # Reassign books to a default genre or set genre_id to None
            books = Book.query.filter_by(genre_id=genre.id).all()
            for book in books:
                # Optionally, assign to a default genre
                book.genre_id = None  # or book.genre_id = default_genre.id
            # Remove genre from users
            users = User.query.filter(User.genres.contains(genre)).all()
            for user in users:
                user.genres.remove(genre)
            # Delete the genre
            db.session.delete(genre)
    db.session.commit()
    print("Incorrect genres removed.")

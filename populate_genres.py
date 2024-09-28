# populate_genres.py

from app import create_app, db
from app.models import Genre

app = create_app()
with app.app_context():
    genre_list = [
        'Philosophy', 'Poetry', 'Science', 'Juvenile Fiction', 'Drama',
        'Fiction', 'Cooking', 'Art', 'Biography & Autobiography', 'History'
    ]
    for name in genre_list:
        if not Genre.query.filter_by(name=name).first():
            genre = Genre(name=name)
            db.session.add(genre)
    db.session.commit()
    print("Genres populated.")

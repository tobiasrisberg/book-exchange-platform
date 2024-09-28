# Run this script once to populate genres
from app import create_app, db
from app.models import Genre

app = create_app()
with app.app_context():
    genre_list = [
        'Biography & Autobiography', 'Fiction', 'Juvenile Fiction', 'Quantum theory', 'Dwarfs (Folklore)',
        'Adventure stories', 'Science', 'History', 'Poetry', 'Philosophy'
    ]
    for name in genre_list:
        if not Genre.query.filter_by(name=name).first():
            genre = Genre(name=name)
            db.session.add(genre)
    db.session.commit()
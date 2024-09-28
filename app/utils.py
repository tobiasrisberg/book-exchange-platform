import requests

def get_book_details(isbn):
    url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data:
            book_info = data['items'][0]['volumeInfo']
            title = book_info.get('title', 'No Title')
            authors = ', '.join(book_info.get('authors', ['Unknown Author']))
            genres = book_info.get('categories', ['Unknown Genre'])
            genre = genres[0] if genres else 'Unknown Genre'
            image_links = book_info.get('imageLinks', {})
            image_url = image_links.get('thumbnail', '')
            return {
                'title': title,
                'author': authors,
                'genre': genre,
                'image_url': image_url
            }
    return None

import requests

def get_book_details(isbn):
    api_url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
    response = requests.get(api_url)
    data = response.json()
    if 'items' in data:
        volume_info = data['items'][0]['volumeInfo']
        title = volume_info.get('title')
        authors = volume_info.get('authors', [])
        genres = volume_info.get('categories', [])
        return {
            'title': title,
            'author': ', '.join(authors),
            'genre': ', '.join(genres)
        }
    else:
        return None
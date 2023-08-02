import os
import requests
from urllib.parse import urlparse


def get_file_extension(url):
    file_url_path, file_extension = os.path.splitext(urlparse(url).path)
    return file_extension


def save_picture(url, pathname, name):
    response = requests.get(url)
    response.raise_for_status()
    os.makedirs(pathname, exist_ok=True)
    with open(f'{pathname}/{name}{get_file_extension(url)}', 'wb') as file:
        file.write(response.content)

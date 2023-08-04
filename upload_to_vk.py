import os
from random import randint

import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

VK_API_URL = 'https://api.vk.com/method/'
XKCD_COMICS_COUNT = 2811


def get_file_extension(url):
    file_url_path, file_extension = os.path.splitext(urlparse(url).path)
    return file_extension


def save_picture(url, name):
    response = requests.get(url)
    response.raise_for_status()
    with open(f'{name}{get_file_extension(url)}', 'wb') as file:
        file.write(response.content)
    return f'{name}{get_file_extension(url)}'


def get_comic(page):
    response = requests.get(f'https://xkcd.com/{page}/info.0.json')
    response.raise_for_status()
    comic = response.json()
    picture_filename = save_picture(comic['img'], comic['title'])
    return {'picture_file': picture_filename, 'picture_text': comic['alt']}


if __name__ == '__main__':
    load_dotenv()
    group_id = os.getenv('VK_GROUP_ID')
    vk_token = os.getenv('VK_APP_TOKEN')

    picture = get_comic(randint(1, XKCD_COMICS_COUNT))

    vk_parameters = {'access_token': vk_token, 'v': 5.131, 'group_id': group_id}
    wall_upload_server_response = requests.get(f'{VK_API_URL}photos.getWallUploadServer', params=vk_parameters)
    wall_upload_server_response.raise_for_status()
    upload_url = wall_upload_server_response.json()['response']['upload_url']

    with open(picture['picture_file'], 'rb') as picture_file:
        upload_files = {'photo': picture_file}
        upload_response = requests.post(upload_url, files=upload_files)
    upload_response.raise_for_status()
    upload_parameters = upload_response.json()
    save_wall_photo_parameters = {'photo': upload_parameters['photo'],
                                  'server': upload_parameters['server'],
                                  'hash': upload_parameters['hash']}
    save_wall_photo_response = requests.post(f'{VK_API_URL}photos.saveWallPhoto',
                                             params=(save_wall_photo_parameters | vk_parameters))
    save_wall_photo_response.raise_for_status()
    attachments_parameters = save_wall_photo_response.json()["response"][0]
    post_parameters = {'owner_id': f'-{group_id}',
                       'from_group': 1,
                       'message': picture['picture_text'],
                       'attachments': f'photo{attachments_parameters["owner_id"]}_{attachments_parameters["id"]}'}
    post_response = requests.post(f'{VK_API_URL}wall.post', params=(post_parameters | vk_parameters))
    os.remove(picture["picture_file"])
    post_response.raise_for_status()

import os
from random import randint

import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

VK_API_URL = 'https://api.vk.com/method/'
XKCD_COMICS_COUNT = 2811


class VKResponseError(TypeError):
    pass


def read_vk_response(self):
    if 'error' in self.json():
        raise VKResponseError('Response returned with Error')
    if 'photo' in self.json():
        if self.json()['photo'] == '[]':
            raise VKResponseError('No photo to upload')


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


def get_server_url_to_upload(params):
    wall_upload_server_response = requests.get(f'{VK_API_URL}photos.getWallUploadServer', params=params)
    wall_upload_server_response.raise_for_status()
    try:
        read_vk_response(wall_upload_server_response)
        return wall_upload_server_response.json()['response']['upload_url']
    except VKResponseError:
        os.remove(picture["picture_file"])
        return exit('get_server_url_to_upload returned with Error')


def upload_comic_to_server(params):
    with open(picture['picture_file'], 'rb') as picture_file:
        upload_files = {'photo': picture_file}
        upload_response = requests.post(params, files=upload_files)
    upload_response.raise_for_status()
    os.remove(picture["picture_file"])
    try:
        read_vk_response(upload_response)
        upload_parameters = upload_response.json()
        return {'photo': upload_parameters['photo'],
                'server': upload_parameters['server'],
                'hash': upload_parameters['hash']}
    except VKResponseError:
        return exit('upload_comic_to_server returned that nothing to upload')


def save_comic(params):
    save_wall_photo_response = requests.post(f'{VK_API_URL}photos.saveWallPhoto', params=params)
    save_wall_photo_response.raise_for_status()
    try:
        read_vk_response(save_wall_photo_response)
        attachments_parameters = save_wall_photo_response.json()["response"][0]
        return {'owner_id': f'-{group_id}',
                'from_group': 1,
                'message': picture['picture_text'],
                'attachments': f'photo{attachments_parameters["owner_id"]}_{attachments_parameters["id"]}'}
    except VKResponseError:
        return exit('save_comic returned with Error')


def post_comic_in_vk_wall(params):
    post_response = requests.post(f'{VK_API_URL}wall.post', params=params)
    post_response.raise_for_status()
    try:
        read_vk_response(post_response)
    except VKResponseError:
        return exit('post_comic_in_vk_wall returned with Error')


if __name__ == '__main__':
    load_dotenv()
    group_id = os.environ['VK_GROUP_ID']
    vk_token = os.environ['VK_APP_TOKEN']
    picture = get_comic(randint(1, XKCD_COMICS_COUNT))
    vk_parameters = {'access_token': vk_token, 'v': 5.131, 'group_id': group_id}
    params_to_upload = get_server_url_to_upload(vk_parameters)
    save_comic_params = upload_comic_to_server(params_to_upload) | vk_parameters
    post_comic_params = save_comic(save_comic_params) | vk_parameters
    post_comic_in_vk_wall(post_comic_params)

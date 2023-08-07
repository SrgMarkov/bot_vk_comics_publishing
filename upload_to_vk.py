import os
from random import randint
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse


VK_API_URL = 'https://api.vk.com/method/'
VK_API_VERSION = 5.131
XKCD_COMICS_COUNT = 2811
PUBLICATION_FROM_GROUP = 1


class VKResponseError(TypeError):
    pass


def check_vk_response(self):
    vk_response = self.json()
    if 'error' in vk_response:
        error_msg = f'Error {vk_response["error"]["error_code"]}: {vk_response["error"]["error_msg"]}'
        raise VKResponseError(error_msg)
    if 'photo' in vk_response:
        if self.json()['photo'] == '[]':
            error_msg = 'upload_comic_to_server returned that nothing to upload'
            raise VKResponseError(error_msg)


def get_file_extension(url):
    file_url_path, file_extension = os.path.splitext(urlparse(url).path)
    return file_extension


def save_picture(url, name):
    response = requests.get(url)
    response.raise_for_status()
    with open(f'{name}{get_file_extension(url)}', 'wb') as file:
        file.write(response.content)
    return f'{name}{get_file_extension(url)}'


def get_comic(issue_number):
    response = requests.get(f'https://xkcd.com/{issue_number}/info.0.json')
    response.raise_for_status()
    comic = response.json()
    return save_picture(comic['img'], comic['title']), comic['alt']


def get_server_url_to_upload(token, group):
    vk_parameters = {'access_token': token, 'v': VK_API_VERSION, 'group_id': group}
    wall_upload_server_response = requests.get(f'{VK_API_URL}photos.getWallUploadServer', params=vk_parameters)
    wall_upload_server_response.raise_for_status()
    check_vk_response(wall_upload_server_response)
    return wall_upload_server_response.json()['response']['upload_url']


def upload_comic_to_server(url, picture_file):
    with open(picture_file, 'rb') as file_to_upload:
        upload_files = {'photo': file_to_upload}
        upload_response = requests.post(url, files=upload_files)
    upload_response.raise_for_status()
    check_vk_response(upload_response)
    upload_parameters = upload_response.json()
    return upload_parameters['photo'], upload_parameters['server'], upload_parameters['hash']


def save_comic(token, group, photo, server, server_hash):
    save_comic_parameters = {'access_token': token,
                             'v': VK_API_VERSION,
                             'group_id': group,
                             'photo': photo,
                             'server': server,
                             'hash': server_hash}
    save_wall_photo_response = requests.post(f'{VK_API_URL}photos.saveWallPhoto', params=save_comic_parameters)
    save_wall_photo_response.raise_for_status()
    check_vk_response(save_wall_photo_response)
    attachments_parameters = save_wall_photo_response.json()["response"][0]
    return f'photo{attachments_parameters["owner_id"]}_{attachments_parameters["id"]}'


def post_comic_in_vk_wall(token, group, message, attachments):
    post_parameters = {'access_token': token,
                       'v': VK_API_VERSION,
                       'group_id': group,
                       'owner_id': f'-{group_id}',
                       'from_group': PUBLICATION_FROM_GROUP,
                       'message': message,
                       'attachments': attachments}
    post_response = requests.post(f'{VK_API_URL}wall.post', params=post_parameters)
    post_response.raise_for_status()
    check_vk_response(post_response)


if __name__ == '__main__':
    load_dotenv()
    group_id = os.environ['VK_GROUP_ID']
    vk_token = os.environ['VK_APP_TOKEN']
    comic_file, comic_text = get_comic(randint(1, XKCD_COMICS_COUNT))
    try:
        upload_url = get_server_url_to_upload(vk_token, group_id)
        saving_photo, server_to_save, hash_to_save = upload_comic_to_server(upload_url, comic_file)
        post_attachments = save_comic(vk_token, group_id, saving_photo, server_to_save, hash_to_save)
        post_comic_in_vk_wall(vk_token, group_id, comic_text, post_attachments)
    except VKResponseError as error:
        print(error)
    finally:
        os.remove(comic_file)

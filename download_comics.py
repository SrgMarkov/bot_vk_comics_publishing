import argparse
import requests
from save_pictures import save_picture


def get_comics(count):
    for page in range(1, count + 1):
        response = requests.get(f'https://xkcd.com/{page}/info.0.json')
        response.raise_for_status()
        comic = response.json()
        save_picture(comic['img'], 'images', comic['title'])


if __name__ == '__main__':
    command_arguments = argparse.ArgumentParser\
        (description='Загрузка комиксов')
    command_arguments.add_argument('count', help='Количество комиксов', type=int)
    args = command_arguments.parse_args()
    get_comics(args.count)


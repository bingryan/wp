import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'images')


def get_sys_json():
    with open(os.path.join(BASE_DIR, 'wallpaper.json')) as f:
        data = f.readline().split('\001')
        if len(data) > 0:
            return data


def list_images_name():
    for _, _, files in os.walk(IMAGE_DIR):
        return files


def get_random_image_path():
    images = list_images_name()
    images_len = len(images)
    return os.path.join(IMAGE_DIR, images[random.randint(1, images_len - 1)])


def get_random_wallpaper_url():
    urls = get_sys_json()
    urls_len = len(get_sys_json())
    if urls_len < 1:
        return
    return [urls[random.randint(1, urls_len)]]


def get_random_wallpaper_urls(nums):
    urls = get_sys_json()
    urls_len = len(get_sys_json())
    if urls_len < 1:
        return
    if urls_len < nums:
        return urls
    return random.sample(urls, nums)


def _closest_file(file_name='wallpaper.json', path='.', prev_path=None):
    """
    return the path  of the closest wallpaper.json file
    """
    if path == prev_path:
        return ''

    path = os.path.abspath(path)
    settings_file = os.path.join(path, file_name)
    if os.path.exists(settings_file):
        return settings_file
    return _closest_file(file_name=file_name, path=os.path.dirname(path), prev_path=path)


if __name__ == '__main__':
    print(get_random_wallpaper_url()[0])

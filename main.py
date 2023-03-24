import shutil
import requests
import os
import random
from dotenv import load_dotenv
from pprint import pprint


def download_image(filename, url, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()
    path = os.path.join("comics", filename)
    os.makedirs('comics', exist_ok=True)
    with open(path, 'wb') as file:
        file.write(response.content)


def get_comic():
    filename = 'comic_current.png'
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    response_content = response.json()
    comic_number = response_content['num']
    random_url = f'https://xkcd.com/{random.randint(1, comic_number)}/info.0.json'
    response = requests.get(random_url)
    response.raise_for_status()
    response_content = response.json()
    img_url = response_content['img']
    download_image(filename, img_url)
    return response_content["alt"]


def get_upload_server(access_token, group_id):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {'v': '5.131', 'access_token': access_token, 'group_id': group_id}
    response = requests.get(url, params=payload)
    response_content = response.json()
    response.raise_for_status()
    print(response_content)
    return response_content['response']['upload_url']


def upload_comics(upload_url):
    comic_path = 'comics\comic_current.png'
    with open(comic_path, 'rb') as photo:
        files = {
            'photo': photo
        }
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    response_content = response.json()
    return response_content['hash'], response_content['server'], response_content['photo']


def save_comics_to_group_album(access_token, photo_hash, photo_server, photo, group_id):
    payload = {'v': '5.131', 'access_token': access_token, 'group_id': group_id, 'hash': photo_hash, 'server': photo_server, 'photo': photo}
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url, params=payload)
    response.raise_for_status()
    response_content = response.json()
    return response_content['response'][0]['id'], response_content['response'][0]['owner_id']


def publish_comic(access_token, group_id, owner_id, media_id, comic_alt):
    payload =  {
        'access_token': access_token,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': comic_alt,
        'attachments': f'photo{owner_id}_{media_id}',
        'v': '5.131'
    }
    url = 'https://api.vk.com/method/wall.post'
    response = requests.post(url, params=payload)
    response.raise_for_status()
    response_content = response.json()


if __name__ == "__main__":
    load_dotenv()
    access_token = os.environ["VK_ACCESS_TOKEN"]
    group_id = os.environ["VK_GROUP_ID"]
    try:
        comic_alt = get_comic()
        upload_url = get_upload_server(access_token, group_id)
        photo_hash, photo_server, photo = upload_comics(upload_url)
        media_id, owner_id = save_comics_to_group_album(access_token, photo_hash, photo_server, photo, group_id)
        publish_comic(access_token, group_id, owner_id, media_id, comic_alt)
    except requests.exceptions.HTTPError:
        print('Ошибка запроса!!')
    finally:
        shutil.rmtree('comics')
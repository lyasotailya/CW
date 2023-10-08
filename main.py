import json
from urllib.parse import urlencode
import requests
from progress.bar import IncrementalBar

my_id = input('Укажите id вашего профиля ВК: ')
ya_token = input('Укажите токен Яндекс.Диска: ')
type_photo = input('Укажите идентификатор альбома, где: "wall" — фотографии со стены, "profile" — фотографии профиля, '
                   '"saved" — сохраненные фотографии: ')

# Получение токена ВК


def get_vk_token() -> str:
    url = 'https://oauth.vk.com/authorize/'
    params = {
        'client_id': '51755559',
        'redirect_uri': 'https://oauth.vk.com/blank.html',
        'display': 'page',
        'scope': 'photos',
        'response_type': 'token',
    }
    return f'{url}?{urlencode(params)}'


vk_token = input('Укажите токен ВКонтакте, если он у вас есть, если нет, напишите "absent" ')
if vk_token == 'absent':
    print('Перейдите по указанной ссылке, скопируйте токен и вставьте ниже', get_vk_token(),  sep="\n")
    vk_token = input('Ваш токен: ')


class VK:
    base_url = 'https://api.vk.com/method'

    def __init__(self, vk_token, user_id):
        self.token = vk_token
        self.id = user_id

    def get_params(self) -> dict:
        return {
            'access_token': self.token,
            'v': '5.131'
        }

    def get_photos(self) -> json:
        params = self.get_params()
        params.update({'album_id': type_photo, 'extended': 1})
        response = requests.get(f'{self.base_url}/photos.get', params=params)
        return response.json()


# Получение фотографии

file1 = VK(vk_token, my_id).get_photos()
all_count_photos = VK(vk_token, my_id).get_photos().get('response', '').get('count', '')


# Указание колличества фотографий
def check_count_photos(count_photos: str) -> int:
    if all_count_photos == 0:
        print('Кол-во фотографий в альбоме: 0')
        return all_count_photos

    elif (count_photos.isdigit() and
          0 < int(count_photos) <= all_count_photos):
        return int(count_photos)

    elif (count_photos.isdigit() and
          not 0 < int(count_photos) <= all_count_photos and
          all_count_photos >= 5):
        print('Некорректный ввод, число превышает кол-во фотографий в альбоме, '
              'выставленно число фотографий по умолчанию: 5')
        return 5

    else:
        if not count_photos.isdigit() and all_count_photos >= 5:
            print('Некорректный ввод, выставленно число фотографий по умолчанию: 5')
            return 5

        elif not count_photos.isdigit() and all_count_photos < 5:
            print('Некорректный ввод, выставленно общее число фотографий: ', count_photos)
            return all_count_photos


count_photos = input(f'Укажите желаемое число сохраняемых фотографий (всего фото в альбоме: {all_count_photos}): ')
check_count_photos(count_photos)

# Создание папки Яндекс диска
ya_url = 'https://cloud-api.yandex.net'


def create_folder(_folder_name: str) -> str or int:
    _params = {
        'path': _folder_name
    }
    url_for_create_folder = ya_url + '/v1/disk/resources'

    responce = requests.put(url_for_create_folder,
                            headers={'Authorization': ya_token},
                            params=_params)

    if 200 <= responce.status_code < 300:
        return responce.json().get('href', '')
    elif responce.status_code == 409:
        return 'Папка с таким именем существует'
    else:
        return responce.status_code


folder_name = input('Укажите название папки для ее создания на ЯД (имя должно быть уникально): ')
create_folder(folder_name)


# Загрузка фотографий на ЯД
def send_on_ya():
    url_for_get_link = ya_url + '/v1/disk/resources/upload'
    information_about_photos = []

    bar = IncrementalBar('Countdown', max=check_count_photos(count_photos))

    for i in range(check_count_photos(count_photos)):
        bar.next()

        photo = file1.get('response', '').get('items', '')[i]
        date = str(photo.get('date', ''))

        likes = photo.get('likes', '').get('count', '')
        photo_name = str(likes) + '.jpg'

        size = photo.get('sizes', '')[-1].get('type', '')

        photo_url_for_load = photo.get('sizes', '')[-1].get('url', '')  # Ссылка на фото
        photo_byte = requests.get(photo_url_for_load).content

        info = {}
        info.setdefault('file_name', photo_name)
        info.setdefault('size', size)
        information_about_photos.append(info)

        for j in range(i):
            if file1['response']['items'][j]['likes']['count'] == likes:
                photo_name = str(likes) + '_' + date + '.jpg'
                break

        params = {
            'path': folder_name + '/' + photo_name
        }

        response = requests.get(url_for_get_link,
                                params=params,
                                headers={'Authorization': ya_token})

        url_upload = response.json().get('href', '')  # Ссылка, куда загружать

        response = requests.put(url_upload, files=[('file', photo_byte)])

    bar.finish()

    with open('json.json', 'w', encoding='utf-8') as f:
        json.dump(information_about_photos, f, indent=2)


send_on_ya()

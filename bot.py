import datetime

import vk_api
from vk_api.exceptions import ApiError
import os
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from dotenv import load_dotenv
from random import randrange

from vk_api.longpoll import VkLongPoll, VkEventType

load_dotenv()

# загружаем данные из переменной окружения .env
token = os.getenv('token')
VKtoken = os.getenv('VKtoken')

vk = vk_api.VkApi(token=token)
vk_session = vk_api.VkApi(token=VKtoken)
vk_request = vk_session.get_api()


def write_msg(user_vk_id: str or int, message: str, attachment=None, keyboard=None) -> dict:
    """ Функция отправляет сообщение через VK API указанному пользователю VK """

    params = {
        'user_id': user_vk_id,
        'message': message,
        'random_id': randrange(10 ** 7),
    }

    if attachment is not None and isinstance(attachment, str):
        params['attachment'] = attachment
    if keyboard is not None and isinstance(keyboard, vk_api.keyboard.VkKeyboard):
        params['keyboard'] = keyboard.get_keyboard()

    response = vk.method('messages.send', params)

    if isinstance(response, int):
        return {'result': True, 'id_msg': response}
    else:
        return {'result': False, 'error': response}


def get_user_info(user_vk_id: str or int) -> dict:
    """ Функция позволяет получить данные пользователя VK, используя метод
    VK API users.get. (имя, фамилия, пол, город). """

    params = {'user_ids': f'{user_vk_id}',
              'fields': 'bdate, sex, city'
              }
    try:
        response = vk_request.users.get(**params)
    except ApiError as error:
        print(error)
    first_name = response[0].get('first_name')
    last_name = response[0].get('last_name')
    city = response[0].get('city')
    if city is not None:
        city = city.get('id')
    else:
        city = None
    gender = response[0].get('sex')
    current_date = datetime.datetime.now()
    bdate_str = response[0].get('bdate')
    if bdate_str is not None:
        bdate = datetime.datetime.strptime(bdate_str, '%d.%m.%Y')
        age = current_date.year - bdate.year
    else:
        age = None

    user_info = {
        'first_name': first_name,
        'last_name': last_name,
        'city_id': city,
        'gender': gender,
        'age': age
    }

    return user_info


def user_search(user_vk_id: str or int, city: int, age: int, offset=1) -> list:
    """ Функция позволяет получить список словарей с данными пользователей по указанным параметрам, используя метод """

    info_user = get_user_info(user_vk_id)
    if info_user.get('sex') == 1:
        sex = 2
    else:
        sex = 1
    params = {
        'sort': 0,
        'status': 6,
        'has_foto': 1,
        'city': city,
        'sex': sex,
        'age_from': age - 2,
        'age_to': age + 2,
        'fields': 'bdate, sex',
        'count': 50,
        'offset': offset
    }
    try:
        response = vk_request.users.search(**params)
    except ApiError as error:
        print(error)
    return response.get('items')


def get_user_photos(user_vk_id: str or int) -> list:
    """ Функция позволяет получить фотографии указанного профиля VK, с помощью метода VK API photos.get """

    params = {
        'owner_id': f'{user_vk_id}',
        'album_id': 'profile',
        'rev': 0,
        'extended': 1,
    }

    response = vk_request.photos.get(**params)
    likes_ids_list = []
    try:
        for photos in response.get('items'):
            for photo in photos.get('sizes'):
                if 'm' in photo.get('type'):
                    likes_ids = {'like': (photos.get('likes').get('count')),
                                 'photo_id': (photos.get('id')),
                                 'photo_url': (photo.get('url'))}
                    likes_ids_list.append(likes_ids)
        return sorted(likes_ids_list, key=lambda x: x.get('like'), reverse=True)[:3]
    except AttributeError:
        return likes_ids_list[0:3]


def get_city_id(city_name: str) -> dict:
    params = {
        'q': city_name
    }
    try:
        response = vk_request.database.getCities(**params)
    except ApiError as error:
        print(error)
    info = {}
    for item in response.get('items'):
        info[item['title']] = item['id']
    return info


def ask_city(user_id):
    longpoll = VkLongPoll(vk)
    write_msg(user_vk_id=user_id, message="Из какого вы города ?")
    city = None
    while not city:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.user_id == user_id:
                    city = event.text
                    break
    return city


def ask_age(user_id):
    longpoll = VkLongPoll(vk)
    write_msg(user_vk_id=user_id, message="Напишите свой возраст")
    age = None
    while not age:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.user_id == user_id:
                    age = event.text
                    break
    return age


def handle_user_info(user_id):
    user_info = get_user_info(user_id)

    if user_info.get('city_id') is None:
        city = ask_city(user_id)
        res = get_city_id(city)
        user_info['city_id'] = res.get(city)

    if user_info.get('age') is None:
        age = ask_age(user_id)
        user_info['age'] = age

    return user_info


def greet_user(user_id):
    user_info = handle_user_info(user_id)

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
    write_msg(user_id,
              f"{user_info['first_name']}, рад приветствовать вас!\n"
              f" Для поиска пары нажмите кнопку ниже)",
              keyboard=keyboard)
    return user_info

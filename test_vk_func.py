# -*- coding: utf-8 -*-
import requests
import json
import os
import sys
import vk_api
from vk_api import exceptions
import configparser
import time
import python3_anticaptcha
from python3_anticaptcha import ImageToTextTask, errors
import vk

def captcha_handler(captcha):
    key = ImageToTextTask.ImageToTextTask(anticaptcha_key='79523f546e63d7f59f40650e5651728b', save_format='const') \
            .captcha_handler(captcha_link=captcha.get_url())
    
    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key['solution']['text'])

# Считываем настройки
config_path = os.path.join(sys.path[0], 'settings.ini')
config = configparser.ConfigParser()
config.read(config_path)
LOGIN = config.get('VK', 'LOGIN')
PASSWORD = config.get('VK', 'PASSWORD')
OWNER_ID = config.get('VK', 'OWNER_ID')
DOMAIN = config.get('VK', 'DOMAIN')
COUNT = config.get('VK', 'COUNT')
TIME_TO_SLEEP = int(config.get('VK', 'TIME_TO_SLEEP'))
VK_TOKEN = config.get('VK', 'TOKEN', fallback=None)

# INCLUDE_LINK = config.getboolean('Settings', 'INCLUDE_LINK')
# PREVIEW_LINK = config.getboolean('Settings', 'PREVIEW_LINK')
posted_before = config.get('posted_before','sources')
list_posted_before=posted_before.split()
print('LOGIN==', LOGIN)
print('password==', PASSWORD)
# Получаем данные из vk.com
def get_data(count_vk):
    global LOGIN
    global PASSWORD
    global VK_TOKEN
    global config
    global config_path
    global DOMAIN
    
    # global vk
    if VK_TOKEN is not None:
        # vk_session = vk_api.VkApi(LOGIN, PASSWORD, VK_TOKEN,captcha_handler=captcha_hander)
        vk_session = vk_api.VkApi(LOGIN, PASSWORD, VK_TOKEN, captcha_handler=captcha_handler)
        vk_session.auth(token_only=True)
    else:
        vk_session = vk_api.VkApi(LOGIN, PASSWORD)
        try:
            vk_session.auth()
        except vk_api.AuthError as error_msg:
            print(error_msg)
            return

    new_token = vk_session.token['access_token']
    if VK_TOKEN != new_token:
        VK_TOKEN = new_token
        config.set('VK', 'TOKEN', new_token)
        with open(config_path, "w") as config_file:
            config.write(config_file)

    vk = vk_session.get_api()
    
    response = vk.newsfeed.get(count=COUNT)
# это если пробовать забирать с группы (добрые мемы)
    # response=vk.wall.get(domain=DOMAIN, count=count_vk)
    print('hello, this is response')
    one_line_json = json.dumps(response,indent=2)
    # print(one_line_json)
    original_stdout = sys.stdout    
    # for comfort reading request (with highlighting)
    with open('filename2.py', 'w') as f:
        sys.stdout = f 
        print(one_line_json)
        
        sys.stdout = original_stdout 
        print('Response wrote to file')
    return response

def post_to_group_from_group(ago):
    global VK_TOKEN
    global COUNT
    global vk
    global posted_before
    global list_posted_before
    global TIME_TO_SLEEP
    global OWNER_ID
    print('POSTED_BEFORE on the beginning:::',posted_before)
    my_response = get_data(COUNT)
    cur_timestamp=time.time()
    urls=[]
    for i in range(len(my_response['items'])):
        if 'copy_history' in my_response['items'][i]:
            for k in range(len(my_response['items'][i]['copy_history'])):
                if 'attachments' in my_response['items'][i]['copy_history'][k]:
                    for m in range(len(my_response['items'][i]['copy_history'][k]['attachments'])):                        
                        if 'photo' in my_response['items'][i]['copy_history'][k]['attachments'][m]:                            
                            max_size=0
                            max_size_url=''
                            for c in range(len(my_response['items'][i]['copy_history'][k]['attachments'][m]['photo']['sizes'])):
                                # if 'sizes' in my_response['items'][i]['copy_history'][k]['attachments'][m]:
                                if(my_response['items'][i]['copy_history'][k]['attachments'][m]['photo']['sizes'][c]['height']>max_size):
                                    max_size=my_response['items'][i]['copy_history'][k]['attachments'][m]['photo']['sizes'][c]['height']
                                    max_size_url=my_response['items'][i]['copy_history'][k]['attachments'][m]['photo']['sizes'][c]['url']                                   
                            urls.append(max_size_url ) 
    # print(urls)
    # хотел попробовать постить в группу -161522049, не прикрепляет attachments
    for IMAGE_URL in urls:
        vkapi = vk.API(vk.Session(VK_TOKEN))
        destination = vkapi.photos.getWallUploadServer(v='5.124',group_id=161522049)
        image = requests.get(IMAGE_URL, stream=True)
        data = ("image.jpg", image.raw, image.headers['Content-Type'])
        meta = requests.post(destination['upload_url'], files={'photo': data}).json()
        # me = vkapi.users.get()[0]['uid']
        photo = vkapi.photos.saveWallPhoto(group_id=161522049, v='5.124', **meta)[0]
        vkapi.wall.post(message='photo from dobrye memy',owner_id=-161522049,v='5.124', attachments=photo['id'],access_token= VK_TOKEN)
        print('sleep 3')
    
    time.sleep(60)
    for i in range(int(COUNT)):
                     
            time.sleep(1)           
            OBJECT='wall'+str(my_response['items'][i]['copy_history'][0]['owner_id'])+'_'+str(my_response['items'][i]['copy_history'][0]['attachments'][0]['photo']['post_id'])
            res=requests.post('https://api.vk.com/method/wall.post', data={'object': OBJECT,
                                                                'access_token': VK_TOKEN,
                                                                'owner_id': -161522049, 
                                                                'message': 'test'+str(i),
                                                                'v':"5.52"}).json()
            print('is it posted?????', res)
             
def post_to_wall(ago):
    global VK_TOKEN
    global COUNT
    global vk
    global posted_before
    global list_posted_before
    global TIME_TO_SLEEP
    print('POSTED_BEFORE on the beginning:::',posted_before)
    my_response = get_data(COUNT)
    cur_timestamp=time.time()
    try:
        
        
        for i in range(int(COUNT)):
            
            try:
                if(my_response['items'][i]['source_id']==int(OWNER_ID)):
                    print('SKIP my OWN post\n')
                    continue
                
                if(my_response['items'][i]['date']+ago<cur_timestamp):
                    if(input("Пошли старые посты, прервать постинг? y/n")=='n'):
                        ago+=ago
                        continue
                    else:                         
                        break
            except KeyError:
                print('No key, sough')    
                continue
            except IndexError:
                print("Zakon4ilis items v response\n") 
            # except Exception:
            #     print('Somewthing wrong',Exception)
            #     continue
            try:
                OBJECT='wall'+str(my_response['items'][i]['source_id'])+'_'+str(my_response['items'][i]['post_id'])
            except KeyError:
                print(f'Missed key for {i}')
                continue
            except IndexError:
                print('Index out of range, break')
                break
            if(OBJECT in list_posted_before):
                print("SKIP posts I've posted before\n")
                continue
            try:                
                time.sleep(1)
                res=requests.post('https://api.vk.com/method/wall.repost', data={'access_token': VK_TOKEN,
                                                                                                        # 'post_id':1857743,
                                                                                                        'object':OBJECT,
                                                                                                    #   'owner_id': OWNER_ID,
                                                                                                    #   'from_group': OWNER_ID,
                                                                                                    'message': 'test'+str(i),
                                                                                                    #   'signed': 0,
                                                                                                    'v': "11.9"}).json()
                print('is it posted?????', res)
                if 'error' in res:
                    if res['error']['error_msg']=='Captcha needed':
                        print('caught captcha error\n')
                        print('captcha_sid == ',res['error']['captcha_sid'])
                        print('captcha_img==',res['error']['captcha_img'])
                        ImageToTextTask.ImageToTextTask(anticaptcha_key='79523f546e63d7f59f40650e5651728b', save_format='const') \
                        .captcha_handler(captcha_link=res['error']['captcha_img'])
                        i-=1
                        continue    
                    elif res['error']['error_msg']=='Access to adding post denied: you can only add 50 posts a day':
                        print(f'You achived daily posting limit. Sleep for {TIME_TO_SLEEP} seconds')
                        break
                else:
                    list_posted_before.append(OBJECT)
                    posted_before+=(OBJECT+" ")
                    print('POSTED_BEFORE:::',posted_before)
            except:
                print('I caught something!\n')
                
            
    #  https://anti-captcha.com/
                        # captcha.sid # Получение sid
                        # captcha.get_url() # Получить ссылку на изображение капчи
                        # captcha.get_image() # Получить изображение капчи (jpg)
    finally:
        config.set('posted_before', 'sources',posted_before)
        with open(config_path, "w") as config_file:
            config.write(config_file)
        print('POSTED_BEFORE:::',posted_before)

def main():
    global COUNT
    global TIME_TO_SLEEP
    while(True):
        try:
            post_to_wall(TIME_TO_SLEEP)
            # if input('wall or newsfeed?: (wall/newsfeed)')=='wall':
            #     post_to_wall_from_wall(TIME_TO_SLEEP)
            # else:
            #     post_to_wall(TIME_TO_SLEEP)
            print('sleep for',TIME_TO_SLEEP)
            time.sleep(TIME_TO_SLEEP)
        except KeyboardInterrupt:
            break
if __name__ == '__main__':
    main()

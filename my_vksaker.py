# coding=utf-8
"""Script for download audio from VK"""
import urllib
import vk_api
import getpass

def main():
    """Enter requested information"""
    login, password, owner_id = input('Input your login:'), getpass.getpass('Input your password:'), input('Input your ID:')
    api = vk_api.VkApi(login, password)

    """Check in AuthorizationError"""
    try:
        api.authorization()
    except vk_api.AuthorizationError:
        return error_msg  

    """Get infotmation from response"""      
    vk = api.get_api()
    response = vk.audio.get(owner_id)
    file = urllib.URLopener()

    """Get our audio"""
    for item in response['items']:
        url = item['url']
        artist = item['artist']
        title = item['title']
        name = artist + '_' + title + '.mp3'
        song = artist + ' ' + title + ' ' + url
        file.retrieve(url, name)
        
if __name__ == '__main__':
    main()

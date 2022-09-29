#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import time
from auto_download_photos import QQZone, QQZonePictures

if __name__ == '__main__':
    username = input('>> 输入账号(必填): \r\n  ').strip() or '默认QQ号'
    password = input('>> 输入密码(可以为空, 直接回车): \r\n  ').strip() or '默认密码'
    other_username = input('>> 输入对方账号(空表示下载自己): \r\n  ').strip() or '朋友的QQ号'
    other_username = other_username if other_username else username
    threads_num = input('>> 输入下载线程数(默认4): \r\n  ').strip()
    threads_num = int(threads_num) if threads_num else 4

    print('*' * 60, '\r\n\t\t    即将开始!')
    print('*' * 60)
    time.sleep(2)

    print('>> 1.先模拟登陆获取cookie')
    login = QQZone(username=username, password=password, other_username=other_username)
    cookies, gtk, username = login.login()
    final_ck = ''
    for ck in cookies:
        final_ck += '{}={};'.format(ck['name'], ck['value'])

    spider = QQZonePictures(cookies=final_ck, gtk=gtk, username=username, host_username=other_username, thread_max_num=threads_num)
    spider.main()

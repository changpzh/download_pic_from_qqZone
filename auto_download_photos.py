#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import copy
import json
import math
import time
import datetime
import requests
from tqdm import tqdm
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.status import HTTP_200_OK
from simple_queue import SimpleQueue


def empty(lists):
    return not lists

class QQZone:
    def __init__(self, username=None, password=None, other_username=None):
        self.login_url = 'https://i.qq.com/'
        self.username = username
        self.password = password
        self.other_username = other_username
        self.qzonetoken = None
        self.cookies = None
        self.g_tk = None
        self.headers = {
            'host': 'user.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:66.0) Gecko/20100101 Firefox/66.0',
            'connection': 'keep-alive',
            'referer': 'https://qzone.qq.com/',
        }
        # Chrome下载链接：http://xfxuezhang.cn/web/share/软件-电脑/Chrome.zip
        self.browser_path = r'Chrome/BitBrowser.exe'
        self.driver_path = r'Chrome/chromedriver.exe'

    def driver(self):
        # 有头浏览器的写法
        # driver = uc.Chrome(driver_executable_path=self.driver_path,
        #                     browser_executable_path=self.browser_path,
        #                     suppress_welcome=False)
        driver = uc.Chrome()
        driver.get(self.login_url)

        if self.username and self.password:
            print('>> 提供了账号或密码，进入自动登录模式')
            print('>> 切换到登录表单')
            driver.switch_to.frame('login_frame')
            # 切换到账号密码登录
            log_method = driver.find_element(by=By.ID, value='switcher_plogin')
            log_method.click()
            # 输入账号密码，登录
            print('>> 输入账号中...')
            username = driver.find_element(by=By.ID, value='u')
            username.clear()
            username.send_keys(self.username)
            print('>> 输入密码中...')
            password = driver.find_element(by=By.ID, value='p')
            password.clear()
            password.send_keys(self.password)
            login_button = driver.find_element(by=By.ID, value='login_button')
            login_button.click()
            print('**此处若有滑块验证，请在10s内手动完成！！！**')
            time.sleep(1)
        else:
            print('>> 未提供账号或密码，进入手动登录模式')

        while True:
            try:
                WebDriverWait(driver, 2, 0.5).until(
                    expected_conditions.presence_of_element_located((By.ID, r'aIcenter')))  # 等待个人中心，表示进入了空间
                print('>> 登陆成功!')
                break
            except:
                print('>> 等待手动完成登录中...')
                time.sleep(10)
        driver.switch_to.default_content()

        if self.other_username:
            print('>> 进入好友空间...')
            driver.get(r'https://user.qzone.qq.com/' + self.other_username)
            time.sleep(2)
        self.cookies = driver.get_cookies()
        return driver

    # 生成g_tk
    def get_g_tk(self, driver):
        hashes = 5381
        for letter in driver.get_cookie('p_skey')['value']:
            hashes += (hashes << 5) + ord(letter)
        self.g_tk = hashes & 0x7fffffff
        return self.g_tk

    def login(self):
        print('>> 开始登陆')
        driver = self.driver()
        print('>> 获取g_tk')
        self.get_g_tk(driver)
        print('>> 登录完成')
        driver.close()
        return self.cookies, self.g_tk, self.username


class QQZonePictures:
    def __init__(self, cookies=None, gtk=None, username=None, host_username=None, thread_max_num=4):
        self.cookies = cookies
        self.gtk = gtk
        self.uin = username
        self.hostUin = host_username
        self.thread_max_num = thread_max_num
        self.root = self.mkdir_path("./QQZone/")
        self.file_save_path = None
        self.url_list = 'https://user.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3'
        self.url_photo = 'https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_list_photo?'
        self.header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                      'q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'cookie': self.cookies,
            'pragma': 'no-cache',
            'referer': 'https://user.qzone.qq.com/',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77',
        }

    @staticmethod
    def mkdir_path(path):
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def get_album_info(self):
        param = {
            'g_tk': self.gtk,
            'hostUin': self.hostUin if self.hostUin else self.uin,
            'uin': self.uin,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'pageNumModeSort': '40',
            'pageNumModeClass': '15'
        }
        res = requests.get(self.url_list, headers=self.header, params=param)
        if res.status_code == HTTP_200_OK:
            return json.loads(res.text[10:-2])
        return None

    def get_photos(self, album_id, max_page_num, start=0):
        param = {
            'g_tk': self.gtk,
            'hostUin': self.hostUin if self.hostUin else self.uin,
            'uin': self.uin,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'topicId': album_id,
            'mode': 0,
            'appid': 4,
            'idcNum': 4,
            'noTopic': 0,
            'singleurl': 1,
            'skipCmtCount': 0,
            'pageStart': start,
            'pageNum': max_page_num,
            'source': 'qzone',
            'plat': 'qzone',
            'outstyle': 'json',
            'format': 'jsonp',
            'json_esc': 1,
            'question': '',
            'answer': '',
            'batchId': '',
        }
        res = requests.get(self.url_photo, headers=self.header, params=param)
        # 在qq空间中，取不到数据时，返回也是200 code，但是 data.list为None
        if res.status_code == HTTP_200_OK:
            return json.loads(res.text[10:-2])
        return None

    def multi_thread_download(self, photo_name_and_urls):
        def task_assign_and_download(thread_id, tasks):
            def get_index(tasks, thread_id):
                task_length = len(tasks)
                task_num_per_thread = math.ceil(task_length / self.thread_max_num)  # 每个线程处理的任务个数
                task_start_idx = task_num_per_thread * thread_id
                task_end_idx = task_num_per_thread * (thread_id + 1)
                task_end_idx = task_end_idx if task_end_idx <= task_length else task_length
                return task_start_idx, task_end_idx

            def download(source_url, target_path):
                photo_get = requests.get(source_url)
                if photo_get.status_code == HTTP_200_OK:
                    with open(target_path, 'wb+') as file:
                        file.write(photo_get.content)
                    return True
                return False

            start, end = get_index(tasks, thread_id)
            print('>> [{}]当前线程分配区域: [{}~{})'.format(thread_id, start, end))
            task_queue = SimpleQueue(copy.deepcopy(tasks[start:end]))
            while True:
                photo_item = task_queue.get()
                if empty(photo_item):
                    print('>> [{}]没有更多内容，当前线程完成'.format(thread_id))
                    break
                pic_name, pic_url = photo_item
                photo_save_path = self.file_save_path + pic_name
                print('>> [{}]当前下载：{} - {}'.format(thread_id, photo_save_path, pic_url))
                if download(source_url=pic_url, target_path=photo_save_path):
                    print(f'>> [{thread_id}] {pic_name} 下载成功')
                else:
                    print(f'>> [{thread_id}] {pic_name} 下载失败')
                time.sleep(0.1)

        print(">> 正式开始下载...")
        with ThreadPoolExecutor(self.thread_max_num) as executor:  # 创建 ThreadPoolExecutor
            future_list = [executor.submit(task_assign_and_download, thread_id=thread_id,
                                           tasks=photo_name_and_urls) for thread_id in
                           range(self.thread_max_num)]
        results = []
        for future in as_completed(future_list):
            results.append(future.result())  # 获取任务结果

    @staticmethod
    def print_info(info_lists):
        if empty(info_lists):
            print('>> 相册获取失败')
            return
        index = 1
        print(">> 你共有以下相册，请输入需要下载相册的序号 \r\n  ")
        for info_item in info_lists:
            name = info_item['name']
            num = info_item['total']
            allow_access = '加密' if info_item['allowAccess'] == 0 else '开放'
            print("[{}] ({}){} - {}".format(index, allow_access, name, num))
            index += 1

    def get_download_info(self, album_info):
        start_index = 0
        photo_lists = []
        album_name = ''
        while start_index < album_info['photo_total_num']:
            photo_info_json = self.get_photos(album_info['album_id'], album_info['max_num_in_page'],
                                              start=start_index)

            tmp_photo_lists = photo_info_json['data']['photoList']
            if not tmp_photo_lists:
                print('>> 无更多项')
                break

            print('>> 获取到{}项'.format(len(tmp_photo_lists)))
            photo_lists.extend(tmp_photo_lists)
            if not album_name:
                album_name = photo_info_json['data']['topic']['name']
            start_index += album_info['max_num_in_page']
        return photo_lists, album_name

    @staticmethod
    def rename_if_exist(f_name, f_suffix, f_name_sets):
        '''rename format: {f_name}_{exist_index}" + f_suffix'''
        temp_file_name = f_name + f_suffix
        exist_index = 1
        # while f_name_lists.count(temp_file_name):  # 文件重名就重新命名
        while temp_file_name in f_name_sets:  # 检测名字是否重名，当list数据量大的时候，用index的效率比count要高
            temp_file_name = f"{f_name}_{exist_index}" + f_suffix
            exist_index += 1
        return temp_file_name

    @staticmethod
    def write_info_to(file_name, info_lists, mode='w+'):
        with open(file_name, mode=mode, encoding='utf-8') as f:
            for name, url in info_lists:
                f.write(name + ' ' + url + '\n')
        print(f'>> 图片信息写入{file_name}完成')

    def get_name_and_urls(self, photo_lists):
        tmp_photo_name_and_urls = []
        file_names = set()  # 名字不重名，所以改用sets类型更好
        for item in tqdm(photo_lists, desc='照片链接处理中...'):
            item_name = item['name'].split('/')[-1].split('.')[-1]
            item_url = item['url'] if item['url'] else item['raw']
            is_video = item['is_video'] == 'true'
            suffix = '.mp4' if is_video else '.jpg'
            file_name = self.rename_if_exist(item_name, suffix, file_names)
            file_names.add(file_name)
            tmp_photo_name_and_urls.append((file_name, item_url))
        return tmp_photo_name_and_urls

    def main(self):
        print('>> 2.获取下载相册信息')
        res_json = self.get_album_info()
        album_info_lists = res_json['data']['albumListModeSort']
        if empty(album_info_lists):
            print('>> 获取下载信息失败')
            return

        self.print_info(album_info_lists)
        download_album_index = int(input('输入数字(如:1) ').strip()) - 1

        album_dict = {'album_id': album_info_lists[download_album_index]['id'],
                      'photo_total_num': album_info_lists[download_album_index]['total'],
                      'max_num_in_page': 500}
        print('>> 获取照片中...')
        photo_lists, album_name = self.get_download_info(album_dict)
        self.file_save_path = self.mkdir_path(self.root + album_name + '/')
        photo_name_and_urls = self.get_name_and_urls(photo_lists)

        print('>> 写照片信息到文件downloaded.txt...')
        self.write_info_to('downloaded.txt', photo_name_and_urls)

        start_time = datetime.datetime.now()
        print('>> 3. 下载照片中...')
        self.multi_thread_download(photo_name_and_urls)
        print(f">> 相册{album_name}下载完成...")
        print(f">> 下载用时{datetime.datetime.now() - start_time}s")




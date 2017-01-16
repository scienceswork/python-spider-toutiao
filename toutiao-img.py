#! /usr/bin/env python
# coding:utf-8

import re
import json
import time
import random
import os
import urllib2
import urllib

from urllib import urlencode
from bs4 import BeautifulSoup


# 根据传入的目录名创建一个目录,这里使用了python2.7的os库
def _create_dir(name):
    if not os.path.exists(name):
        os.mkdir(name)
    return name


# 将查询参数编码为url
def _get_query_string(data):
    return urlencode(data)


# 获取文章的url链接
def get_article_urls(req, timeout=10):
    res = urllib2.urlopen(req, timeout=timeout)
    d = json.loads(res.read().decode()).get('data')
    # 判断是否为空
    if d is None:
        print '数据全部请求完毕'
        return
    urls = [article.get('article_url') for article in d if article.get('article_url')]
    return urls


# 获取图片链接url
def get_photo_urls(req, timeout=10):
    res = urllib2.urlopen(req, timeout=timeout)
    soup = BeautifulSoup(res.read())
    article_main = soup.find('div', id="article-main")
    if not article_main:
        print '无法定位到文章主体...'
        return
    # 获取标题
    heading = article_main.h1.string
    if u'美女' not in heading:
        print '这不是美女的文章~'
        return
    img_list = [img.get('src') for img in article_main.find_all('img') if img.get('src')]
    return heading, img_list


# 保存图片
def save_photo(photo_url, save_dir, timeout=10):
    # 获取图片的名字
    photo_name = photo_url.rsplit('/', 1)[-1] + '.jpg'
    save_path = save_dir + '/' + photo_name
    data = urllib.urlopen(photo_url).read()
    f = file(save_path, 'wb')
    f.write(data)
    f.close()
    print '已下载图片:', save_path, ',请求的地址为:', photo_url


if __name__ == '__main__':
    offset = 0  # 请求的偏移量，每次累加20
    roo_dir = _create_dir('toutiao')  # 保存图片的根目录
    request_headers = {
        'Referer': 'http://www.toutiao.com/search/?keyword=%E7%BE%8E%E5%A5%B3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
    }

    while True:
        query_data = {
            'offset': offset,
            'format': 'json',
            'keyword': '美女',
            'autoload': 'true',
            'count': 20,
            'cur_tab': 1
        }
        query_url = 'http://www.toutiao.com/search_content/' + '?' + _get_query_string(query_data)
        article_req = urllib2.Request(query_url, headers=request_headers)
        article_urls = get_article_urls(article_req)
        # 如果队列中没有数据表示全部数据已经请求完毕，则跳出循环
        if article_urls is None:
            break
        # 得到每篇文章的url后开始发送请求
        for a_url in article_urls:
            # 请求页面时有可能会发生异常，比如连接超时、页面不存在等，对这些异常做一个处理
            try:
                photo_req = urllib2.Request(a_url, headers=request_headers)
                photo_urls = get_photo_urls(photo_req)
                # 判断文章中是否有图片，没有的话则跳到下一篇文章
                if photo_urls is None:
                    continue
                article_heading, photo_urls = photo_urls
                # 对文章标题进行处理，过滤不能作为目录名的特殊字符
                dir_name = re.sub(r'[\\/:*?"<>|]', '', article_heading)
                download_dir = _create_dir(roo_dir + '/' + dir_name)
                print download_dir
                # 开始下载文章中的图片
                for p_url in photo_urls:
                    # 异常处理
                    try:
                        save_photo(p_url, save_dir=download_dir)
                    except Exception, e:
                        print e
                        continue
            except Exception, e:
                # 链接超时，随机休息1~5秒
                print e
                time.sleep(random.randint(1, 5))
                continue
        # 每次请求完迁移量添加20
        offset += 20

# coding=utf-8
# for Python 3.x

import re
import os
import sys
import urllib.request
import time

# 屏幕大小，目前可用1920x1200、1920x1080
# 前者适用16:10屏幕，后者适用16:9屏幕
myscreen = '1920x1200'

#=====================
#      网络获取
#=====================


class FetcherInfo:

    def __init__(self):
        self.ua = 'bingwp'
        self.referer = ''
        self.open_timeout = 120
        self.retry_count = 2
        self.retry_interval = 1


class Fetcher:

    '''web获取器'''

    def __init__(self, fetcher_info=None):
        if fetcher_info == None:
            fetcher_info = FetcherInfo()
        
        self.referer = fetcher_info.referer
        self.info = fetcher_info

        # no proxy
        proxy = urllib.request.ProxyHandler({})
        # opener
        self.opener = urllib.request.build_opener(proxy)

    def save_file(self, url, local_path):
        if os.path.exists(local_path):
            print(local_path, '文件已存在')
            return 0

        byte_data = self.fetch_url(url)
        data_len = len(byte_data)

        if data_len > 0:
            with open(local_path, 'wb') as f:
                f.write(byte_data)
        return data_len

    def fetch_url(self, url):
        '''返回bytes'''
        # 重试次数
        retry = self.info.retry_count

        # request对象
        req = urllib.request.Request(url)
        req.add_header('User-Agent', self.info.ua)

        # 重试用的循环
        while True:
            try:
                # r是HTTPResponse对象
                r = self.opener.open(req,
                                     timeout=self.info.open_timeout
                                     )
                ret_data = r.read()
                return ret_data

            except Exception as e:
                print('! 下载时出现异常', url)
                print('! 可能是网址错误、服务器抽风、下载超时等等')
                print('! 详细异常信息:', type(e), '\n', e, '\n')

            retry -= 1
            if retry <= 0:
                break

            print('{0}秒后重试，剩余重试次数：{1}次\n'.
                  format(self.info.retry_interval, retry)
                  )
            time.sleep(self.info.retry_interval)

        print('重试次数用完，下载失败')
        return b''

#======================
#       主程序
#======================


def main():
    print('准备保存cn.bing.com首页背景图\n')

    # wallpapers目录
    if not os.path.isdir('wallpapers'):
        try:
            os.mkdir('wallpapers')
        except:
            raise Exception('创建wallpapers目录失败')

    # 得到 文件名list
    try:
        f = open(os.path.join('wallpapers', 'fnlist'))
        fn_lst = eval(f.read())
        f.close()
    except:
        fn_lst = []

    # fetcher
    f = Fetcher()

    # 下载首页
    bing_url = 'http://cn.bing.com/'
    try:
        html = f.fetch_url(bing_url).decode('utf-8')
    except:
        print('解码失败')
        html = ''

    if not html:
        raise Exception('无法下载首页')
    print('首页共%d个字符' % len(html))

    # 提取图片链接
    p = r"g_img={url:'([^']+)'"
    m = re.search(p, html)
    if not m:
        raise Exception('无法用正则表达式<提取图片地址>')
    pic_url = m.group(1)

    # 提取本地file_name
    p = r'http://.*/(.*)_ZH-CN'
    m = re.search(p, pic_url, re.I)
    if not m:
        raise Exception('无法用正则表达式<提取要保存的文件名>')
    file_name = m.group(1)

    # 检查fn_lst
    if file_name in fn_lst:
        print('%s 图片已经存在' % file_name)
        return ''

    fn_lst.insert(0, file_name)
    if len(fn_lst) > 10:
        fn_lst = fn_lst[:10]

    # 本地图片路径
    file_path = os.path.join('wallpapers', file_name + '.jpg')
    file_path2 = os.path.join('wallpapers', '000'+file_name + '.jpg')

    
    # 替换分辨率，替换成1920x1200：
    # http://s.cn.bing.net/az/hprichbg/rb/
    # LaCazeCastle_ZH-CN9575179265_1920x1080.jpg
    p = r'(http://.*_)\d+x\d+(\.jpg)'
    new_url, n = re.subn(p, r'\g<1>' + myscreen + r'\g<2>',
                         pic_url, flags=re.I)
 
    if n != 1:
        raise Exception('用正则表达式<替换分辨率>失败')

    # 下载替换分辨率后的图片
    print('正在下载...')
    file_size = f.save_file(new_url, file_path)
    # 如失败，尝试下载原图
    if file_size == 0:
        file_size = f.save_file(pic_url, file_path2)
        if file_size == 0:
            raise Exception('文件下载失败')
        file_path = file_path2
    print('下载完成，共%s字节' % format(file_size, ','))

    # 写入fnlist
    with open(os.path.join('wallpapers', 'fnlist'), 'w') as f:
        f.write(repr(fn_lst))

    # 取绝对路径
    this_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(this_path, file_path)
     
#     # 设为壁纸
#     print(file_path)
#     ret = ctypes.windll.user32.SystemParametersInfoA(
#                 0x14, 0, file_path, 3)
#     if not ret:
#         raise Exception('设置失败')
# 
#     print('设置壁纸成功')

    # 调用外部程序打开图片
    if sys.platform == 'win32':
        os.startfile(file_path)
    else:
        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
        import subprocess
        subprocess.call([opener, file_path])

    # 提取简介
    p = r'var g_hot=(.*?);;function fadeComplete'
    m = re.search(p, html)
    if not m:
        raise Exception('无法用正则表达式<提取介绍文字1>')
    rawtext = m.group(1)

    p = r'".*?"'
    lst = re.findall(p, rawtext)
    if not lst:
        raise Exception('无法用正则表达式<提取介绍文字2>')

    # 返回介绍
    return file_name + '\n\n' + ''.join(i.strip('"') for i in lst)


from tkinter import Tk, Frame, Text, Scrollbar, Pack, Grid, Place
from tkinter.constants import RIGHT, LEFT, Y, BOTH, END


class ScrolledText(Text):

    def __init__(self, master=None, **kw):
        self.frame = Frame(master)
        self.vbar = Scrollbar(self.frame)
        self.vbar.pack(side=RIGHT, fill=Y)

        kw.update({'yscrollcommand': self.vbar.set})
        Text.__init__(self, self.frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=True)
        self.vbar['command'] = self.yview

        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack!
        text_meths = vars(Text).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)


def showtext(message):
    root = Tk()

    stext = ScrolledText(master=root, bg='white', width=50, height=10)
    stext.insert(END, message)
    stext.pack(fill=BOTH, side=LEFT, expand=True)
    stext.focus_set()
    # stext.mainloop()

    # center on screen
    w = stext.winfo_reqwidth()
    h = stext.winfo_reqheight()
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    root.mainloop()

if __name__ == '__main__':
    try:
        text = main()
        if text:
            showtext(text)
    except Exception as e:
        print('异常:', e, '\n')
        if sys.platform == 'win32':
            os.system('pause')

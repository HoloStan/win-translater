#/usr/bin/env python
#coding=utf8
import sys
import os
import http.client
import hashlib
import urllib.parse
import random
import time
import threading
import pyperclip
import tkinter
import json
import tkinter.ttk as ttk
from ctypes import windll

from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image

appid = '' #你的appid
secretKey = '' #你的密钥

httpClient = None
myurl = ''
q = 'apple'
fromLang = 'en'
toLang = 'zh'


GWL_EXSTYLE=-20
WS_EX_APPWINDOW=0x00040000
WS_EX_TOOLWINDOW=0x00000080

# 功能对象
class Function(object):
    # 初始化类
    def __init__(self):
        super(Function, self).__init__()
    # 翻译
    def translate(self, text):
        try:
            salt = random.randint(32768, 65536)
            sign = appid+text+str(salt)+secretKey
            m1 = hashlib.md5(sign.encode("utf-8"))
            sign = m1.hexdigest()
            myurl = '/api/trans/vip/translate?appid='+appid+'&q='+urllib.parse.quote(text, '')+'&from='+fromLang+'&to='+toLang+'&salt='+str(salt)+'&sign='+sign
            httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient.request('GET', myurl)
         
            #response是HTTPResponse对象
            response = httpClient.getresponse()
            res = json.loads(response.read().decode('utf-8'))
            return res
        except Exception as e:
            print(e)
        finally:
            if httpClient:
                httpClient.close()

# 皮肤界面
class Interface(object):
    # 初始化类
    def __init__(self, winWidth, winHeight):
        super(Interface, self).__init__()
        # 窗口主体
        self.root = tkinter.Tk()
        # 这是文字变量储存器, 接收并显示翻译结果
        self.result = tkinter.StringVar()
        # 窗口位置
        self.winXPos = 0
        self.winYPos = 0
        # 窗口宽高
        self.winWidth = winWidth if winWidth else self.root.winfo_screenwidth()
        self.winHeight = winHeight if winHeight else self.root.winfo_screenheight()
        # 屏幕宽高
        self.realWinXMaxPos = self.root.winfo_screenwidth()
        self.realWinYMaxPos = self.root.winfo_screenheight()
        # 右键菜单
        self.menu = tkinter.Menu(self.root, tearoff=0)
        self.menu.add_command(label="退出", command=self.root.quit)
        self.root.bind("<Button-3>", self.rmenu)
        self.func = Function()
        self.afterId = None

    # 预先配置
    def preConfig(self):
        # 窗口位置
        self.winXPos = rootWin.realWinXMaxPos - rootWin.winWidth
        self.winYPos = rootWin.realWinYMaxPos - rootWin.winHeight - 40
        # 窗口透明
        self.root.attributes("-alpha", 0.6)
        self.root.configure(bg="grey")
        # 窗口位置, 默认屏幕底部
        #self.root.geometry(str(self.winWidth) + "x" + str(self.winHeight) + "+" + str(self.winXPos) + "+" + str(self.winYPos))
        self.root.geometry("0x0+%s+%s" % (str(self.winXPos), str(self.winYPos)))
        # 绘制文本框
        self.label = tkinter.Label(self.root, textvariable=self.result, bg="black", fg="white", wraplength=(self.winWidth / 4), font=("宋体", 14))
        self.label.pack()
        # 拖动文本框
        self.label.bind("<ButtonPress-1>", self.StartMove)
        self.label.bind("<ButtonRelease-1>", self.StopMove)
        self.label.bind("<B1-Motion>", self.OnMotion)
        # 窗口置顶
        self.root.wm_attributes('-topmost',1)
        self.root.wm_title("translater")
        # 自定义样式
        self.root.overrideredirect(True)
        self.root.after(10, lambda: self.set_appwindow())
    # 无边框设置
    def set_appwindow(self):
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        # 不在任务栏显示
        style = style & ~WS_EX_APPWINDOW    #当窗口可见时将一个顶层窗口放置在任务栏上
        style = style | WS_EX_TOOLWINDOW    #工具条窗口样式
        res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        # re-assert the new window style
        self.root.wm_withdraw()
        self.root.after(10, lambda: self.root.wm_deiconify())
        
    # 右键菜单
    def rmenu(self, event):
        self.menu.post(event.x_root, event.y_root)
    # 置顶框架, leftTime秒
    def showRoot(self, leftTime):
        # 框架自适应
        self.root.winfo_toplevel().wm_geometry("")
        if self.afterId:
            self.root.after_cancel(self.afterId)
        self.afterId = self.root.after(leftTime, lambda: self.hideRoot())
    # 隐藏框架
    def hideRoot(self):
        self.root.geometry("0x0")
    # 显示文本内容
    def setText(self, text):
        res = self.func.translate(text)
        print(res)
        self.result.set(str(res['trans_result'][0]['dst']))
    # 拖动文本框
    def StartMove(self, event):
        self.x = event.x
        self.y = event.y
    def StopMove(self, event):
        self.x = None
        self.y = None
    def OnMotion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry("+%s+%s" % (x, y))
    def destroy(self):
        self.root.destroy()

# 监听对象
class Listener(threading.Thread):

    def __init__(self, rootWin):
        threading.Thread.__init__(self)
        self.recent_value = ""
        self.tmp_value = ""
        self.rootWin = rootWin

    def run(self):
        while True:
            self.tmp_value = pyperclip.paste()  # 读取剪切板复制的内容
            try:
                if self.tmp_value and self.tmp_value != self.recent_value:   # 如果检测到剪切板内容有改动，那么就尝试翻译
                    self.recent_value = self.tmp_value
                    # todo:翻译并输出
                    rootWin.setText(str(self.tmp_value))
                    rootWin.showRoot(5000)
                time.sleep(0.1)  # 等待100ms
            except Exception as e:
                print(e)

#生成资源文件目录访问路径
def resource_path(relative_path):
    if getattr(sys, 'frozen', False): #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def blank(rootWin):
    pass

def quit(icon, rootWin):
    try:
        icon.visible = False
        #icon.stop()
        rootWin.destroy()
    except Exception as e:
        print(e)

# 初始化系统托盘
def systemTrayIcon(rootWin):
    icon("translater", Image.open(resource_path(os.path.join("res","image.ico"))), "translater", menu=menu(
        item("退出", lambda icon, item: quit(icon, rootWin)),
    )).run()

# 启动程序
if __name__ == '__main__':
    # 初始化窗口
    rootWin = Interface(0, 40)
    rootWin.preConfig()
    
    print('[%s] thread start!' % time.ctime())
    try:
        # 启动托盘进程
        t0 = threading.Thread(target=systemTrayIcon, args=(rootWin,))
        t0.setDaemon(True)
        t0.start()
        
        t = Listener(rootWin)
        t.setDaemon(True)
        t.start()  # create a listen thread
        
        rootWin.root.mainloop()
    except KeyboardInterrupt as e:
        print("[%s] thread exiting..." % time.ctime())

    print('[%s] thread end!' % time.ctime())
    
# package command
# pyinstaller translater.py --noconsole
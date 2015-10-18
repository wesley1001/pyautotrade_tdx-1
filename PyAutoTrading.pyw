# -*- encoding: utf8 -*-
# QQ群： 486224275
__author__ = '人在江湖'


import tkinter.messagebox
from tkinter import *
from tkinter.ttk import *
import datetime
import threading
import pickle
import configparser
import time
import tushare as ts
from winguiauto import *

is_start = False
is_monitor = True
set_stock_info = []
order_msg = []
actual_stock_info = []
is_ordered = [1] * 5  # 1：未下单  0：已下单


def getConfigData():
    '''
    读取配置文件参数
    :return:双向委托界面下，控件的数量
    '''
    cp = configparser.ConfigParser()
    cp.read('pyautotrading.ini')
    numChildWindows = cp.getint('tradeVersion', 'numChildWindows')
    return numChildWindows


# def pickHwndOfControls(top_hwnd, num_child_windows):
#     cleaned_hwnd_controls = []
#     hwnd_controls = findSpecifiedWindows(top_hwnd, num_child_windows)
#     for Hwnd, text_name, class_name in hwnd_controls:
#         if class_name in ('Button', 'Edit'):
#             cleaned_hwnd_controls.append((Hwnd, text_name, class_name))
#     return cleaned_hwnd_controls


def getRunningMoney(sub_hwnds):
    '''
    :param sub_hwnds: 双向委托操作界面下的控件句柄列表
    :return:可用资金
    '''
    return getWindowText(sub_hwnds[12][1])


def buy(sub_hwnds, code, stop_price, quantity):
    '''
    买函数，自动填写3个Edit控件，及点击买入按钮。
    :param sub_hwnds: 双向委托操作界面下的控件句柄列表
    :param code: 股票代码，字符串
    :param stop_price: 涨停市价， 字符串
    :param quantity: 买入股票 数量，字符串
    :return:
    '''
    setEditText(sub_hwnds[0][0], code)
    setEditText(sub_hwnds[1][0], stop_price)
    setEditText(sub_hwnds[3][0], quantity)
    time.sleep(0.3)
    click(sub_hwnds[5][0])
    time.sleep(0.3)


def sell(sub_hwnds, code, stop_price, quantity):
    '''
    买函数，自动填写3个Edit控件，及点击卖出按钮。
    :param sub_hwnds: 双向委托操作界面下的控件句柄列表
    :param code: 股票代码，字符串
    :param stop_price: 涨停市价， 字符串
    :param quantity: 卖出股票 数量，字符串
    :return:
    '''
    setEditText(sub_hwnds[24][0], code)
    setEditText(sub_hwnds[25][0], stop_price)
    setEditText(sub_hwnds[27][0], quantity)
    time.sleep(0.3)
    click(sub_hwnds[29][0])
    time.sleep(0.3)


def order(top_hwnd, sub_hwnds, code, stop_prices, quantity, direction):
    '''
    买卖函数
    :param top_hwnd: 顶层窗口句柄
    :param sub_hwnds: 双向委托操作界面下的控件句柄列表
    :param code: 股票代码， 字符串
    :param stop_prices: 涨跌停价格，字符串
    :param quantity: 买卖数量，字符串
    :param direction: 交易方向，字符串
    :return:
    '''
    if direction == 'B':
        buy(sub_hwnds, code, stop_prices[0], quantity)
    if direction == 'S':
        sell(sub_hwnds, code, stop_prices[1], quantity)


def tradingInit():
    '''
    获得交易软件句柄
    :return:顶层窗口句柄，双向委托操作界面下的控件句柄列表
    '''
    top_hwnd = findSpecifiedTopWindow(wantedClass='TdxW_MainFrame_Class')
    if top_hwnd == 0:
        tkinter.messagebox.showerror('错误', '请先打开交易软件，再运行本软件')
        return top_hwnd, []
    else:
        sub_hwnds = findSpecifiedWindows(top_hwnd, getConfigData())
    return top_hwnd, sub_hwnds


def pickCodeFromItems(items_info):
    '''
    提取股票代码
    :param items_info: UI下各项输入信息
    :return:股票代码列表
    '''
    stock_codes = []
    for item in items_info:
        stock_codes.append(item[0])
    return stock_codes


def getStockData(items_info):
    '''
    获取股票实时数据
    :param items_info:UI下各项输入信息
    :return:股票实时数据
    '''
    code_name_price = []
    stock_codes = pickCodeFromItems(items_info)
    try:
        df = ts.get_realtime_quotes(stock_codes)
        df_len = len(df)
        for stock_code in stock_codes:
            is_found = False
            for i in range(df_len):
                actual_code = df['code'][i]
                if stock_code == actual_code:
                    actual_name = df['name'][i]
                    pre_close = float(df['pre_close'][i])
                    if 'ST' in actual_name:
                        highest = str(round(pre_close * 1.05, 2))
                        lowest = str(round(pre_close * 0.95, 2))
                        code_name_price.append((actual_code, actual_name, df['price'][i], (highest, lowest)))
                    else:
                        highest = str(round(pre_close * 1.1, 2))
                        lowest = str(round(pre_close * 0.9, 2))
                        code_name_price.append((actual_code, actual_name, df['price'][i], (highest, lowest)))
                    is_found = True
                    break
            if is_found is False:
                code_name_price.append(('', '', '', ('', '')))
    except:
        code_name_price = [('', '', '', ('', ''))] * 5  # 网络不行，返回空
    return code_name_price


def monitor():
    '''
    实时监控函数
    :return:
    '''
    global actual_stock_info, order_msg, is_ordered, set_stock_info
    count = 0
    top_hwnd, sub_hwnds = tradingInit()
    # 如果top_hwnd为零，直接终止循环
    while is_monitor and top_hwnd:
        if count % 100 == 0:
            # clickButton(sub_hwnd[12][0]) # 点击刷新按钮
            time.sleep(1)
        time.sleep(3)
        count += 1
        if is_start:
            actual_stock_info = getStockData(set_stock_info)
            # print('actual_stock_info', actual_stock_info)
            for row, (actual_code, actual_name, actual_price, stop_prices) in enumerate(actual_stock_info):
                if is_start and actual_code and is_ordered[row] == 1 \
                        and set_stock_info[row][1] and set_stock_info[row][2] > 0 \
                        and set_stock_info[row][3] and set_stock_info[row][4] \
                        and datetime.datetime.now().time() > set_stock_info[row][5]:
                    if is_start and set_stock_info[row][1] == '>' and float(actual_price) > set_stock_info[row][2]:
                        dt = datetime.datetime.now()
                        order(top_hwnd, sub_hwnds, actual_code, stop_prices,
                              set_stock_info[row][4], set_stock_info[row][3])
                        closePopupWindows(top_hwnd)
                        order_msg.append(
                            (dt.strftime('%x'), dt.strftime('%X'), actual_code,
                             actual_name, set_stock_info[row][3],
                             actual_price, set_stock_info[row][4], '已下单'))
                        is_ordered[row] = 0

                    if is_start and set_stock_info[row][1] == '<' and float(actual_price) < set_stock_info[row][2]:
                        dt = datetime.datetime.now()
                        order(top_hwnd, sub_hwnds, actual_code, stop_prices,
                              set_stock_info[row][4], set_stock_info[row][3])
                        closePopupWindows(top_hwnd)
                        order_msg.append(
                            (dt.strftime('%x'), dt.strftime('%X'), actual_code,
                             actual_name, set_stock_info[row][3],
                             actual_price, set_stock_info[row][4], '已下单'))
                        is_ordered[row] = 0


class StockGui:
    def __init__(self):
        self.window = Tk()
        self.window.title("自动化股票交易")
        self.window.resizable(0, 0)

        frame1 = Frame(self.window)
        frame1.pack(padx=10, pady=10)

        Label(frame1, text="股票代码", width=8, justify=CENTER).grid(
            row=1, column=1, padx=5, pady=5)
        Label(frame1, text="股票名称", width=8, justify=CENTER).grid(
            row=1, column=2, padx=5, pady=5)
        Label(frame1, text="当前价格", width=8, justify=CENTER).grid(
            row=1, column=3, padx=5, pady=5)
        Label(frame1, text="关系", width=4, justify=CENTER).grid(
            row=1, column=4, padx=5, pady=5)
        Label(frame1, text="价格", width=8, justify=CENTER).grid(
            row=1, column=5, padx=5, pady=5)
        Label(frame1, text="方向", width=4, justify=CENTER).grid(
            row=1, column=6, padx=5, pady=5)
        Label(frame1, text="数量", width=8, justify=CENTER).grid(
            row=1, column=7, padx=5, pady=5)
        Label(frame1, text="时间可选", width=8, justify=CENTER).grid(
            row=1, column=8, padx=5, pady=5)
        Label(frame1, text="状态", width=4, justify=CENTER).grid(
            row=1, column=9, padx=5, pady=5)

        self.rows = 5
        self.cols = 9

        self.variable = []
        for row in range(self.rows):
            self.variable.append([])
            for col in range(self.cols):
                temp = StringVar()
                self.variable[row].append(temp)

        for row in range(self.rows):
            Entry(frame1, textvariable=self.variable[row][0],
                  width=8).grid(row=row + 2, column=1, padx=5, pady=5)
            Entry(frame1, textvariable=self.variable[row][1], state=DISABLED,
                  width=8).grid(row=row + 2, column=2, padx=5, pady=5)
            Entry(frame1, textvariable=self.variable[row][2], state=DISABLED,
                  width=8).grid(row=row + 2, column=3, padx=5, pady=5)
            Combobox(frame1, values=('<', '>'), textvariable=self.variable[row][3],
                     width=2).grid(row=row + 2, column=4, padx=5, pady=5)
            Spinbox(frame1, from_=0, to=1000, textvariable=self.variable[row][4],
                    increment=0.01, width=6).grid(row=row + 2, column=5, padx=5, pady=5)
            Combobox(frame1, values=('B', 'S'), textvariable=self.variable[row][5],
                     width=2).grid(row=row + 2, column=6, padx=5, pady=5)
            Spinbox(frame1, from_=0, to=100000, textvariable=self.variable[row][6],
                    increment=100, width=6).grid(row=row + 2, column=7, padx=5, pady=5)
            Entry(frame1, textvariable=self.variable[row][7],
                  width=8).grid(row=row + 2, column=8, padx=5, pady=5)
            Entry(frame1, textvariable=self.variable[row][8], state=DISABLED,
                  width=5).grid(row=row + 2, column=9, padx=5, pady=5)

        frame3 = Frame(self.window)
        frame3.pack(padx=10, pady=10)
        self.start_bt = Button(frame3, text="开始", command=self.start)
        self.start_bt.pack(side=LEFT)
        self.set_bt = Button(frame3, text='重置买卖', command=self.setFlags)
        self.set_bt.pack(side=LEFT)
        Button(frame3, text="历史记录", command=self.displayHisRecords).pack(side=LEFT)
        Button(frame3, text='保存', command=self.save).pack(side=LEFT)
        self.load_bt = Button(frame3, text='载入', command=self.load)
        self.load_bt.pack(side=LEFT)

        self.window.protocol(name="WM_DELETE_WINDOW", func=self.close)
        self.window.after(100, self.updateControls)
        self.window.mainloop()

    def displayHisRecords(self):
        '''
        显示历史信息
        :return:
        '''
        global order_msg
        tp = Toplevel()
        tp.title('历史记录')
        tp.resizable(0, 1)
        scrollbar = Scrollbar(tp)
        scrollbar.pack(side=RIGHT, fill=Y)
        col_name = ['日期', '时间', '证券代码', '证券名称', '方向', '价格', '数量', '备注']
        tree = Treeview(
            tp, show='headings', columns=col_name, height=30, yscrollcommand=scrollbar.set)
        tree.pack(expand=1, fill=Y)
        scrollbar.config(command=tree.yview)
        for name in col_name:
            tree.heading(name, text=name)
            tree.column(name, width=70, anchor=CENTER)

        for msg in order_msg:
            tree.insert('', 0, values=msg)

    def save(self):
        '''
        保存设置
        :return:
        '''
        global set_stock_info, order_msg, actual_stock_info
        self.getItems()
        with open('stockInfo.dat', 'wb') as fp:
            pickle.dump(set_stock_info, fp)
            # pickle.dump(actual_stock_info, fp)
            pickle.dump(order_msg, fp)

    def load(self):
        '''
        载入设置
        :return:
        '''
        global set_stock_info, order_msg, actual_stock_info
        with open('stockInfo.dat', 'rb') as fp:
            set_stock_info = pickle.load(fp)
            # actual_stock_info = pickle.load(fp)
            order_msg = pickle.load(fp)
        for row in range(self.rows):
            for col in range(self.cols):
                if col == 0:
                    self.variable[row][col].set(set_stock_info[row][0])
                elif col == 3:
                    self.variable[row][col].set(set_stock_info[row][1])
                elif col == 4:
                    self.variable[row][col].set(set_stock_info[row][2])
                elif col == 5:
                    self.variable[row][col].set(set_stock_info[row][3])
                elif col == 6:
                    self.variable[row][col].set(set_stock_info[row][4])
                elif col == 7:
                    temp = set_stock_info[row][5].strftime('%X')
                    if temp == '01:00:00':
                        self.variable[row][col].set('')
                    else:
                        self.variable[row][col].set(temp)

    def setFlags(self):
        '''
        重置买卖标志
        :return:
        '''
        global is_start, is_ordered
        if is_start is False:
            is_ordered = [1] * 5

    def updateControls(self):
        '''
        实时股票名称、价格、状态信息
        :return:
        '''
        global set_stock_info, actual_stock_info, is_start
        if is_start:
            print('actual_stock_info', actual_stock_info)
            for row, (actual_code, actual_name, actual_price, _) in enumerate(actual_stock_info):
                self.variable[row][1].set(actual_name)
                self.variable[row][2].set(str(actual_price))
                if actual_code:
                    if is_ordered[row] == 1:
                        self.variable[row][8].set('监控中')
                    elif is_ordered[row] == 0:
                        self.variable[row][8].set('已下单')
                else:
                    self.variable[row][8].set('')

        self.window.after(3000, self.updateControls)

    def start(self):
        '''
        启动停止
        :return:
        '''
        global is_start
        if is_start is False:
            is_start = True
        else:
            is_start = False

        if is_start:
            self.getItems()
            # print(set_stock_info)
            self.start_bt['text'] = '停止'
            self.set_bt['state'] = DISABLED
            self.load_bt['state'] = DISABLED
        else:
            self.start_bt['text'] = '开始'
            self.set_bt['state'] = NORMAL
            self.load_bt['state'] = NORMAL

    def close(self):
        '''
        关闭程序时，停止monitor线程
        :return:
        '''
        global is_monitor
        is_monitor = False
        self.window.quit()

    def getItems(self):
        '''
        获取UI上用户输入的各项数据，
        '''
        global set_stock_info
        set_stock_info = []

        # 获取买卖价格数量输入项等
        for row in range(self.rows):
            set_stock_info.append([])
            for col in range(self.cols):
                temp = self.variable[row][col].get().strip()
                if col == 0:
                    if len(temp) == 6 and temp.isdigit():  # 判断股票代码是否为6位数
                        set_stock_info[row].append(temp)
                    else:
                        set_stock_info[row].append('')
                elif col == 3:
                    if temp in ('>', '<'):
                        set_stock_info[row].append(temp)
                    else:
                        set_stock_info[row].append('')
                elif col == 4:
                    try:
                        price = float(temp)
                        if price > 0:
                            set_stock_info[row].append(price)  # 把价格转为数字
                        else:
                            set_stock_info[row].append(0)
                    except ValueError:
                        set_stock_info[row].append(0)
                elif col == 5:
                    if temp in ('B', 'S'):
                        set_stock_info[row].append(temp)
                    else:
                        set_stock_info[row].append('')
                elif col == 6:
                    if temp.isdigit() and int(temp) >= 100:
                        set_stock_info[row].append(str(int(temp) // 100 * 100))
                    else:
                        set_stock_info[row].append('')
                elif col == 7:
                    try:
                        set_stock_info[row].append(datetime.datetime.strptime(temp, '%H:%M:%S').time())
                    except ValueError:
                        set_stock_info[row].append(datetime.datetime.strptime('1:00:00', '%H:%M:%S').time())


if __name__ == '__main__':
    t1 = threading.Thread(target=StockGui)
    t2 = threading.Thread(target=monitor)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

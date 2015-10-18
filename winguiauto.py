# -*- encoding: utf8 -*-

# Module     : winGuiAuto.py
# Synopsis   : Windows GUI automation utilities
# Programmer : Simon Brunning - simon@brunningonline.net
# Date       : 25 June 2003
# Version    : 1.0 pre-alpha 2
# Copyright  : Released to the public domain. Provided as-is, with no warranty.
# Notes      : Requires Python 2.3, win32all and ctypes 
'''Windows GUI automation utilities.

Until I get around to writing some docs and examples, the tests at the foot of
this module should serve to get you started.
'''
import time
import struct
import win32api
import win32gui
import win32con


def findSpecifiedTopWindow(wantedText=None, wantedClass=None):
    '''
    :param wantedText: 标题名字
    :param wantedClass: 窗口类名
    :return: 返回顶层窗口的句柄
    '''
    return win32gui.FindWindow(wantedClass, wantedText)


def findPopupWindow(hwnd):
    '''
    :param hwnd: 父窗口句柄
    :return: 返回弹出式窗口的句柄
    '''
    return win32gui.GetWindow(hwnd, win32con.GW_ENABLEDPOPUP)


def findTopWindow(wantedText=None, wantedClass=None, selectionFunction=None):
    '''Find the hwnd of a top level window.
    You can identify windows using captions, classes, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)

    Parameters
    ----------
    wantedText          
        Text which the required window's captions must contain.
    wantedClass         
        Class to which the required window must belong.
    selectionFunction   
        Window selection function. Reference to a function
        should be passed here. The function should take hwnd as
        an argument, and should return True when passed the
        hwnd of a desired window.
                    
    Raises
    ------
    WinGuiAutoError     
        When no window found.

    Usage example::
        
        optDialog = findTopWindow(wantedText="Options")
    '''
    topWindows = findTopWindows(wantedText, wantedClass, selectionFunction)
    if topWindows:
        return topWindows[0]
    else:
        raise WinGuiAutoError("No top level window found for wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction))


def findTopWindows(wantedText=None, wantedClass=None, selectionFunction=None):
    '''Find the hwnd of top level windows.
    
    You can identify windows using captions, classes, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)

    Parameters
    ----------
    wantedText          
        Text which required windows' captions must contain.
    wantedClass         
        Class to which required windows must belong.
    selectionFunction   
        Window selection function. Reference to a function
        should be passed here. The function should take hwnd as
        an argument, and should return True when passed the
        hwnd of a desired window.

    Returns
    -------
    A list containing the window handles of all top level
    windows matching the supplied selection criteria.

    Usage example::
        
        optDialogs = findTopWindows(wantedText="Options")
    '''
    results = []
    topWindows = []
    win32gui.EnumWindows(_windowEnumerationHandler, topWindows)
    for hwnd, windowText, windowClass in topWindows:
        if wantedText and not _normaliseText(wantedText) in _normaliseText(windowText):
            continue
        if wantedClass and not windowClass == wantedClass:
            continue
        if selectionFunction and not selectionFunction(hwnd):
            continue
        results.append(hwnd)
    return results


def dumpSpecifiedWindow(hwnd, wantedText=None, wantedClass=None):
    '''
    :param hwnd: 父窗口句柄
    :param wantedText: 指定子窗口名
    :param wantedClass: 指定子窗口类名
    :return: 返回父窗口下所有子窗体的句柄
    '''
    windows = []
    hwndChild = None
    while True:
        hwndChild = win32gui.FindWindowEx(hwnd, hwndChild, wantedClass, wantedText)
        if hwndChild:
            textName = win32gui.GetWindowText(hwndChild)
            className = win32gui.GetClassName(hwndChild)
            windows.append((hwndChild, textName, className))
        else:
            return windows

def findSpecifiedWindows(top_hwnd, numChildWindows=70):
    '''
    查找某一窗口下指定数量的子窗口
    :param top_hwnd: 主窗口句柄
    :param numChildWindows: 子窗口数量
    :return:子窗口列表，包括子窗口hwnd, title, className
    '''
    windows = []
    try:
        win32gui.EnumChildWindows(top_hwnd, _windowEnumerationHandler, windows)
    except win32gui.error:
        # No child windows
        return
    for window in windows:
        childHwnd, windowText, windowClass = window
        windowContent = dumpSpecifiedWindow(childHwnd)
        if len(windowContent) == numChildWindows:
            return windowContent
    # 没有指定数量的句柄
    return

def dumpWindow(hwnd):
    '''Dump all controls from a window into a nested list
    
    Useful during development, allowing to you discover the structure of the
    contents of a window, showing the text and class of all contained controls.

    Parameters
    ----------
    hwnd
        The window handle of the top level window to dump.

    Returns
    -------
    A nested list of controls. Each entry consists of the
    control's hwnd, its text, its class, and its sub-controls, if any.

    Usage example::
        
        replaceDialog = findTopWindow(wantedText='Replace')
        pprint.pprint(dumpWindow(replaceDialog))
    '''
    windows = []
    try:
        win32gui.EnumChildWindows(hwnd, _windowEnumerationHandler, windows)
    except win32gui.error:
        # No child windows
        return
    windows = [list(window) for window in windows]
    for window in windows:
        childHwnd, windowText, windowClass = window
        window_content = dumpWindow(childHwnd)
        if window_content:
            window.append(window_content)
    return windows


def _closePopupWindow(top_hwnd, wantedText=None, wantedClass=None):
    '''
    关闭一个弹窗。
    :param top_hwnd: 主窗口句柄
    :param wantedText: 弹出对话框上的按钮文本
    :param wantedClass: 弹出对话框上的按钮类名
    :return: 如果有弹出式对话框，返回True，否则返回False
    '''
    hwnd_popup = findPopupWindow(top_hwnd)
    if hwnd_popup:
        hwnd_control = findControl(hwnd_popup, wantedText, wantedClass)
        clickButton(hwnd_control)
        return True
    return False


def closePopupWindows(top_hwnd):
    '''
    连续点击多个弹出式对话框，直到没有弹窗
    :param top_hwnd: 主窗口句柄
    :return:
    '''
    while _closePopupWindow(top_hwnd):
        time.sleep(0.3)


def findControl(topHwnd,
                wantedText=None,
                wantedClass=None,
                selectionFunction=None):
    '''Find a control.
    
    You can identify a control using caption, classe, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)

    Parameters
    ----------
    topHwnd             
        The window handle of the top level window in which the
        required controls reside.
    wantedText          
        Text which the required control's captions must contain.
    wantedClass         
        Class to which the required control must belong.
    selectionFunction   
        Control selection function. Reference to a function
        should be passed here. The function should take hwnd as
        an argument, and should return True when passed the
        hwnd of the desired control.

    Returns
    -------
    The window handle of the first control matching the
    supplied selection criteria.
                    
    Raises
    ------
    WinGuiAutoError, when no control found.

    Usage example::
        
        optDialog = findTopWindow(wantedText="Options")
        okButton = findControl(optDialog,
                               wantedClass="Button",
                               wantedText="OK")
    '''
    controls = findControls(topHwnd,
                            wantedText=wantedText,
                            wantedClass=wantedClass,
                            selectionFunction=selectionFunction)
    if controls:
        return controls[0]
    else:
        raise WinGuiAutoError("No control found for topHwnd=" +
                              repr(topHwnd) +
                              ", wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction))


def findControls(topHwnd,
                 wantedText=None,
                 wantedClass=None,
                 selectionFunction=None):
    '''Find controls.
    
    You can identify controls using captions, classes, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)

    Parameters
    ----------
    topHwnd             
        The window handle of the top level window in which the
        required controls reside.
    wantedText          
        Text which the required controls' captions must contain.
    wantedClass         
        Class to which the required controls must belong.
    selectionFunction   
        Control selection function. Reference to a function
        should be passed here. The function should take hwnd as
        an argument, and should return True when passed the
        hwnd of a desired control.

    Returns
    -------
    The window handles of the controls matching the
    supplied selection criteria.    

    Usage example::

        optDialog = findTopWindow(wantedText="Options")
        def findButtons(hwnd, windowText, windowClass):
            return windowClass == "Button"
        buttons = findControl(optDialog, wantedText="Button")
    '''

    def searchChildWindows(currentHwnd):
        results = []
        childWindows = []
        try:
            win32gui.EnumChildWindows(currentHwnd,
                                      _windowEnumerationHandler,
                                      childWindows)
        except win32gui.error:
            # This seems to mean that the control *cannot* have child windows,
            # i.e. not a container.
            return
        for childHwnd, windowText, windowClass in childWindows:
            descendentMatchingHwnds = searchChildWindows(childHwnd)
            if descendentMatchingHwnds:
                results += descendentMatchingHwnds

            if wantedText and \
                    not _normaliseText(wantedText) in _normaliseText(windowText):
                continue
            if wantedClass and \
                    not windowClass == wantedClass:
                continue
            if selectionFunction and \
                    not selectionFunction(childHwnd):
                continue
            results.append(childHwnd)
        return results

    return searchChildWindows(topHwnd)


def clickButton(hwnd):
    '''Simulates a single mouse click on a button

    Parameters
    ----------
    hwnd
        Window handle of the required button.

    Usage example::

        okButton = findControl(fontDialog,
                               wantedClass="Button",
                               wantedText="OK")
        clickButton(okButton)
    '''
    _sendNotifyMessage(hwnd, win32con.BN_CLICKED)


def click(hwnd):
    '''
    模拟鼠标左键单击
    :param hwnd: 要单击的控件、窗体句柄
    :return:
    '''
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, None, None)
    time.sleep(.2)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, None, None)


def focusWindow(hwnd):
    '''
    捕捉窗口焦点
    :param hwnd: 窗体句柄
    :return:
    '''
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
    win32gui.SetForegroundWindow(hwnd)


def sendKey(hwnd, key_code):
    '''
    模拟按键
    :param hwnd: 窗体句柄
    :param key_code: 按键码，在win32con下，比如win32con.VK_F1
    :return:
    '''
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)  # 消息键盘
    time.sleep(.2)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)


def clickStatic(hwnd):
    '''Simulates a single mouse click on a static

    Parameters
    ----------
    hwnd
        Window handle of the required static.

    Usage example:  TODO
    '''
    _sendNotifyMessage(hwnd, win32con.STN_CLICKED)


def doubleClickStatic(hwnd):
    '''Simulates a double mouse click on a static

    Parameters
    ----------
    hwnd
        Window handle of the required static.

    Usage example:  TODO
    '''
    _sendNotifyMessage(hwnd, win32con.STN_DBLCLK)


# def getEditText(hwnd):
#     bufLen = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0) + 1
#     print(bufLen)
#     buffer = win32gui.PyMakeBuffer(bufLen)
#     win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, bufLen, buffer)
#
#     text = buffer[:bufLen]
#     return text


def getWindowText(hwnd):
    return win32gui.GetWindowText(hwnd)


def setEditText(hwnd, text):
    '''
    设置Edit控件的文本，这个只能是单行文本
    :param hwnd: Edit控件句柄
    :param text: 要设置的文本
    :return:
    '''
    win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, None, text)


# def setEditText(hwnd, text, append=False):
#     '''Set an edit control's text.
#
#     Parameters
#     ----------
#     hwnd
#         The edit control's hwnd.
#     text
#         The text to send to the control. This can be a single
#         string, or a sequence of strings. If the latter, each will
#         be become a a seperate line in the control.
#     append
#         Should the new text be appended to the existing text?
#         Defaults to False, meaning that any existing text will be
#         replaced. If True, the new text will be appended to the end
#         of the existing text.
#         Note that the first line of the new text will be directly
#         appended to the end of the last line of the existing text.
#         If appending lines of text, you may wish to pass in an
#         empty string as the 1st element of the 'text' argument.
#
#     Usage example::
#
#         print "Enter various bits of text."
#         setEditText(editArea, "Hello, again!")
#         time.sleep(.5)
#         setEditText(editArea, "You still there?")
#         time.sleep(.5)
#         setEditText(editArea, ["Here come", "two lines!"])
#         time.sleep(.5)
#
#         print "Add some..."
#         setEditText(editArea, ["", "And a 3rd one!"], append=True)
#         time.sleep(.5)
#     '''

# Ensure that text is a list
# try:
#     text + ''
#     text = [text]
# except TypeError:
#     pass
#
# # Set the current selection range, depending on append flag
# if append:
#     win32gui.SendMessage(hwnd,
#                          win32con.EM_SETSEL,
#                          -1,
#                          0)
# else:
#     win32gui.SendMessage(hwnd,
#                          win32con.EM_SETSEL,
#                          0,
#                          -1)
#
# # Send the text
# win32gui.SendMessage(hwnd,
#                      win32con.EM_REPLACESEL,
#                      True,
#                      os.linesep.join(text))


def _windowEnumerationHandler(hwnd, resultList):
    '''Pass to win32gui.EnumWindows() to generate list of window handle,
    window text, window class tuples.'''
    resultList.append((hwnd,
                       win32gui.GetWindowText(hwnd),
                       win32gui.GetClassName(hwnd)))


def _buildWinLong(high, low):
    '''Build a windows long parameter from high and low words.
    See http://support.microsoft.com/support/kb/articles/q189/1/70.asp
    '''
    # return ((high << 16) | low)
    return int(struct.unpack('>L',
                             struct.pack('>2H',
                                         high,
                                         low))[0])


def _sendNotifyMessage(hwnd, nofifyMessage):
    '''Send a notify message to a control.'''
    win32gui.SendMessage(win32gui.GetParent(hwnd),
                         win32con.WM_COMMAND,
                         _buildWinLong(nofifyMessage,
                                       win32api.GetWindowLong(hwnd,
                                                              win32con.GWL_ID)),
                         hwnd)


def _normaliseText(controlText):
    '''Remove '&' characters, and lower case.
    Useful for matching control text.'''
    return controlText.lower().replace('&', '')


class Bunch(object):
    '''See http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308'''

    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __str__(self):
        state = ["%s=%r" % (attribute, value)
                 for (attribute, value)
                 in list(self.__dict__.items())]
        return '\n'.join(state)


class WinGuiAutoError(Exception):
    pass

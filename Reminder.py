#! env python
# -*- coding: utf-8 -*-

import webbrowser
import wx
from time import sleep

# gcal_tool.Reminder
# Date: 2018/11/03
# Filename: Reminder 

__author__ = 'takutohasegawa'
__date__ = "2018/11/03"

url = 'https://calendar.google.com/'
webbrowser.open(url)
app = wx.App()
sleep(5)
wx.MessageBox('実績の入力を忘れずに。')


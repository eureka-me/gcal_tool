#! env python
# -*- coding: utf-8 -*-

import os
import sys
import configparser
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter

from module import GetGcalInfo as ggi
from module import ProcessGcalData as pgd
from module import UploadFile as uf

# gcal_manager.Main
# Date: 2018/04/14
# Filename: main 

__author__ = 'takutohasegawa'
__date__ = "2018/04/14"

logger = getLogger('')
fileHandler = FileHandler(__file__.replace('py', 'log'))
fileHandler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
streamHandler = StreamHandler()
streamHandler.setLevel(DEBUG)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.setLevel(DEBUG)

config = configparser.ConfigParser()
config.read_file(open('./config.conf', 'r', encoding='UTF-8'))

GetGcalInfo = ggi.GetGcalInfo(config)
ProcessGcalData = pgd.ProcessGcalData(config)

# 期間の取得
time_min, time_max = GetGcalInfo.get_time_min_max()

# Google Calendar情報の取得
work_plan_info = GetGcalInfo.get_gcal_info(config['RETRIEVE']['WORK_PLAN_CAL_ID'],
                                           time_min=time_min, time_max=time_max)
work_result_info = GetGcalInfo.get_gcal_info(config['RETRIEVE']['WORK_RESULT_CAL_ID'],
                                             time_min=time_min, time_max=time_max)
# life_plan_info = GetGcalInfo.get_gcal_info(config['RETRIEVE']['LIFE_PLAN_CAL_ID'])
life_result_info = GetGcalInfo.get_gcal_info(config['RETRIEVE']['LIFE_RESULT_CAL_ID'],
                                             time_min=time_min, time_max=time_max)

# 各カテゴリに対する時間投入量の集計し、csvファイルを出力（Life）
ProcessGcalData.output_work_life_result(work_result_info=work_result_info, life_result_info=life_result_info,
                                        time_min=time_min, time_max=time_max)

ProcessGcalData.output_work_plan_result(work_plan_info=work_plan_info, work_result_info=work_result_info,
                                        time_min=time_min, time_max=time_max)

ProcessGcalData.output_life_timeline(work_result_info=work_result_info, life_result_info=life_result_info,
                                     time_min=time_min, time_max=time_max)

#! env python
# -*- coding: utf-8 -*-

from module import GetGcalInfo as ggi
from module import ProcessGcalData as pgd
import configparser, csv
import datetime as dt
from collections import defaultdict
from module.Tools import Tools as tl
import pandas as pd

# gcal_tool.nippou
# Date: 2018/05/18
# Filename: nippou

config = configparser.ConfigParser()
config.read_file(open('./config.conf', 'r', encoding='UTF-8'))
GetGcalInfo = ggi.GetGcalInfo(config)

__author__ = 'takutohasegawa'
__date__ = "2018/05/18"


def output_nippou_file(_date):

    # work_result_infoの取得
    time_min, time_max = GetGcalInfo.get_time_min_max(dt.datetime.strptime(_date, '%Y%m%d'))
    work_result_info, _ = GetGcalInfo.get_gcal_info(config['RETRIEVE']['WORK_RESULT_CAL_ID'],
                                                 time_min=time_min, time_max=time_max)

    # categoryで集計
    PGD = pgd.ProcessGcalData(config, _date)
    result_dic = PGD.summarize_calendar_info(calendar_info=work_result_info, cate_scope=10, dic=defaultdict(float))

    # 出力用データフレームの作成
    genre_unique = sorted(set([g for (g, __date) in result_dic.keys()]))
    _dic = defaultdict(lambda: ['' for _ in range(len(genre_unique))])
    for (g, __date), _time in result_dic.items():
        _dic[__date[5:]][genre_unique.index(g)] = _time/60
    _dic = {k: l + [sum([v for v in l if v != ''])] for k, l in _dic.items()}
    _dic['sum'] = [sum([v[i] for v in _dic.values() if v[i] != '']) for i in range(len(genre_unique)+1)]
    df_out = pd.DataFrame(_dic)
    df_out.index = genre_unique + ['sum']

    # ファイル出力
    week = tl.get_week(dt.datetime.strptime(_date, '%Y%m%d'))
    df_out.to_csv('./nippou/{}.csv'.format(week))


if __name__ == '__main__':
    output_nippou_file('20181031')

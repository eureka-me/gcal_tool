#! env python
# -*- coding: utf-8 -*-

import csv
import datetime as dt
from logging import getLogger
from collections import defaultdict
from module import Tools
import plotly.offline as po
import plotly.graph_objs as go

# gcal_manager.ProcessGcalData
# Date: 2018/04/14
# Filename: ProcessGcalData 

__author__ = 'takutohasegawa'
__date__ = "2018/04/14"


class ProcessGcalData:
    def __init__(self, config):
        self.config = config
        self.logger = getLogger(__name__)
        self.Tools = Tools.Tools(config)
        self.category_dic = self.Tools.get_category_dic()

    def summarize_work_life_result(self, work_result_info, life_result_info):
        """各項目に対する時間投入量の集計"""

        dic = defaultdict(float)
        for result_info in [work_result_info, life_result_info]:
            for event in result_info:
                if 'summary' not in event:
                    continue
                cate = event['summary'].split('/')[0]
                if cate in self.category_dic.keys():
                    _min = (dt.datetime.strptime(event['end']['dateTime'], '%Y-%m-%dT%H:%M:%S+09:00') -
                            dt.datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S+09:00')).seconds / 60
                    dic[self.category_dic[cate]['abbr']] += _min

        fout = open(self.config['GENERAL']['FILE_DIR'] + 'category_summary_life.csv', 'w', encoding='SJIS')
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        writer.writerow(['category_abbr', 'category_note', 'minute'])
        for cate_abbr, _min in dic.items():
            writer.writerow([cate_abbr, self.category_dic[cate_abbr]['note'], _min])
        fout.close()

        # TODO: カレンダー情報に更新があったかどうかの判定機能
        return True

    def update_summarize_work_life_result_html(self):
        """各項目に対する時間投入量の集計結果ファイルの更新"""

        # データの読み込み
        dic = {}
        with open(self.config['GENERAL']['FILE_DIR'] + 'category_summary_life.csv', 'r') as f:

            reader = csv.reader(f)
            header = next(reader)
            ix = {h: i for i, h in enumerate(header)}

            for row in reader:
                dic[(row[ix['category_abbr']], row[ix['category_note']])] = float(row[ix['minute']])

        data = [go.Bar(
            x=[k[1] for k in dic.keys()],
            y=list(dic.values()),
            text=list(dic.values()),
            textposition='auto',
            marker=dict(color='rgb(158,202,225)', line=dict(color='rgb(8,48,107)', width=1.5),),
            opacity=0.6
        )]

        layout = go.Layout(
            xaxis=dict(
                tickangle=90,
            ),
        )

        fig = go.Figure(data=data, layout=layout)
        po.plot(fig, filename=self.config['GENERAL']['UPLOAD_DIR'] + 'test.html', auto_open=False)















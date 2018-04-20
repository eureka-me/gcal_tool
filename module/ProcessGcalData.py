#! env python
# -*- coding: utf-8 -*-

import csv
import datetime as dt
from logging import getLogger
from collections import defaultdict
from module import Tools
import plotly.offline as po
import plotly.graph_objs as go
import plotly.figure_factory as ff

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
        self.category_dic, self.abbr_display = self.Tools.get_category_dic()

    def output_work_life_result(self, work_result_info, life_result_info, time_min, time_max):

        if self.summarize_work_life_result(work_result_info, life_result_info):
            self.update_summarize_work_life_result_html(time_min, time_max)

    def summarize_work_life_result(self, work_result_info, life_result_info):
        """各項目に対する時間投入量の集計"""

        dic = defaultdict(float)
        for result_info in [work_result_info, life_result_info]:
            dic = self.summarize_calendar_info(calendar_info=result_info, cate_scope=1, dic=dic)

        fout = open(self.config['GENERAL']['FILE_DIR'] + 'category_summary_life.csv', 'w', encoding='SJIS')
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        writer.writerow(['category_abbr', 'category_note', 'minute'])
        for _abbr in self.abbr_display:
            writer.writerow([_abbr, self.category_dic[_abbr]['note'], dic[_abbr]])
        fout.close()

        # TODO: カレンダー情報に更新があったかどうかの判定機能
        return True

    def summarize_calendar_info(self, calendar_info, cate_scope, dic):
        """カレンダーオブジェクトを受け取り、辞書に格納"""

        for event in calendar_info:
            if 'summary' not in event:
                continue

            if cate_scope == 1:
                cate = event['summary'].split('/')[0]
                if cate not in self.category_dic.keys():
                    continue

            elif cate_scope == 2:
                cate = tuple(event['summary'].split('/')[:2])
                if cate[0] not in self.category_dic.keys():
                    continue

            elif cate_scope < 0:
                cate = tuple(event['summary'].split('/'))
            else:
                raise Exception('cate_scope is wrong.')

            _min = (dt.datetime.strptime(event['end']['dateTime'], '%Y-%m-%dT%H:%M:%S+09:00') -
                    dt.datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S+09:00')).seconds / 60

            if cate_scope == 1:
                dic[self.category_dic[cate]['abbr']] += _min
            elif cate_scope == 2:
                dic[cate] += _min

        return dic

    def update_summarize_work_life_result_html(self, time_min, time_max):
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
            text=self.format_value_label(dic.values()),
            textposition='auto',
            marker=dict(color='rgb(158,202,225)', line=dict(color='rgb(8,48,107)', width=1.5),),
            opacity=0.6
        )]

        layout = go.Layout(
            title='time input<br>{0}-{1}'.format(time_min.strftime('%Y/%m/%d(%a)'),
                                                   (time_max - dt.timedelta(days=1)).strftime('%Y/%m/%d(%a)')),
            xaxis=dict(
                tickangle=90,
            ),
        )

        fig = go.Figure(data=data, layout=layout)
        po.plot(fig, filename=self.config['GENERAL']['UPLOAD_DIR'] + 'life_work_result.html', auto_open=False)

    def output_work_plan_result(self, work_plan_info, work_result_info, time_min, time_max):
        """仕事に関する項目に関して予定時間に対する実績時間の進捗状況を集計し、htmlファイルを出力"""

        update, plan_dic, result_dic, abbr_note_dic = self.summarize_work_plan_result(work_plan_info, work_result_info)
        if update:
            self.update_work_plan_result_html(plan_dic, result_dic, time_min, time_max, abbr_note_dic)

    def summarize_work_plan_result(self, work_plan_info, work_result_info):
        """仕事に関する各項目に対する予定時間に対する実績時間の進捗状況を集計し、csv出力"""

        plan_dic = self.summarize_calendar_info(calendar_info=work_plan_info, cate_scope=2, dic=defaultdict(float))
        result_dic = self.summarize_calendar_info(calendar_info=work_result_info, cate_scope=2, dic=defaultdict(float))
        abbr_note_dic = self.get_abbr_note_dic(work_plan_info=work_plan_info, work_result_info=work_result_info)

        # TODO: カレンダー情報に更新があったかどうかの判定機能
        return True, plan_dic, result_dic, abbr_note_dic

    @staticmethod
    def get_abbr_note_dic(work_plan_info, work_result_info):
        """abbrのnoteを示す辞書の取得"""

        dic = defaultdict(str)
        for event in work_plan_info:
            _event = event['summary'].split('/')
            if _event[0] != 'w':
                continue
            if dic[_event[1]] == '':
                dic[_event[1]] = _event[2]

        for event in work_result_info:
            _event = event['summary'].split('/')
            if _event[0] != 'w':
                continue
            if dic[_event[1]] == '':
                dic[_event[1]] = _event[2]

        return dic

    def update_work_plan_result_html(self, plan_dic, result_dic, time_min, time_max, abbr_note_dic):
        """htmlファイルを更新"""

        x = sorted(list(set([k[1] for k in plan_dic.keys() if k[0] == 'w']
                            + [k[1] for k in result_dic.keys() if k[0] == 'w'])), reverse=True)

        y_p = [plan_dic[('w', c)] for c in x]
        y_r = [result_dic[('w', c)] for c in x]
        y_progress = ['{}%'.format(round(r*100/p)) if p > 0 else '-%' for p, r in zip(y_p, y_r)]

        trace_p = go.Bar(
            x=y_p,
            y=x,
            text=self.format_value_label(y_p),
            textposition='auto',
            marker=dict(color='rgb(158,202,225)', line=dict(color='rgb(8,48,107)', width=1.5), ),
            opacity=0.6,
            name='plan',
            orientation='h',
            xaxis='x2', yaxis='y2'
        )

        trace_r = go.Bar(
            x=y_r,
            y=x,
            text=['{0},{1}'.format(r, p) for r, p in zip(self.format_value_label(y_r), y_progress)],
            textposition='auto',
            marker=dict(color='rgb(255,200,132)', line=dict(color='rgb(165,100,12)', width=1.5), ),
            opacity=0.6,
            name='result',
            orientation='h',
            xaxis='x2', yaxis='y2'
        )

        table_domain = float(self.config['PROCESS']['TABLE_DOMAIN'])
        table_height = int(self.config['PROCESS']['TABLE_HEIGHT'])

        table = [['abbr', 'note']]
        for _x in sorted(x):
            table.append([_x, abbr_note_dic[_x]])
        fig = ff.create_table(table, height_constant=table_height)
        # fig = go.Figure(data=trace_table)

        fig['data'].extend(go.Data([trace_r, trace_p]))
        fig.layout.yaxis.update({'domain': [0, table_domain]})
        fig.layout.yaxis2.update({'domain': [table_domain + 0.05, 1]})

        fig.layout.yaxis2.update({'anchor': 'x2'})
        fig.layout.xaxis2.update({'anchor': 'y2'})

        height = table_height*len(x)/table_domain
        fig.layout.update({'height': height,
                           'legend': dict(orientation='h')
                           })

        fig.layout.margin.update({'t': 100, 'r': 30, 'l': 30})
        fig.layout.update({'title': 'plan result<br>{0}-{1}<br>{2}h {3}min / {4}h {5}min ({6}%)'
                          .format(time_min.strftime('%Y/%m/%d(%a)'),
                                  (time_max - dt.timedelta(days=1)).strftime('%m/%d(%a)'),
                                  int(sum(y_r) // 60), int(sum(y_r) % 60),
                                  int(sum(y_p) // 60), int(sum(y_p) % 60),
                                  round(sum(y_r)*100/sum(y_p)))})
        po.plot(fig, filename=self.config['GENERAL']['UPLOAD_DIR'] + 'work_plan_result.html', auto_open=False,
                config={'displayModeBar': False})

    @staticmethod
    def format_value_label(vl):
        """棒グラフの数値のリストをラベルの形式に変換"""

        labels = []
        for v in vl:
            if v >= 60:
                if v % 60 != 0:
                    labels.append("{0}h {1}m".format(int(v // 60), int(v % 60)))
                else:
                    labels.append("{0}h".format(int(v // 60)))
            else:
                labels.append("{}m".format(int(v)))

        return labels



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
import textwrap

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

        update, plan_dic, result_dic, abbr_note_dic, complete_tasks\
            = self.summarize_work_plan_result(work_plan_info, work_result_info)
        if update:
            self.update_work_plan_result_html(plan_dic, result_dic, time_min, time_max, abbr_note_dic, complete_tasks)

    def summarize_work_plan_result(self, work_plan_info, work_result_info):
        """仕事に関する各項目に対する予定時間に対する実績時間の進捗状況を集計し、csv出力"""

        complete_tasks, work_result_info = self.get_complete_tasks(work_result_info=work_result_info)

        plan_dic = self.summarize_calendar_info(calendar_info=work_plan_info, cate_scope=2, dic=defaultdict(float))
        result_dic = self.summarize_calendar_info(calendar_info=work_result_info, cate_scope=2, dic=defaultdict(float))

        abbr_note_dic = self.get_abbr_note_dic(work_plan_info=work_plan_info, work_result_info=work_result_info)

        # TODO: カレンダー情報に更新があったかどうかの判定機能
        return True, plan_dic, result_dic, abbr_note_dic, complete_tasks

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

    @staticmethod
    def get_complete_tasks(work_result_info):

        complete_tasks = []
        for i, event in enumerate(work_result_info):
            _event = event['summary'].split('/')
            if _event[0] != 'w':
                continue
            if '@d@' in event['summary']:
                complete_tasks.append(_event[1])
                work_result_info[i]['summary'] = work_result_info[i]['summary'].replace('@d@', '')

        return complete_tasks, work_result_info

    def update_work_plan_result_html(self, plan_dic, result_dic, time_min, time_max, abbr_note_dic, complete_tasks):
        """htmlファイルを更新"""

        x = sorted(list(set([k[1] for k in plan_dic.keys() if k[0] == 'w']
                            + [k[1] for k in result_dic.keys() if k[0] == 'w'])), reverse=True)

        y_p = [plan_dic[('w', c)] for c in x]
        y_r = [result_dic[('w', c)] for c in x]
        y_progress = ['{}%'.format(round(r*100/p)) if p > 0 else '-%' for p, r in zip(y_p, y_r)]

        trace_p = go.Bar(
            x=y_p,
            y=[self.twrap(_x + ', ' + abbr_note_dic[_x]) for _x in x],
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
            y=[self.twrap(_x+ ', ' + abbr_note_dic[_x]) for _x in x],
            text=['{0},{1}'.format(r, p) for r, p in zip(self.format_value_label(y_r), y_progress)],
            textposition='auto',
            marker=dict(color=['rgb(255,200,132)' if _x in complete_tasks else 'rgb(255,255,255)' for _x in x],
                        line=dict(color='rgb(165,100,12)',
                                  width=1.5), ),
            opacity=0.6,
            name='result',
            orientation='h',
            xaxis='x2', yaxis='y2',
        )

        table_domain = float(self.config['PROCESS']['TABLE_DOMAIN'])
        table_height = int(self.config['PROCESS']['TABLE_HEIGHT'])

        table = [['abbr', 'note']]
        for _x in sorted(x):
            table.append([_x, abbr_note_dic[_x]])
        fig = ff.create_table(table, height_constant=table_height)

        fig['data'].extend(go.Data([trace_r, trace_p]))
        fig.layout.yaxis.update({'domain': [0, table_domain]})
        fig.layout.yaxis2.update({'domain': [table_domain + 0.05, 1]})

        fig.layout.yaxis2.update({'anchor': 'x2'})
        fig.layout.xaxis2.update({'anchor': 'y2'})

        height = table_height*len(x)/table_domain
        fig.layout.update({'height': height,
                           'legend': dict(orientation='h')
                           })

        fig.layout.margin.update({'t': 100, 'r': 30, 'l': 100})
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

    def output_life_timeline(self, work_result_info, life_result_info, time_min, time_max):
        tl_dic = self.summarize_life_timeline(work_result_info=work_result_info, life_result_info=life_result_info)
        self.update_life_timeline(tl_dic, time_min, time_max)

    def summarize_life_timeline(self, work_result_info, life_result_info):

        # まずは1日単位に分割
        events = work_result_info + life_result_info
        _first_date = min([self.Tools.convert_datetime(event['end']['dateTime'])
                           for event in events if 'dateTime' in event['end']])
        first_date = dt.datetime(_first_date.year, _first_date.month, _first_date.day)

        _st_time, _en_time = first_date, first_date + dt.timedelta(days=1)
        date_event_dic = defaultdict(list)
        while _st_time < first_date + dt.timedelta(days=7):
            for event in events:
                if 'dateTime' not in event['start']:
                    continue

                st_time = self.Tools.convert_datetime(event['start']['dateTime'])
                en_time = self.Tools.convert_datetime(event['end']['dateTime'])
                if (_st_time <= st_time < _en_time) or (_st_time < en_time <= _en_time):
                    date_event_dic[_st_time].append(event)

            _st_time += dt.timedelta(days=1)
            _en_time += dt.timedelta(days=1)

        tl_dic = defaultdict(lambda: {'date': [], 'length': [], 'base': []})
        for _date, events in date_event_dic.items():
            for event in events:
                cate = self.decide_category(event)
                length = self.get_length(_date, event)
                base = self.get_base(_date, event)
                tl_dic[cate]['date'].append(_date.strftime('%m-%d(%a)'))
                tl_dic[cate]['length'].append(length)
                tl_dic[cate]['base'].append(base)

        return tl_dic

    @staticmethod
    def decide_category(event):
        cate_list = event['summary'].split('/')
        if cate_list[0] in ['w', 'W']:
            return 'work'
        elif cate_list[0] in ['l', 's', 'fw', 'i', 'L', 'S', 'Fw', 'I', 'F']:
            return 'private'
        elif event['summary'] in ['睡眠']:
            return 'sleep'
        else:
            return 'other'

    def get_length(self, _date, event):
        st_time = self.Tools.convert_datetime(event['start']['dateTime'])
        en_time = self.Tools.convert_datetime(event['end']['dateTime'])
        length_time = min(en_time, _date + dt.timedelta(days=1)) - max(st_time, _date)
        return int(length_time.seconds // 60)

    def get_base(self, _date, event):
        st_time = self.Tools.convert_datetime(event['start']['dateTime'])
        base_datetime = max(st_time, _date)
        return (base_datetime - _date).seconds // 60

    def update_life_timeline(self, tl_dic, time_min, time_max):

        color_dic = {'work': 'rgb(218,98,144)', 'private': 'rgb(243,199,89)',
                     'other': 'rgb(164,197,32)', 'sleep': 'rgb(69,161,207)'}

        data = []
        for cate, _dic in tl_dic.items():
            data.append(
                go.Bar(
                    y=_dic['length'],
                    x=_dic['date'],
                    base=_dic['base'],
                    # orientation='h',
                    name=cate,
                    marker=dict(
                        color=color_dic[cate],
                    ),
                    opacity=0.8
                )
            )

        layout = go.Layout(
            title='time input<br>{0}-{1}'.format(time_min.strftime('%Y/%m/%d(%a)'),
                                                   (time_max - dt.timedelta(days=1)).strftime('%Y/%m/%d(%a)')),
            barmode='stack',
            # legend=dict(orientation='h'),
            margin={'t': 100, 'b': 100},
            yaxis=dict(
                autorange='reversed',
                tickvals=list(range(0, 1500, 60)),
                ticktext=list(range(0, 25)),
                gridcolor='rgb(97,97,97)',
                gridwidth=0.5,
                ),

        )

        fig = go.Figure(data=data, layout=layout)
        po.plot(fig, filename=self.config['GENERAL']['UPLOAD_DIR'] + 'life_timeline.html', auto_open=False)

    @staticmethod
    def twrap(txt):
        txtlist = textwrap.wrap(txt, width=8)
        return '<br>'.join(txtlist)

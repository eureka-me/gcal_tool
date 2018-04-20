#! env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import csv
import datetime as dt

# gcal_manager.Tools
# Date: 2018/04/16
# Filename: Tools 

__author__ = 'takutohasegawa'
__date__ = "2018/04/16"


class Tools:
    def __init__(self, config):
        self.config = config

    def get_category_dic(self):

        dic, abbr_display = defaultdict(dict), []
        with open(self.config['GENERAL']['CATEGORY_DIC_FILE_PATH'], 'r') as f:

            reader = csv.reader(f)
            header = next(reader)
            ix = {h: i for i, h in enumerate(header)}

            for row in reader:
                variables = row[ix['variants']].split('/')
                for variable in variables:
                    dic[variable]['abbr'] = row[ix['abbr']]
                    dic[variable]['note'] = row[ix['note']]
                abbr_display.append((row[ix['abbr']], int(row[ix['disp_order']])))

        return dic, [_abbr[0] for _abbr in sorted(abbr_display, key=lambda x: x[1])]

    @staticmethod
    def convert_datetime(datetime_str):
        return dt.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S+09:00')

#! env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os, sys, configparser
import httplib2
import os
from logging import getLogger

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import datetime as dt

from module import Tools

# gcal_manager.GetGcalInfo
# Date: 2018/04/14
# Filename: GetGcalInfo

__author__ = 'takutohasegawa'
__date__ = "2018/04/14"

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


class GetGcalInfo:
    def __init__(self, config):
        self.config = config
        self.logger = getLogger(__name__)
        self.Tools = Tools.Tools(config)

    def get_gcal_info(self, calendar_id, time_min, time_max, evaluation=False):
        """google calendarデータを取得する"""

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        time_min_max_list = self.get_time_min_max_list(time_min, time_max)
        events = []
        for _time_min, _time_max in time_min_max_list:

            _time_min_s = (_time_min - dt.timedelta(hours=9+6)).isoformat() + 'Z'
            _time_max_s = (_time_max - dt.timedelta(hours=9)).isoformat() + 'Z'

            eventsResult = service.events().list(
                calendarId=calendar_id, timeMin=_time_min_s, timeMax=_time_max_s, singleEvents=True,
                orderBy='startTime').execute()
            events.extend(eventsResult.get('items', []))

        if evaluation is False:
            _events = []
            for event in events:
                if 'dateTime' not in event['start']:
                    continue

                st_time = self.Tools.convert_datetime(event['start']['dateTime'])
                en_time = self.Tools.convert_datetime(event['end']['dateTime'])
                if time_min <= st_time < time_max:
                    if time_max < en_time:
                        event['end']['dateTime'] = time_max.strftime('%Y-%m-%dT%H:%M:%S+09:00')
                    _events.append(event)
                elif time_min < en_time <= time_max:
                    event['start']['dateTime'] = time_min.strftime('%Y-%m-%dT%H:%M:%S+09:00')
                    _events.append(event)
        else:
            _events = events

        # latest_updateの取得
        if len(_events) > 0:
            latest_update = max([dt.datetime.strptime(e['updated'][:-5], '%Y-%m-%dT%H:%M:%S') for e in _events]) \
                            + dt.timedelta(hours=9)
        else:
            latest_update = dt.datetime(1990, 1, 1, 0, 0, 0)

        return _events, latest_update

    @staticmethod
    def get_time_min_max(_datetime):
        """集計の開始・終了時刻の取得"""
        # 土曜日始まり！！

        # time_minの生成
        _year, _month, _day = _datetime.year, _datetime.month, _datetime.day
        days_diff = (_datetime.weekday() + 2) % 7
        saturday = dt.datetime(_year, _month, _day) - dt.timedelta(days=days_diff)
        time_min = saturday
        time_max = saturday + dt.timedelta(days=7)

        return time_min, time_max

    @staticmethod
    def get_credentials():
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'calendar-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    @staticmethod
    def get_time_min_max_list(time_min, time_max):

        time_min_temp, lst = time_min, []
        while (time_max - time_min_temp).days > 30:
            lst.append((time_min_temp, time_min_temp + dt.timedelta(days=30)))
            time_min_temp += dt.timedelta(days=30)
        lst.append((time_min_temp, time_max))

        return lst

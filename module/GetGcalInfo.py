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

import datetime

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

    def get_gcal_info(self, calendar_id):
        """google calendarデータを取得する"""

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        _timeMin = datetime.datetime.utcnow() - datetime.timedelta(days=int(self.config['RETRIEVE']['EVENT_DAYS_FROM']))
        timeMin = _timeMin.isoformat() + 'Z'

        try:
            eventsResult = service.events().list(
                calendarId=calendar_id, timeMin=timeMin, singleEvents=True,
                orderBy='startTime').execute()
            events = eventsResult.get('items', [])

        except Exception as e:
            self.logger.error(e)
            events = []

        return events

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


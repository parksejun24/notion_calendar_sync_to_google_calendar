import os.path
import json
import datetime
import time

from pprint import pprint
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]
creds = None
if os.path.exists("private/token.json"):
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
  else:
    flow = InstalledAppFlow.from_client_secrets_file(
        "private/credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)


#--------------- 여기까지 google calendar Api 초기 설정 ------------------#

def make_easy_form_data(data_list, format):
  if format == 'notion':
    notion_TempDataList = []
    for data in data_list:
      if safe_get(data,'start.date') is None:
        notion_TempDataList.append({
          'summary' : safe_get(data,'summary'),
          'start' : safe_get(data,'start.dateTime').replace('.000',''),
          'end' : safe_get(data,'end.dateTime').replace('.000',''),
          'id' : safe_get(data,'description')
        })

      else :
        notion_TempDataList.append({
          'summary' : safe_get(data,'summary'),
          'start' : safe_get(data,'start.date'),
          'end' : safe_get(data,'end.date'),
          'id' : safe_get(data,'description')
        })
    return notion_TempDataList

  elif format == 'google':
    google_tempDataList = []
    for data in data_list:
      if safe_get(data,'start.date') is None:
        google_tempDataList.append(
          {
            'summary' : safe_get(data,'summary'),
            'start' : safe_get(data,'start.dateTime'),
            'end' : safe_get(data,'end.dateTime'),
            'id' : safe_get(data,'description')
          }
        )
      else:
        google_tempDataList.append(
          {
            'summary' : safe_get(data,'summary'),
            'start' : safe_get(data,'start.date'),
            'end' : safe_get(data,'end.date'),
            'id' : safe_get(data,'description')
          }
        )
    return google_tempDataList

def safe_get(data, dot_chain):
    keys = dot_chain.split('.')
    for key in keys:
        try:
            if isinstance(data, list):
                data = data[int(key)]
            else:
                data = data[key]
        except (KeyError,TypeError,IndexError):
            return None
    return data


def first_sync_calendar(notion_calendar_data, calendar_id):
  try:
    google_events_data=[]
    service = build("calendar", "v3", credentials=creds)
    if safe_get(notion_calendar_data,'0.start.date') is None :
      google_events_tmp = service.events().list(calendarId=calendar_id,
                                                timeMin=notion_calendar_data[0]['start']['dateTime'],
                                                maxResults=100, singleEvents=True,
                                                orderBy='startTime').execute() #조회 시작 시간 부터 100개 
      google_events_data += google_events_tmp.get('items', [])
      while safe_get(google_events_tmp,'nextPageToken') is not None:
        google_events_tmp = service.events().list(calendarId=calendar_id,
                                                timeMin=notion_calendar_data[0]['start']['dateTime'],
                                                pageToken=safe_get(google_events_tmp,'nextPageToken'),
                                                maxResults=100, singleEvents=True,
                                                orderBy='startTime').execute() #조회 시작 시간 부터 100개 
        google_events_data += google_events_tmp.get('items', [])

    else:
      google_events_tmp = service.events().list(calendarId=calendar_id,
                                                timeMin=notion_calendar_data[0]['start']['date']+'T00:00:00+09:00',
                                                maxResults=100, singleEvents=True,
                                                orderBy='startTime').execute()
      google_events_data += google_events_tmp.get('items', [])
      while safe_get(google_events_tmp,'nextPageToken') is not None:
        google_events_tmp = service.events().list(calendarId=calendar_id,
                                                timeMin=notion_calendar_data[0]['start']['date']+'T00:00:00+09:00',
                                                pageToken=safe_get(google_events_tmp,'nextPageToken'),
                                                maxResults=100, singleEvents=True,
                                                orderBy='startTime').execute()
        google_events_data += google_events_tmp.get('items', [])

    notion_TempDataList = make_easy_form_data(notion_calendar_data,'notion')
    google_TempDataList = make_easy_form_data(google_events_data,'google')
    
    notion_id_list = [id_tmp['id'] for id_tmp in notion_TempDataList]
    google_id_list = [id_tmp['id'] for id_tmp in google_TempDataList]

    syncAddData = []
    syncUpdateData = []

    for data_id in notion_id_list:
      if data_id not in google_id_list:
        notion_new_data = [data for data in notion_calendar_data if data['description']==data_id]
        notion_new_data = notion_new_data[0]
        syncAddData.append(notion_new_data)
      else:
        notion_same_id_data = [data for data in notion_TempDataList if data['id']==data_id]
        google_same_id_data = [data for data in google_TempDataList if data['id']==data_id]
        date = None
        if len(safe_get(google_same_id_data,'0.end'))>10:
          date = google_same_id_data[0]['end']
        else:
          date = google_same_id_data[0]['end']
          date = str(datetime.datetime.strptime(date,'%Y-%m-%d') - datetime.timedelta(days=1)).split(' ')[0]


        if notion_same_id_data[0]['summary']!=google_same_id_data[0]['summary'] or notion_same_id_data[0]['start']!=google_same_id_data[0]['start'] or notion_same_id_data[0]['end'] != date :
          notion_update_data = [data for data in notion_calendar_data if data['description']==data_id]
          notion_update_data = notion_update_data[0]
          syncUpdateData.append(notion_update_data)

    syncDeleteData = []

    for data_id in google_id_list:
      if data_id not in notion_id_list:
        google_delete_data = [data for data in google_events_data if data['description']==data_id]
        syncDeleteData.append(google_delete_data[0])


    for event in syncAddData:
      print('add :',event['description'])
      event = service.events().insert(calendarId=calendar_id, body=event).execute()

    for event in syncDeleteData:
      print('delete :',event['id'])
      event = service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()

    
    for event in syncUpdateData:
      print('update :',event['description'])
      event_google = [data for data in google_events_data if data['description']==event['description']]
      event_google = event_google[0]
    
      event_google['summary'] = event['summary']
      event_google['start'] = event['start']
      event_google['end'] = event['end']
      
      if safe_get(event_google,'end.date') is not None:
        date = event_google['end']['date']
        event_google['end']['date'] = str(datetime.datetime.strptime(date,'%Y-%m-%d') + datetime.timedelta(days=1)).split(' ')[0]

      event = service.events().update(calendarId=calendar_id, eventId=event_google['id'], body=event_google).execute()
  
  except HttpError as error:
    print(f"An error occurred: {error}")





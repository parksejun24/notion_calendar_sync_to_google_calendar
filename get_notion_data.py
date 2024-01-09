from dotenv import dotenv_values
from notion_client import Client
from pprint import pprint
from datetime import datetime

config = dotenv_values('private/.env')
notion_secret_token = config.get('NOTION_TOKEN')
notion = Client(auth=notion_secret_token)

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

def get_first_data():
    sort_option = []
    sort_option.append({'property':'Date', 'direction':'ascending'})
    notion_temp_data = notion.databases.query(database_id=config.get('DATABASE_ID'),sorts=sort_option)
    notion_full_data = notion_temp_data['results'][:]

    while notion_temp_data['has_more']:
        notion_temp_data = notion.databases.query(database_id=config.get('DATABASE_ID'),sorts=sort_option,start_cursor=notion_temp_data['next_cursor'])
        notion_full_data += notion_temp_data['results']
    #next cursor -> start cursor 를 반복해서 끝까지 받을수 있음
    
    notion_calendar_data = []
    for row in notion_full_data:
        title = safe_get(row,'properties.Name.title.0.plain_text')
        start_date = safe_get(row,'properties.Date.date.start')
        end_date = safe_get(row,'properties.Date.date.end')
        data_id = safe_get(row,'id')
        if len(start_date)>10 :
            if end_date is not None:
                notion_calendar_data.append({
                    'summary' : title,
                    'description' : data_id,
                    'start' : {
                        'dateTime' : start_date,
                        'timeZone': 'Asia/Seoul'
                    },
                    'end' : {
                        'dateTime' : end_date,
                        'timeZone': 'Asia/Seoul'
                    }
                })
            else :
                notion_calendar_data.append({
                    'summary' : title,
                    'description' : data_id,
                    'start' : {
                        'dateTime' : start_date,
                        'timeZone': 'Asia/Seoul'
                    },
                    'end' : {
                        'dateTime' : start_date,
                        'timeZone': 'Asia/Seoul'
                    }
                })
        else:
            if end_date is not None:
                notion_calendar_data.append({
                    'summary' : title,
                    'description' : data_id,
                    'start' : {
                        'date' : start_date,
                        'timeZone': 'Asia/Seoul'
                    },
                    'end' : {
                        'date' : end_date,
                        'timeZone': 'Asia/Seoul'
                    }
                })
            else:
                notion_calendar_data.append({
                    'summary' : title,
                    'description' : data_id,
                    'start' : {
                        'date' : start_date,
                        'timeZone': 'Asia/Seoul'
                    },
                    'end' : {
                        'date' : start_date,
                        'timeZone': 'Asia/Seoul'
                    }
                })

    return notion_calendar_data

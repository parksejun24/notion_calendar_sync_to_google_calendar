from dotenv import dotenv_values
from notion_client import Client
from pprint import pprint
from datetime import datetime
import load_google_calender
import get_notion_data

config = dotenv_values('.env')

def main():
    load_google_calender.first_sync_calendar(get_notion_data.get_first_data(), config.get('CALENDAR_ID'))

if __name__ == "__main__":
    main()
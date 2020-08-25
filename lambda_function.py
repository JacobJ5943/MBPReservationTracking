import requests
import json
import datetime
import boto3
import pytz

from bs4 import BeautifulSoup
def get_reservations_for_date(month,day,year):
    url = "https://app.rockgympro.com/b/widget/?a=equery"

    payload = {'show_date': str(year) + '-' + str(month) + '-' + str(day),
               'PreventChromeAutocomplete': '',
               'random': '5f43ffdd394e9',
               'iframeid': 'rgpiframe5f43ffdcbf982f',
               'mode': 'e',
               'fctrl_1': 'offering_guid',
               'offering_guid': 'b4776c4115654be383f2a4d69d91e9ab',
               'fctrl_2': 'course_guid',
               'course_guid': '',
               'fctrl_3': 'limited_to_course_guid_for_offering_guid_b4776c4115654be383f2a4d69d91e9ab',
               'limited_to_course_guid_for_offering_guid_b4776c4115654be383f2a4d69d91e9ab': '',
               'fctrl_4': 'show_date',
               'ftagname_0_pcount-pid-1-1137': 'pcount',
               'ftagval_0_pcount-pid-1-1137': '1',
               'ftagname_1_pcount-pid-1-1137': 'pid',
               'ftagval_1_pcount-pid-1-1137': '1137',
               'fctrl_5': 'pcount-pid-1-1137',
               'pcount-pid-1-1137': '1'}

    response = requests.request("POST", url, data=payload)
    body_json = json.loads(response.text)
    return body_json['event_list_html']

def get_reservations_from_html(html:str, hour,minute, ampm):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.table
    reservationList = table.children
    time_to_find = generate_timeslot_string(hour, minute, ampm)

    for child in reservationList:
        if child == '\n':
            continue

        # Find if the time is in this one
        contents = child.contents
        contents = filter(lambda x : x != '\n',
                   contents)
        timeFound = False
        for content in contents:
            if timeFound:
                content = str(content)
                if 'Availability' in content:
                    endIndex = content.find('spaces') -1
                    startindex = content.find('<br/>') + 5

                    if endIndex < 0 or startindex < 0:
                        return 0
                    reservations = content[startindex:endIndex]
                    return int(reservations)
            if time_to_find in str(content):
                timeFound = True
    return -404
def get_next_slot_reservation():
    tzinfo = pytz.timezone('US/Mountain')
    date = datetime.datetime.now(tzinfo)
    month = date.month
    year = date.year
    day = date.day
    minute = date.minute
    hour = date.hour - 5
    reservations_on_day = get_reservations_for_date(month, day, year)
    (hour, minute, ampm) = timeslot_from_hour_minute(hour, minute)
    return get_reservations_from_html(reservations_on_day, hour, minute, ampm)


def generate_timeslot_string(hour, minute, ampm):
    if minute == 0:
        time_to_find = (str(hour) + ' ' + ampm + ' to')
    else:
        time_to_find = (str(hour) + ':' + str(minute) + ' ' + ampm + ' to')

    return time_to_find

def timeslot_from_hour_minute(hour, minute):
    if minute < 30:
        minute = 30
    else:
        minute = 0
        hour = hour + 1
    ampm = 'AM'

    if hour >= 12:
        ampm = 'PM'
        hour = hour - 12

    return (hour, minute, ampm)

def send_results_to_s3(results):
    s3_client = boto3.client('s3')
    corgi = s3_client.get_object(Bucket='mbpreservations', Key='Reservations.csv')
    corgibody = corgi['Body'].read()
    corgibody = corgibody.decode('utf-8') + results + '\n'
    corgi2_response = s3_client.put_object(Bucket='mbpreservations', Key='Reservations.csv',Body=corgibody)
    pass

# This is what will occur for a lambda function
def lambda_handler(event, context):
    tzinfo = pytz.timezone('US/Mountain')
    timeNow = datetime.datetime.now(tzinfo)
    hour = timeNow.hour
    minute = timeNow.minute

    (timeslotHour, timeslotMinute, ampm) = timeslot_from_hour_minute(hour, minute)
    timeslot = generate_timeslot_string(timeslotHour, timeslotMinute, ampm)
    insert_line =  str(timeNow) + '|' + timeslot[:len(timeslot) -3] + '|' + str(get_next_slot_reservation())
    send_results_to_s3(insert_line)
    return {
        'statusCode': 200,
        'body': json.dumps('Complpete')
    }


if __name__ == '__main__':
    centralTimezone = pytz.timezone('US/Mountain')
    timeNow = datetime.datetime.now(centralTimezone)
    hour = timeNow.hour
    minute = timeNow.minute

    (timeslotHour, timeslotMinute, ampm) = timeslot_from_hour_minute(hour, minute)
    timeslot = generate_timeslot_string(timeslotHour, timeslotMinute, ampm)
    insert_line = str(timeNow) + '|' + timeslot[:len(timeslot) - 3] + '|' + str(get_next_slot_reservation())
    send_results_to_s3(insert_line)


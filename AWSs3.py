import requests
import boto3
from botocore.config import Config

if __name__ == '__main__':
    s3_client = boto3.client('s3')
    #corgi = s3_client.get_object('s3://mbpreservation-year-month-day-hour-minute/Corgi.jpg')
    corgi = s3_client.get_object(Bucket='mbpreservations', Key='Reservations.csv')
    #corgibody = corgi['Body'].read()
    #corgibody = corgibody.decode('utf-8') + '\n' + '2020-08-25 00:09:29.893218|0:30 AM|-404'
    corgibody = 'TIMESTAMP|TIMESLOT|SPACES_AVAILABLE\n'
    corgi2_response = s3_client.put_object(Bucket='mbpreservations', Key='Reservations.csv',Body=corgibody)
    form_params = dict()
    pass
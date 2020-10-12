import os, sys
sys.path.insert(1, '/mnt/efs/')
print("Mounted.")

import boto3
import json
import pickle
import pandas as pd
from pymongo import MongoClient
print("Imported.")

aws_id, aws_secret_key = pd.read_csv('DesiPilla_accessKeys.csv').values[0]
print("Keys loaded.")
bucket = os.environ["bucket"]
queue_name = os.environ["queueName"]
queue_url = os.environ["queueUrl"]

# s3 = boto3.client('s3')
# s3_resource = boto3.resource('s3')
s3 = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
s3_resource = boto3.resource('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
sqs = boto3.client('sqs')
print("s3 and sqs connected.")

mongo = MongoClient('mongodb://52.71.228.156:27017/')
print("Mongo connected.")

import stanza
# nlp = stanza.Pipeline('en', '/mnt/efs/')
nlp = s3.get_object(Bucket=bucket, Key='dataframes/test.csv')
print("NLP loaded.")


def handler(event, context):
    print("Enter handler.")
    
    resp = sqs.receive_message(QueueUrl = queue_url, AttributeNames=['All'])
    doc = json.loads(resp["Messages"][0]["Body"])
    msg_receipt = resp["Messages"][0]["ReceiptHandle"]



    return {"message":dbs,
            "ip": str(ip)
    }
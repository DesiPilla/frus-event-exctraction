import os, sys
sys.path.insert(1, '/mnt/efs/')
print("Mounted.")

import time
start_time = time.time()

import io
import re
import json
import boto3
import pickle
import stanza
import logging
import pandas as pd
from pymongo import MongoClient
print("Imported.")

# Load AWS Credentials
aws_id, aws_secret_key = pd.read_csv('DesiPilla_accessKeys.csv').values[0]
print("Keys loaded.")
bucket = os.environ["bucket"]
queue_name = os.environ["queueName"]
queue_url = os.environ["queueUrl"]

# Configure AWS clients
s3 = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
s3_resource = boto3.resource('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
sqs = boto3.client('sqs')
print("s3 and sqs connected.")

# Load Stanford CoreNLP pipeline
obj = s3.get_object(Bucket=bucket, Key='nlp')
data = obj['Body'].read()
nlp = pickle.loads(data)
print("NLP loaded.")

def prepare_doc(doc):
    doc["source"] = doc["website"]
    doc["context"] = doc['text']

    strip = [k for k in doc.keys() if "." in k ] + ["website", "text"]
    for k in strip:
        del doc[k]

    doc['stanford'] = 0
    # doc['_id'] = doc['id']
    return doc


def handler(event, context):
    print("Enter handler.")
    start_time = time.time()
    
    mongo = MongoClient('mongodb://52.71.228.156:27017/')
    db = mongo.FRUS
    collection = db.ParsedDocs
    print("Mongo connected.")

    count = 0
    while time.time() - start_time < 600:
        print("Parsing doc {:,}...".format(count), end="")
        resp = sqs.receive_message(QueueUrl=queue_url, AttributeNames=['All'])
        doc = json.loads(resp["Messages"][0]["Body"])
        msg_receipt = resp["Messages"][0]["ReceiptHandle"]

        text = doc["text"][:2000]
        print("({:,})...".format(len(text)), end="")
        try:
            parsed = nlp(text).to_dict()[0]
            doc["parsed"] = json.dumps(parsed)
        except:
            doc["parsed"] = "error"

        to_mongo = prepare_doc(doc)
        collection.insert_one(to_mongo)
        del_resp = sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg_receipt)
        print("Done")
        count += 1
        
            
    print("{:,} documents parsed and sent to Mongo.".format(count))
    return {"message":"{:,} documents parsed and sent to Mongo.".format(count)}
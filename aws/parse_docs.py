import os, sys
sys.path.insert(1, '/mnt/efs')

print("Printing files:")
print(os.listdir('/mnt/'))
print(os.listdir('/mnt/efs/'))
print("Done.")

import json
import boto3
import stanza

# Configure s3 client and resource
print("Configure s3...")
bucket = os.environ["bucket"]
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')

def handler(event, context):
    president = month = file_id = text = 'test'

    # Create stanza Pipeline
    nlp = stanza.Pipeline('en', '/mnt/efs/')
    
    # Feed text into CoreNLP
    parsed = nlp('Barack Obama was the President.').to_dict()
    
    # Upload results to s3
    key = f"parsed/president={president}/month={month}/{file_id}.json"
    
    results = {
            "president": president,
            "month": month,
            "file_id": file_id,
            "text": text,
            "results": json.dumps(parsed[0]),
            "key": key
           }

    resp = s3_resource.Object(bucket, key).put(Body=json.dumps(results))

    return {"message": "Success!",
            "s3_response": resp,
            "results": results,
    }
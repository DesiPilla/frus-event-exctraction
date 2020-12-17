import os, sys
sys.path.insert(1, '/mnt/efs/')
print("Mounted.")

import psutil
print(psutil.virtual_memory())

import io
import json
import time
import boto3
import logging
import pandas as pd
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

print(psutil.virtual_memory())

# from stanfordcorenlp import StanfordCoreNLP
# nlp = StanfordCoreNLP("/mnt/efs/stanford-corenlp-full-2018-10-05", timeout=600, lang="en", memory="8g", quiet=False, logging_level=logging.INFO)
# print(nlp.port)
# print(nlp.url)

print(psutil.virtual_memory())

# import stanza
# from stanza.server import CoreNLPClient
# classpath = '/mnt/efs/stanford-corenlp-full-2018-10-05'
# nlp = CoreNLPClient(be_quite=False, 
#                       classpath=classpath, 
#                       annotators=['tokenize'],# 'mwt', 'pos', 'lemma', 'depparse'], 
#                       memory='4G', 
#                       endpoint='http://localhost:9001')
# nlp.start()

# ann = nlp.annotate(text)

import stanza
# Load English neural pipeline
nlp = stanza.Pipeline('en', '/mnt/efs', processors="tokenize, pos, lemma, ner, depparse") 



print("CoreNLP loaded.")
# print("Initializing CoreNLP with 'I' parse...")
# start_time = time.time()
# text = "Barack Obama was the 45th President of the United States. The clothes in the dressing room are gorgeous. Can I have one?"
# prop={'annotators': 'tokenize,ssplit,pos,','pipelineLanguage':'en','outputFormat':'xml'}
# ann = nlp.annotate(text, properties=prop)
# ann = nlp(text)
# print(ann)

# print("Done. (initialized in {:.1} seconds".format(time.time() - start_time))


def parse_doc(doc):
    
    # Extract document information
    doc_id = doc.id
    text = doc.text
    title = doc.title
    url = doc.url
    date = doc.date
    president = doc.website

    # Only keep the first 3,000 words
    if doc.num_words > 3000:
        text = ' '.join(text.split(' ')[:3000])

    try:
        # Parse document text
        parsed = nlp(text)
        
        # Isolate sentence results and dependency strings
        parse_results = [sentence.to_dict() for sentence in parsed.sentences]
        dep_strs = [sentence.dependencies_string() for sentence in parsed.sentences]
    
    
        # Construct message
        message = {
            "id": doc_id,
            "text": text,
            "title": title,
            "url": url,
            "date": date,
            "website": president,
            
            "parse_results": json.dumps(parse_results),
            "dependency_strings": json.dumps(dep_strs),
        }
        
        return message
        
    # Handle any exceptions thrown during processing
    except:
        return 'error'


def handler(event, context):
    print("Enter handler.")

    # Initialize progress counters
    successes = 0
    errors = 0

    # resp = sqs.receive_message(QueueUrl = queue_url, AttributeNames=['All'])
    # doc = json.loads(resp["Messages"][0]["Body"])
    # msg_receipt = resp["Messages"][0]["ReceiptHandle"]


    # Get document
    key = "parsed/test.csv"
    data = s3_resource.Object(bucket, key).get()['Body'].read()
    df = pd.read_csv(io.BytesIO(data)).iloc[:, 1:]
    
    for i in range(10):
        # Load document
        doc = df.iloc[i]
        print("Parsing doc {} (id = {})".format(i, doc.url))
        
        # Parse document and get JSON output
        print("Parsing example document...")
        start_time = time.time()
        message = parse_doc(doc)
        print("Done. (parsed in {:.1f} seconds)".format(time.time() - start_time))
    
        if message != 'error': successes += 1
        else: errors += 1
    

    # # Save output
    # s3.put_object(
    #         Body=str(json.dumps(xml)),
    #         Bucket=bucket,
    #         Key="parsed/test_output.xml"
    # )

    return {
        "message": "{:,} documents were processed.\n{:,} were parsed successfuly and {:,} threw errors.".format(successes + errors, successes, errors)
    }
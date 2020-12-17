import os, sys
sys.path.insert(1, '/mnt/efs/')
print("Mounted.")

# import pandas as pd
# pd.read_excel("https://github.com/DesiPilla/college-emails/blob/master/CollegeEmails.xlsx?raw=true")
# print("Connected to internet.")

# Start function timer
import time

import io
import json
import boto3
import psutil
import logging
import pandas as pd
print("Imported.")

aws_id, aws_secret_key = pd.read_csv('DesiPilla_accessKeys.csv').values[0]
print("Keys loaded.")

bucket = os.environ["bucket"]
queue_name = os.environ["queueName"]
queue_url = os.environ["queueUrl"]

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
# s3 = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
# s3_resource = boto3.resource('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
sqs = boto3.client('sqs', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
print("s3 and sqs connected.")


# Load English neural pipeline
import stanza
nlp = stanza.Pipeline('en', '/mnt/efs', processors="tokenize, pos, lemma, ner, depparse") 
print("CoreNLP loaded.")



def parse_doc(doc):
    
    # Extract document information
    doc_id = doc["id"]
    text = doc["text"]
    title = doc["title"]
    url = doc["url"]
    decade = doc["decade"]
    date = doc["date"]
    president = doc["website"]

    # Only keep the first 1,600 words
    if doc["num_words"] > 1600:
        text = ' '.join(text.split(' ')[:1600])

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

        # Create S3 key
        key = "parsed/{}/{}/{}.json".format(president, decade, doc_id)
        
        return message, key
        
    # Handle any exceptions thrown during processing
    except:
        return 'error', None




def handler(event, context):
    start_time = time.time()
    print("Enter handler.")

    # Initialize progress counters
    successes = 0
    errors = 0

    # Keep parsing documents one at a time for 1 minutes
    counter = 0
    while time.time() - start_time < 600:
        counter += 1
        
        try:
            # Fetch document from SQS
            resp = sqs.receive_message(QueueUrl=queue_url, AttributeNames=['All'])
            doc = json.loads(resp["Messages"][0]["Body"])
            msg_receipt = resp["Messages"][0]["ReceiptHandle"]
            print("Parsing doc {} ({} words, id = {})".format(counter, doc["num_words"], doc["url"]))
        except:
            print("Empty message recevied.")
            continue
        
        # Parse document and get JSON output
        doc_start = time.time()
        message, key = parse_doc(doc)
        print("\tParsed in {:.1f} seconds.".format(time.time() - doc_start))
    
        # If no error was thrown
        if key:
            # Save output to s3
            s3_resp = s3.put_object(
                Body=json.dumps(message),
                Bucket=bucket,
                Key=key
                )

            # Check that results were saved to s3 successfully
            if s3_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print(s3_resp)
                errors += 1
                del message
                del resp
                del doc
                del msg_receipt
                continue

            # Delete document from SQS
            del_resp = sqs.delete_message(
                QueueUrl = queue_url,
                ReceiptHandle = msg_receipt
            )
            
            # Check that document was deleted from SQS successfully
            if del_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print(del_resp)
                errors += 1
                del message
                del resp
                del doc
                del msg_receipt
                continue
            
            successes += 1
        else: 
            print(key)
            print(message)
            errors += 1
            del message
            del resp
            del doc
            del msg_receipt
            continue
        
        print("{:.2f} MB available".format(psutil.virtual_memory().available * 1e-6))
        # Delete message from memory to cut costs
        del message
        del resp
        del doc
        del msg_receipt

    return {
        "message": "{:,} documents were processed.\n{:,} were parsed successfuly and {:,} threw errors.".format(successes + errors, successes, errors)
    }
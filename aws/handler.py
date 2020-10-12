import os, sys
sys.path.insert(1, '/mnt/efs')

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
    
os.environ["bucket"] = 'frus-corenlp'

# Configure s3 client and resource
logging.critical("Configure s3...")
bucket = os.environ["bucket"]
# s3 = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)
# s3_resource = boto3.resource('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret_key)

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
nlp = stanza.Pipeline('en', '.')


def df_to_s3(df, key):
    '''
    This function takes a pandas dataframe, converts it to a csv file, and then uploads it to an s3 bucket.

    Parameters:
    ---------------
    df: pandas dataframe, the dataframe to be saved
    s3: authorized boto s3 resource
    bucket: str, bucket to upload file to (topic-modeling-deployment)
    key: key of the file to be uploaded (.csv file)

    Returns:
    ---------------
    key: str, the key / name of the file in the s3 bucket
    '''
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)        
    try:
        s3_resource.Object(bucket, key).delete()
    except:
        pass
    s3_resource.Object(bucket, key).put(Body=csv_buffer.getvalue())
    return key


def parse_doc(doc):
    
    # Extract document information
    file_id = doc.id 
    text = doc.text
    title = doc.title
    url = doc.url
    date = doc.date
    president = doc.website
    batch = doc.batch
        
    try:
        # Only keep first 6 sentences of text
        num_sentences = 6
        text = ''.join(re.split(r'(?<=[.])(\s[A-Z])', text)[:num_sentences*2 - 1])[:1000]
    
        # Feed text into CoreNLP
        parsed = nlp(text).to_dict()
        
        return parsed[0]
    except:
        return 'error'

    return resp

def handler(event):
    print("Enter handler.")

    # Get key name
    key = event["key"]
    timeout = event["timeout"]
    batch_name = key.split('/')[-1][:-4]
    # logging.critical("Parsing {}".format(batch_name))
    print("Parsing {}".format(batch_name))
    
    # print("Loading NLP...")
    # global nlp
    # nlp = stanza.Pipeline('en', '/mnt/efs/')
    # obj = s3.get_object(Bucket=bucket, Key='nlp')
    # data = obj['Body'].read()
    # nlp = pickle.loads(data)


    # Get file containing documents
    data = s3_resource.Object("frus-corenlp", key).get()['Body'].read()
    df = pd.read_csv(io.BytesIO(data)).iloc[:, 1:]
    if 'parsed' not in df.columns:
        df['parsed'] = None
    
    # Check how many documents need to be parsed
    # logging.critical("{:,}/{:,} documents need to be parsed.".format(df.parsed.isnull().sum(), len(df)))
    print("{:}: {:,}/{:,} documents need to be parsed.".format(batch_name, df.parsed.isnull().sum(), len(df)))
    df.parsed = df.parsed.astype(str)
    try:
        start_index = df.parsed.to_list().index('nan')
    except:
        start_index = 0

    success = len(df[~df.parsed.isin(['error', 'nan'])])
    error_ids = []
    dnf_ids = []
    # logging.critical("Begin parsing loop.")
    print("{}: Begin parsing loop.".format(batch_name))
    size = df.shape[0]
    for i in range(start_index, size):
        # Check if Lambda time is close to timing out
        if time.time() - start_time > timeout - 45:
            # logging.critical("Out of time.")
            print("{}: Out of time.".format(batch_name))
            dnf_ids .extend(df.id.tolist()[i:])
            break
            
        # Get document
        doc = df.iloc[i]
        
        # Check document has not already been analyzed
        if doc.parsed  == "None":
            # logging.critical("File {}/{}: now running".format(i, size))
            print("{}: File {}/{}: now running".format(batch_name, i, size))
            # Pass doc to CoreNLP
            parsed = parse_doc(doc)
        
            # Check for errors
            if parsed == 'error':
                error_ids.append(int(doc.id))
                df.iloc[i, -1] = 'error'
            else:
                df.iloc[i, -1] = json.dumps(parsed)
                success += 1
            
            # if not (i - start_index + 1) % 10:
            #     # Save progress to s3
            #     df_to_s3(df, key)
            df_to_s3(df, key)
        else:
            # logging.critical("File {}/{} already done".format(i, size))
            # print("{}: File {}/{} already done".format(batch_name, i, size))
            pass

    # Save progress to s3
    # df_to_s3(df, key)

    if success == size:
        # logging.critical("All documents in batch have been analyzed.")
        print("{}: All documents in batch have been analyzed.".format(batch_name))
    
        # Save batch dataframe to s3
        df_key = 'parsed/{}.csv'.format(batch_name)
        df_to_s3(df, df_key)
            
    message = "{0:,} documents successfully parsed.".format(success)
    message += "\n{0:,} documents raised errors.".format(len(error_ids))
    # message += "\n{0:,} documents did not get parsed due to time.".format(len(dnf_ids))
    # logging.critical(message)
    print("{}:".format(batch_name), message)
    print("{}: Time: {:.2f}".format(batch_name, time.time() - start_time))

    return {"message": message}
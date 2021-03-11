import sys
import json
import sklearn
import pandas as pd
import pickle
import os
import numpy as np

def handler(event, context):
    with open('./tmp/pickle_model.pkl', 'rb') as file:
    	pickle_model = pickle.load(file)
    pred = pickle_model.predict(np.array([[5,3.2,1.6,0.4]]))
    results = json.dumps(pred.tolist())
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT',
            'Access-Control-Allow-Credentials': True
        },
        'body': results
    }
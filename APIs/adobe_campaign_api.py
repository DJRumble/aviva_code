# -*- coding: utf-8 -*-
import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import requests
import collections
import re
import time

# Recipe inputs
master_adobe_campaign_API_OUTPUT = dataiku.Dataset("daily_MASTER_ARC_output")
df = master_adobe_campaign_API_OUTPUT.get_dataframe()

##### DEFFINE API ##### 

#API URL
url = "https://....jsp" #UAT
#url = "https://....jsp" #PROD

#Headers
headers = {
    'content-type': "text/xml;charset=UTF-8",
    'soapaction': "...",
    'cache-control': "no-cache",
    'postman-token': "..."
    }

batchsize = 12000

dttm_list = []

##### BUILD PAYLOAD ##### 

payload_start = """<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:urn=\"urn:av:adaMessagingEventQueue\">\n
                 <soapenv:Header/>\n   
                 <soapenv:Body>\n      
                 <urn:PushMessageBatch>\n         
                 <urn:sessiontoken>adaStage</urn:sessiontoken>\n                
                 <urn:domMessageCollection>\n               
                 <messages>\n  """

#DEV
#<urn:sessiontoken>adaStage</urn:sessiontoken>\n
#PROD
#<urn:sessiontoken>adaProd</urn:sessiontoken>\n

payload_end = """
                 </messages>\n         
                 </urn:domMessageCollection>\n      
                 </urn:PushMessageBatch>\n  
                 </soapenv:Body>\n
                 </soapenv:Envelope>\n"""

readout = {}

for i in xrange(0, len(df), batchsize):
    
    #Timing step
    start_time_batch = time.time()
    
    batch = df[i:i+batchsize]
    print '{}/{} - {}%'.format(i,len(df),round((float(i)/float(len(df)))*100,0))
    
    payload_rows =  """ """
    
    batch.columns=batch.columns.str.lower()
    
    for j in range(len(batch)):
        
        try:
            part_payload = """

                         <avivaMessage 
                         campaignName=\"{}\" 
                         masterId=\"{}\" 
                         productRecommendation=\"{}\" 
                         contentLevel1=\"{}\" 
                         contentLevel2=\"{}\" 
                         contentLevel3=\"{}\"/>\n """.format(
                batch.campaignid.iloc[j],
                batch.masterid.iloc[j],
                batch.productrecomendation.iloc[j],
                batch.emailcontentlevel1.iloc[j],
                batch.emailcontentlevel2.iloc[j],
                batch.emailcontentlevel3.iloc[j],
                )          

            payload_rows = payload_rows + part_payload
        except:
            print 'end of file'
            pass
        
    payload = payload_start+payload_rows+payload_end
    
    ##### SEND API SCRIPT ##### 
    response = requests.request("POST", url, data=payload, headers=headers)
  
    ##### REPORTING ##### 
    m = re.search('Success', response.text)
    
    if str(m) == 'None':
        readout['batch_{}'.format(i)] = response.text
    else:
        readout['batch_{}'.format(i)] = m.group(0)
      
    dttm_list.append(time.strftime('%x %X'))
    
    ##### TESTING ##### 
    #if i == 4:
    #    break    
    
    #Timing step
    end_time_batch = time.time()
    overall_time_delta = end_time_batch - start_time_batch
    print 'Batch run time = {}s'.format(round(overall_time_delta,3))

readout = collections.OrderedDict(sorted(readout.items()))

df_readout = pd.DataFrame(readout.items(),columns=['batch','readout'])
df_readout['dttm'] = pd.Series(dttm_list, index=df_readout.index)

# Recipe outputs
deployment_validation = dataiku.Dataset("daily_validation")
deployment_validation.write_with_schema(df_readout)

# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 20:39:27 2020

@author: yyhan
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

HOS = pd.read_csv('hospitalization.csv')
HOS.describe
HOS.to_excel('HOS1.xlsx')

#HOS_unrepeat = HOS.drop_duplicates(subset=['PAT_ID'], keep='first')
#HOS_unrepeat.describe

# Transform date format
HOS["HOSP_ADMSN_TIME"] = pd.to_datetime(HOS['HOSP_ADMSN_TIME'], format = '%d%b%Y:%H:%M:%S')
HOS['HOSP_ADMSN_TIME'] = pd.to_datetime(HOS['HOSP_ADMSN_TIME'])
HOS['HOSP_ADMSN_TIME'] = HOS['HOSP_ADMSN_TIME'].dt.date
HOS['HOSP_ADMSN_TIME']
HOS["DEATH_DATE"] = pd.to_datetime(HOS["DEATH_DATE"], format = '%d%b%Y:%H:%M:%S')
HOS['DEATH_DATE'] = pd.to_datetime(HOS['DEATH_DATE'])
HOS['DEATH_DATE'] = HOS['DEATH_DATE'].dt.date
HOS['DEATH_DATE']
HOS["END_DATE"] = pd.to_datetime(HOS["END_DATE"], format = '%Y-%m-%d')
HOS['END_DATE'] = pd.to_datetime(HOS['END_DATE'])
HOS['END_DATE'] = HOS['END_DATE'].dt.date
HOS['END_DATE']

# For the death date and end date, select the smaller one as the end date
for i in range(0,4863,1):
    if HOS.END_DATE[i] > HOS.DEATH_DATE[i]:
        HOS.END_DATE[i] = HOS.DEATH_DATE[i]

#HOS['DD'] = HOS.DEATH_DATE - HOS.END_DATE # days that death date after end date


# set severity to 5 leverls
for i in range(0,4863,1):
    if 0 <= HOS.severity[i] <= 0.19:
        HOS.severity[i] = 1
    elif 0.2 <= HOS.severity[i] <= 0.39:
        HOS.severity[i] = 2
    elif 0.4 <= HOS.severity[i] <= 0.59:
        HOS.severity[i] = 3
    elif 0.6 <= HOS.severity[i] <= 0.79:
        HOS.severity[i] = 4
    elif 0.8 <= HOS.severity[i] <= 0.99:
        HOS.severity[i] = 5
Severity_dis = HOS.groupby(by = ['severity']).size() 
Severity_dis

# ICU bed resource
ICU = pd.read_csv('ICU.csv')
ICU['DATE'] = pd.to_datetime(ICU["DATE"], format = '%d-%b-%y')
ICU = ICU.drop_duplicates(subset=['PAT_ID','PAT_ENC_CSN_ID','DATE'],keep='first')
ICU_Stat = ICU.groupby(by = ['DATE']).size() 
ICU_Stat.max() # got the biggest number of occupied ICU
ICU_Stat.min()

# Service time 
ICU1=ICU.drop_duplicates(subset=['PAT_ENC_CSN_ID'],keep='first')
ICU2=ICU.drop_duplicates(subset=['PAT_ENC_CSN_ID'],keep='last')
ICU2
ICU_SE = pd.merge(ICU1,ICU2, on = ['PAT_ENC_CSN_ID','PAT_ID'], how = 'left',suffixes=('_start', '_end'))
ICU_SE.columns = ['PAT_ID', 'PAT_ENC_CSN_ID', 'ICU_start', 'ICU_end']
ICU_SE

HOS = pd.merge(HOS,ICU_SE,on = ['PAT_ENC_CSN_ID','PAT_ID'], how = 'left')
HOS['ICU_start'] = HOS.ICU_start.dt.date
HOS['ICU_end'] = HOS.ICU_end.dt.date

HOS['Total_day'] = HOS.END_DATE - HOS.HOSP_ADMSN_TIME + timedelta(days = 1)
HOS['ICU_day'] = HOS.ICU_end - HOS.ICU_start + timedelta(days = 1)
HOS['Regular_day'] = HOS.Total_day - HOS.ICU_day
for i in range(0,4863,1):
    if HOS.Regular_day.isna()[i] == True:
        HOS.Regular_day[i] = HOS.Total_day[i]


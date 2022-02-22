# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 17:04:48 2020

@author: yyhan
"""
import pandas as pd
import numpy as np
import SimFunctions
import SimRNG
import SimClasses
import matplotlib.pyplot as plt
from scipy import stats

#p1
stayed_in_Reg1=2474
stayed_in_Reg2=1316
stayed_in_Reg3=539
stayed_in_Reg4=242
stayed_in_Reg5=169
stayed_in_Reg1alive=2224
stayed_in_Reg2alive=1047
stayed_in_Reg3alive=301
stayed_in_Reg4alive=53
stayed_in_Reg5alive=7
p11=stayed_in_Reg1alive/stayed_in_Reg1
p12=stayed_in_Reg2alive/stayed_in_Reg2
p13=stayed_in_Reg3alive/stayed_in_Reg3
p11
p12
p13

#p2
stayed_in_ICU1=420
stayed_in_ICU2=248
stayed_in_ICU3=154
stayed_in_ICU4=120
stayed_in_ICU5=95
stayed_in_ICU1alive=330
stayed_in_ICU2alive=128
stayed_in_ICU3alive=32
stayed_in_ICU4alive=6
stayed_in_ICU5alive=3
p24=stayed_in_ICU4alive/stayed_in_ICU4
p25=stayed_in_ICU5alive/stayed_in_ICU5
p24
p25
#p3
nstay_inICU_stayedinReg1=2072
nstay_inICU_stayedinReg2=1082
nstay_inICU_stayedinReg3=403
nstay_inICU_stayedinReg4=143
nstay_inICU_stayedinReg5=91
nstay_inICU_stayedinReg1alive=1893
nstay_inICU_stayedinReg2alive=915
nstay_inICU_stayedinReg3alive=267
nstay_inICU_stayedinReg4alive=43
nstay_inICU_stayedinReg5alive=4
p34=nstay_inICU_stayedinReg4alive/nstay_inICU_stayedinReg4
p35=nstay_inICU_stayedinReg5alive/nstay_inICU_stayedinReg5
p34
p35
#T1
T11=14693/1893
T12=8307/915
T13=2334/267
T11
T12
T13
#T2
T21=3868/369
T22=1945/215
T23=777/128
T21
T22
T23
#T3
T34=616/100
T35=544/87
T34
T35
#T4
T44=154/6
T45=65/3
T44
T45
#T5
T54=1365/114
T55=1123/92
T54
T55
#T6
T64=332/43
T65=59/4
T64
T65



p_value = []
for reps in range(0,1000):
    arr = pd.read_csv('arr.csv') # arrival rate in one day
    maxrate=np.max(arr['number'])
    interval=5
    a=np.zeros(shape=(int(len(arr)/interval+1),interval))
    for i in range(len(arr)):
        for k in range(int(len(arr)/interval)+2):
           if int(i/interval)==k-1:
              a[k-1,i%interval] =arr['number'][i]
    b=[]
    for i in range(int(len(arr)/interval)+1):
        b.append(np.mean(a[i]))
    maxrate=np.max(b)
    q=np.zeros(shape=(1,int((len(arr)/interval))+1))
    e=[]
    for i in range(0,len(b)):
        q=np.random.poisson(b[i],interval)
        e.append(q)
    o=[]
    for i in range(0,len(e)):
        o=o+list(e[i])
    s=range(0,len(o))
    realdata = arr.number
    
    result = stats.ks_2samp(realdata, o)
    p_value.append(result[1])

p_value
print('CI of p-value:', [np.mean(p_value) - 1.96 * np.std(p_value)/np.sqrt(1000), np.mean(p_value) + 1.96 * np.std(p_value)/np.sqrt(1000)])






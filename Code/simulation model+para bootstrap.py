#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 21:17:05 2020

@author: zhangruotong
"""


# Call Center HW Project 
# Current SMP Call Center
# Import needed modules

import pandas as pd
import numpy as np
import SimFunctions
import SimRNG
import SimClasses
import matplotlib.pyplot as plt

# posibility of each severity level
SeverityPro = [0.5165,0.7916,0.9068,0.9617,1] #cumulative probability

# posibility for discion making
P1=[0,0.90,0.80,0.56]
P2=[0,0,0,0,0.05,0.03]
P3=[0,0,0,0,0.30,0.04]

# service time
T1 = [0,7.76,9.08,8.74]
T2 = [0,10.48,9.05,6.07]
T3 = [0,0,0,0,6.16,6.25]
T4 = [0,0,0,0,25.67,21.67]
T5 = [0,0,0,0,11.97,12.21]
T6 = [0,0,0,0,7.72,14.75]

# Initialize RNG and Event Calendar
ZRNG = SimRNG.InitializeRNSeed()
Calendar = SimClasses.EventCalendar()

TheCTStats = []
TheDTStats = []
TheQueues = []
TheResources = []

RegQueue = SimClasses.FIFOQueue() 
ICUQueue = SimClasses.FIFOQueue()
Regbed = SimClasses.Resource()
ICUbed = SimClasses.Resource()
QueueTimeReg = SimClasses.DTStat()
QueueTimeICU = SimClasses.DTStat()
TotalTime = SimClasses.DTStat()

Regbed.SetUnits(300)
ICUbed.SetUnits(50)

# These lists collect the across-rep data
QTR = [] # time in regular queue
QTI = [] # time in ICU queue
QNR = [] # number in regular queue
QNI = [] # number in ICU queue
RNR = [] # number of busy regular resource
RNI = [] # number of busy ICU resource
TT = [] # time in whole system
DeathRate = []

TheDTStats.append(QueueTimeReg)
TheDTStats.append(QueueTimeICU)
TheDTStats.append(TotalTime)
TheQueues.append(RegQueue)
TheQueues.append(ICUQueue)
TheResources.append(Regbed)
TheResources.append(ICUbed)

RunLength = 100
Warmup = 0

# input arrivel model
arr = pd.read_csv('arr.csv') # arrival rate in one day

plt.plot(range(len(arr)),arr['number'])
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
plt.plot(s,o)

#input model para-bootstrap
nb=len(a[0])
repb=100
alpha=0.05
B=1000
lam=[]
I_CI=pd.DataFrame(columns={'lambda','covery','average mean',
                 'average std','CI MEAN U','CI MEAN L','CI STD U','CI STD L'})
lam
for i in range(0,len(b)):
   i =0
   print('************',i)
   lam.append(b[i])
   CI_b=np.zeros(shape=(repb,7))
   for j in range(repb):
        samplebmean=np.zeros(B)
        samplebstd=np.zeros(B)
        for k in range(B):
            x_b=np.random.poisson(lam[i],nb)
            samplebmean[k]=np.mean(x_b)
            samplebstd[k]=np.std(x_b)
            #print(x_b)
        bmean1=np.quantile(samplebmean,alpha/2)
        bmean2=np.quantile(samplebmean,1-alpha/2)
        bstd1=np.quantile(samplebstd,alpha/2)
        bstd2=np.quantile(samplebstd,1-alpha/2)
        CI_b[j,0]=(bmean1<=lam[i]<=bmean2)
        CI_b[j,1]=bmean2-bmean1
        CI_b[j,2]=bstd2-bstd1
        CI_b[j,3]=bmean1
        CI_b[j,4]=bmean2
        CI_b[j,5]=bstd1
        CI_b[j,6]=bstd2
   res_b=np.mean(CI_b,axis=0)
   print('lambda=',b[i],'covery=',res_b[0],'average mean=',
         res_b[1],'average std=',res_b[2],'CI MEAN','[',res_b[3],res_b[4],']',
         'CI STD','[',res_b[5],res_b[6],']')
   I_CI=I_CI.append(pd.DataFrame({'lambda':[b[i]],'covery':res_b[0],'average mean':res_b[1],
                 'average std':res_b[2],'CI MEAN U':res_b[3],'CI MEAN L':res_b[4],'CI STD U':res_b[5],'CI STD L':res_b[6]}))
I_CI
I_CI.to_excel('I_CI.xlsx')

def ArrivalRate(a):
    k=int(a/interval)
    return b[k]
        
def IAT(stream): # nonstationary poisson 
    PossibleArrival = SimClasses.Clock+SimRNG.Expon(1/maxrate,stream)
    while PossibleArrival< RunLength and SimRNG.Uniform(0,1,stream) >= ArrivalRate(PossibleArrival)/maxrate:
          PossibleArrival += SimRNG.Expon(1/maxrate,stream)
    interarrival = PossibleArrival - SimClasses.Clock
    return interarrival

def Arrival():
    Interarrival = IAT(1)
    if SimClasses.Clock + Interarrival < RunLength:
        SimFunctions.SchedulePlus(Calendar, "Arrival", Interarrival, None)
    # new admitted patient
    NewPatient = SimClasses.Entity(0,"None","Unknown")
    
    SP = SimRNG.Uniform(0, 1, 1)
    if SP <= SeverityPro[0]:
        NewPatient.Severity = 1
    elif SeverityPro[0] < SP <= SeverityPro[1]:
        NewPatient.Severity = 2
    elif SeverityPro[1] < SP <= SeverityPro[2]:
        NewPatient.Severity = 3
    elif SeverityPro[2] < SP <= SeverityPro[3]:
        NewPatient.Severity = 4
    elif SeverityPro[3] < SP <= SeverityPro[4]:
        NewPatient.Severity = 5
        
    Severity = NewPatient.Severity # the new patient's orginal severity level
    
    if Severity <= 3: # go to regular 
        if SimRNG.Uniform(0,1,2) < P1[Severity]: # Patient would get better
            NewPatient.Status = "Alive"
            if Regbed.Busy == Regbed.NumberOfUnits: # the patient needs to wait in regular queue
                NewPatient.NowTreatment = "None" 
                RegQueue.Add(NewPatient)
            else: 
                Regbed.Seize(1)
                NewPatient.NowTreatment = "Regular"
                SimFunctions.SchedulePlus(Calendar, "EOR", T1[Severity], NewPatient)
                QueueTimeReg.Record(0.0) # sum doesn't change, # of observations would change
        else: # the new patient would get worse until severity level reaches to 4
            NewPatient.Status = "Unknown"
            if Regbed.Busy == Regbed.NumberOfUnits:
                NewPatient.NowTreatment = "None" 
                RegQueue.Add(NewPatient)
            else:
                Regbed.Seize(1)
                NewPatient.Status = "Regular"
                SimFunctions.SchedulePlus(Calendar, "EOR", T2[Severity], NewPatient)
                QueueTimeReg.Record(0.0) 
   
    else: # go to ICU
        if ICUbed.Busy < ICUbed.NumberOfUnits:# The new high-severity patient can enter ICU
           # ICUbed.Seize(1)
           ICU(NewPatient, Severity)
           QueueTimeICU.Record(0.0)
        else: # The new high-severity patient cannot get a ICU immediately
            if SimRNG.Uniform(0,1,4) < P3[Severity]: # though the patient can't get ICU, but will survive in regular
                NewPatient.Status = "Alive"
                if Regbed.Busy == Regbed.NumberOfUnits: 
                    NewPatient.NowTreatment = "None" 
                    RegQueue.TopAdd(NewPatient) # put the patient at the top of the queue
                else: 
                    Regbed.Seize(1)
                    NewPatient.NowTreatmen = "Regular"
                    SimFunctions.SchedulePlus(Calendar, "EOR", T6[Severity], NewPatient)
                    QueueTimeReg.Record(0.0)
            else: # if the patient can get a ICU determines that whether the patient would die under regular treatmen
                NewPatient.Status = "Unknown"
                NewPatient.NowTreatment = "None"
                #print(NewPatient.Status)
                ICUQueue.Add(NewPatient) # Take NT = "None" with the patient to wait in regular queue
                if Regbed.Busy == Regbed.NumberOfUnits: 
                    RegQueue.TopAdd(NewPatient)
                else:
                    Regbed.Seize(1)
                    NewPatient.NowTreatment = "Regular"
                    SimFunctions.SchedulePlus(Calendar, "EOR", T3[Severity], NewPatient)
                    QueueTimeReg.Record(0.0)


def ICU(Patient, Severity): # After enter ICU
    ICUbed.Seize(1) 
    Patient.NowTreatment = "ICU"
    if SimRNG.Uniform(0,1,3) < P2[Severity]: # The patient would get better in ICU            
        Patient.Status = "Alive"
        SimFunctions.SchedulePlus(Calendar, "EOI", T4[Severity], Patient)
       # QueueTimeICU.Record(SimClasses.Clock - Patient.CreateTime) 
    else: # The new patient would die in ICU
        Patient.Status = "Deceased"
        SimFunctions.SchedulePlus(Calendar, "EOI", T5[Severity], Patient)
     #   QueueTimeICU.Record(SimClasses.Clock - Patient.CreateTime)
    
def EOR(DepartingPatient):
    if DepartingPatient.Severity <= 3 and DepartingPatient.Status == "Unknown" and DepartingPatient.index == 0:
        DepartingPatient.index = 1 # the patient has reached 4
        DepartingPatient.HosTime = SimClasses.Clock
        if ICUbed.Busy < ICUbed.NumberOfUnits:
            ICU(DepartingPatient, 4)
            QueueTimeICU.Record(0.0)
        else:
            #print(DepartingPatient.Status)
            ICUQueue.Add(DepartingPatient)
            SimFunctions.SchedulePlus(Calendar, "EOR", T3[4], DepartingPatient)
    
    elif RegQueue.NumQueue() > 0:
        while RegQueue.Judge().NowTreatment == "ICU":
                NextPatient = RegQueue.Remove() 
        NextPatient = RegQueue.Remove() 
        
        if NextPatient.Severity <= 3: 
            if NextPatient.Status == "Alive": 
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) # record waiting time in regular queue
                SimFunctions.SchedulePlus(Calendar, "EOR", T1[NextPatient.Severity], NextPatient)
            else: 
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) 
                SimFunctions.SchedulePlus(Calendar, "EOR", T2[NextPatient.Severity], NextPatient)
        else:
            if NextPatient.Status == "Alive": # the high-severity patient would survive in regular bed
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) 
                SimFunctions.SchedulePlus(Calendar, "EOR", T6[NextPatient.Severity], NextPatient)                
            else: # "Unknown" status
                if NextPatient.NowTreatment == "None":
                    NextPatient.NowTreatment = "Regular"
                    QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) 
                    SimFunctions.SchedulePlus(Calendar, "EOR", T3[NextPatient.Severity], NextPatient)   

    else:
        Regbed.Free(1)
 
# Record the real departing patient info
    if DepartingPatient.Severity <= 3 and DepartingPatient.Status == "Unknown" and DepartingPatient.NowTreatment == "Regular" and DepartingPatient.index == 1:
        # the patient with level <= 3 gets worse but only stay in regular bed until death
        DepartingPatient.Status = "Deceased"
        A_D[1] += 1
        TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
    elif DepartingPatient.Severity <= 3 and DepartingPatient.Status == "Alive":
        A_D[0] += 1
        TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
    elif DepartingPatient.Severity > 3 and DepartingPatient.Status == "Alive":
        A_D[0] += 1
        TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
    elif DepartingPatient.Severity > 3 and DepartingPatient.Status == "Unknown" and DepartingPatient.NowTreatment == "Regular":
        # high-severity patients that would get worse in regular bed couldn't enter ICU before death
        DepartingPatient.Status = "Deceased"
        A_D[1] += 1
        TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
            
            
            
def EOI(DepartingPatient):
    if ICUQueue.NumQueue() > 0:
        #print(ICUQueue.Judge().Severity)
         
        while ICUQueue.Judge().Status == "Deceased": # patient could be transferred to ICU as long as not deceased
           NextPatient = ICUQueue.Remove()
           if ICUQueue.NumQueue() == 0:
               break
        
        if ICUQueue.NumQueue() == 0:
            NextPatient.Severity = 0
            NextPatient.Status ="Deceased"
            NextPatient.NowTreatment = "None"
        else:
            NextPatient = ICUQueue.Remove()
        
        if NextPatient.Severity <= 3 and NextPatient.Status == "Unknown" and NextPatient.NowTreatment == "Regular":
           QueueTimeICU.Record(SimClasses.Clock - NextPatient.HosTime)
           ICU(NextPatient, 5) # could depends on the waiting time 
        elif NextPatient.Severity > 3 and NextPatient.NowTreatment == "None": # hasn't enter regular ward
            QueueTimeICU.Record(SimClasses.Clock - NextPatient.CreateTime)
            ICU(NextPatient, NextPatient.Severity) 
        elif NextPatient.Severity > 3 and NextPatient.Status == "Unknown" and NextPatient.NowTreatment == "Regular":
            QueueTimeICU.Record(SimClasses.Clock - NextPatient.CreateTime)
            ICU(NextPatient, 5) # depends on time staying in regular
    else:
      ICUbed.Free(1)
      if DepartingPatient.Status == "Alive":
          if Regbed.Busy < Regbed.NumberOfUnits:
              Regbed.Seize(1)
              DepartingPatient.NowTreatment = "Regular"
              SimFunctions.SchedulePlus(Calendar, "EOR", T1[3], DepartingPatient)
              QueueTimeReg.Record(0.0)
          else:
              TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
              A_D[0] += 1
      elif DepartingPatient.Status == "Deceased":
         A_D[1] += 1
         TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)

          

# main program starts here
for Reps in range(0, 100, 1):
    print('************',Reps)
    A_D = [0,0] # Alive, Death

    SimFunctions.SimFunctionsInit(Calendar, TheQueues, TheCTStats, TheDTStats, TheResources)
    SimFunctions.SchedulePlus(Calendar, "Arrival", IAT(1), None)
    #SimFunctions.SchedulePlus(Calendar, "EndSimulation", RunLength, None)
    #SimFunctions.Schedule(Calendar, "ClearIt", Warmup)
    
    while Calendar.N() != 0:
        NextEvent = Calendar.Remove()
        SimClasses.Clock = NextEvent.EventTime
        if NextEvent.EventType == "Arrival":
            Arrival()
        elif NextEvent.EventType == "EOR":
            EOR(NextEvent.WhichObject)    
        elif NextEvent.EventType == "EOI":
            EOI(NextEvent.WhichObject)  
            
            
    
    
# Collect across-rep data # variance, min, max, CI
    QTR.append(QueueTimeReg.Mean())
    QTI.append(QueueTimeICU.Mean())
    TT.append(TotalTime.Mean())
    QNR.append(RegQueue.Mean())
    QNI.append(ICUQueue.Mean())
    RNR.append(Regbed.Mean()) 
    RNI.append(ICUbed.Mean())
    DeathRate.append(A_D[1] / (A_D[1] + A_D[1]))
    
thedata = {'RegularWaitingTime': QTR, 'ICUWaitingTime': QTI, 'TotalTime': TT, 'RegularQueueNum': QNR, 'ICUQueueNum': QNI, 'RegularBusyNum': RNR, 'ICUBusyNum': RNI, 'DeathRate': DeathRate}
mydata = pd.DataFrame(data=thedata)


print("Means of Our Statistics")
print(mydata.mean())
print("+/- 95% CI")
print(1.96*mydata.std()/np.sqrt(mydata.count()))
print("Relative error")
print(1.96*mydata.std()/np.sqrt(mydata.count())/mydata.mean())
print("Number of reps =", mydata['RegularWaitingTime'].count())

mydata
y=range(len(QTR))
QTRfig=plt.plot(y,QTR)
QTRfig=plt.hist(QTR,len(QTR))

plt.scatter([39.407360-0.237779],[39.407360+0.237779],c='r')

QTRfig.text(0,1.96*mydata.std()/np.sqrt(mydata.count()),'low bound')



    
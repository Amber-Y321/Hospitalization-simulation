#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 18:36:34 2020

@author: zhangruotong
"""


import pandas as pd
import numpy as np
import SimFunctions
import SimRNG
import SimClasses

# posibility of each severity level
SeverityPro = [0.5165,0.7916,0.9068,0.9617,1] #cumulative pro

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

Regbed.SetUnits(650)
ICUbed.SetUnits(70)

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



def ArrivalRatesample(a):
    k=int(a/interval)
    return sampleb[k]
        


def IATsample(stream): # nonstationary poisson 
    PossibleArrival = SimClasses.Clock+SimRNG.Expon(1/samplemaxrate,stream)
    while PossibleArrival< RunLength and SimRNG.Uniform(0,1,stream) >= ArrivalRatesample(PossibleArrival)/samplemaxrate:
          PossibleArrival += SimRNG.Expon(1/samplemaxrate,stream)
    interarrival = PossibleArrival - SimClasses.Clock
    return interarrival


def Arrivalsample():
    Interarrival = IATsample(1)
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
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T1[Severity],6), NewPatient)
                QueueTimeReg.Record(0.0) # sum doesn't change, # of observations would change
        else: # the new patient would get worse until severity level reaches to 4
            NewPatient.Status = "Unknown"
            if Regbed.Busy == Regbed.NumberOfUnits:
                NewPatient.NowTreatment = "None" 
                RegQueue.Add(NewPatient)
            else:
                Regbed.Seize(1)
                NewPatient.Status = "Regular"
                SimFunctions.SchedulePlus(Calendar, "EOR",  SimRNG.Expon(T2[Severity],7), NewPatient)
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
                    SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T6[Severity], 11), NewPatient)
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
                    SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T3[Severity],8), NewPatient)
                    QueueTimeReg.Record(0.0)

def ICU(Patient, Severity): # After enter ICU
    ICUbed.Seize(1) 
    Patient.NowTreatment = "ICU"
    if SimRNG.Uniform(0,1,3) < P2[Severity]: # The patient would get better in ICU            
        Patient.Status = "Alive"
        SimFunctions.SchedulePlus(Calendar, "EOI",  SimRNG.Expon(T4[Severity],9), Patient)
       # QueueTimeICU.Record(SimClasses.Clock - Patient.CreateTime) 
    else: # The new patient would die in ICU
        Patient.Status = "Deceased"
        SimFunctions.SchedulePlus(Calendar, "EOI", SimRNG.Expon(T5[Severity],10), Patient)
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
            SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T3[4],9), DepartingPatient)
    
    elif RegQueue.NumQueue() > 0:
        while RegQueue.Judge().NowTreatment == "ICU":
                NextPatient = RegQueue.Remove() 
                if ICUQueue.NumQueue() == 0:
                    break
                
        if RegQueue.NumQueue() == 0:
            NextPatient.Severity = 5
            NextPatient.Status ="Deceased"
            NextPatient.NowTreatment = "ICU"
        else:
            NextPatient = RegQueue.Remove() 
        
        if NextPatient.Severity <= 3: 
            if NextPatient.Status == "Alive": 
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) # record waiting time in regular queue
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T1[NextPatient.Severity],6), NextPatient)
            else: 
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) 
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T2[NextPatient.Severity],7), NextPatient)
        else:
            if NextPatient.Status == "Alive": # the high-severity patient would survive in regular bed
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) 
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T6[NextPatient.Severity],11), NextPatient)            
            
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
              SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T1[3],8), DepartingPatient)
              QueueTimeReg.Record(0.0)
          else:
              TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
              A_D[0] += 1
      elif DepartingPatient.Status == "Deceased":
         A_D[1] += 1
         TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)

          


#sample main program:
samplerep=100
i_sampleQTR=[]
i_sampleQTI=[]
i_sampleTT=[]
i_sampleQNR=[]
i_sampleQNI=[]
i_sampleRNR=[]
i_sampleRNI=[]
i_sampleDeathRate=[]
    
varQTR=[]
varQTR=[]
varQTI=[]
varTT=[]
varQNR=[]
varQNI=[]
varRNR=[]
varRNI=[]
varDeathRate=[]
B=800
nb=len(a[0])

for k in range(B):# k-th bootstrap
    A_D = [0,0]
    x_total=[]
    for l in range(0,len(b)):
        x_total=x_total+list(np.random.poisson(b[l],nb))
    samplea=np.zeros(shape=(int(len(x_total)/interval+1),interval))
    for m in range(len(x_total)):
        for n in range(int(len(x_total)/interval)+2):
            if int(m/interval)== n-1:
                samplea[n-1,m%interval] =x_total[m]
    sampleb=[]
    for i in range(int(len(x_total)/interval)+1):
        sampleb.append(np.mean(samplea[i]))
        samplemaxrate=np.max(sampleb)
        
    ij_sampleQTR=[]
    ij_sampleQTI=[]
    ij_sampleTT=[]
    ij_sampleQNR=[]
    ij_sampleQNI=[]
    ij_sampleRNR=[]
    ij_sampleRNI=[]
    ij_sampleDeathRate=[]
            
    for Reps in range(0, samplerep, 1): # each bootstrap needsn n reps
    
                # Alive, Death
                
             SimFunctions.SimFunctionsInit(Calendar, TheQueues, TheCTStats, TheDTStats, TheResources)
             SimFunctions.SchedulePlus(Calendar, "Arrival", IATsample(1), None)
    #SimFunctions.SchedulePlus(Calendar, "EndSimulation", RunLength, None)
    #SimFunctions.Schedule(Calendar, "ClearIt", Warmup)
    
             while Calendar.N() != 0:
                    NextEvent = Calendar.Remove()
                    SimClasses.Clock = NextEvent.EventTime
                    if NextEvent.EventType == "Arrival":
                        Arrivalsample()
                    elif NextEvent.EventType == "EOR":
                        EOR(NextEvent.WhichObject)    
                    elif NextEvent.EventType == "EOI":
                        EOI(NextEvent.WhichObject)
                
             ij_sampleQTR.append(QueueTimeReg.Mean())
             ij_sampleQTI.append(QueueTimeICU.Mean())
             ij_sampleTT.append(TotalTime.Mean())
             ij_sampleQNR.append(RegQueue.Mean())
             ij_sampleQNI.append(ICUQueue.Mean())
             ij_sampleRNR.append(Regbed.Mean()) 
             ij_sampleRNI.append(ICUbed.Mean())
             dr = A_D[1] / (A_D[0] + A_D[1])
             ij_sampleDeathRate.append(dr)
             print('~~~~',Reps,k)
    i_sampleQTR.append(np.mean(ij_sampleQTR))
    i_sampleQTI.append(np.mean(ij_sampleQTI))
    i_sampleTT.append(np.mean(ij_sampleTT))
    i_sampleQNR.append(np.mean(ij_sampleQNR))
    i_sampleQNI.append(np.mean(ij_sampleQNI))
    i_sampleRNR.append(np.mean(ij_sampleRNR))
    i_sampleRNI.append(np.mean(ij_sampleRNI))
    i_sampleDeathRate.append(np.mean(ij_sampleDeathRate))
    varQTR.append(np.var(ij_sampleQTR) * (samplerep ))
    varQTI.append(np.var(ij_sampleQTI)* (samplerep ))
    varTT.append(np.var(ij_sampleTT)* (samplerep ))
    varQNR.append(np.var(ij_sampleQNR)* (samplerep))
    varQNI.append(np.var(ij_sampleQNI)* (samplerep ))
    varRNR.append(np.var(ij_sampleRNR)* (samplerep))
    varRNI.append(np.var(ij_sampleRNI)* (samplerep))
    varDeathRate.append(np.var(ij_sampleDeathRate)* (samplerep ))
    print('*************************',k)
varT_QTR=(samplerep/(B-1))*(np.var(i_sampleQTR) * B)
varS_QTR=(1/(B*(samplerep-1)))*sum(varQTR)
varI_QTR=(varT_QTR-varS_QTR)/samplerep
print('QTR,VART,VARS,VARI=',varT_QTR,varS_QTR,varI_QTR)

varT_QTI=(samplerep/(B-1))*(np.var(i_sampleQTI) * B)
varS_QTI=(1/(B*(samplerep-1)))*sum(varQTI)
varI_QTI=(varT_QTI-varS_QTI)/samplerep
print('QTI,VART,VARS,VARI=',varT_QTI,varS_QTI,varI_QTI)

varT_TT=(samplerep/(B-1))*(np.var(i_sampleTT) * B)
varS_TT=(1/(B*(samplerep-1)))*sum(varTT)
varI_TT=(varT_TT-varS_TT)/samplerep
print('TT,VART,VARS,VARI=',varT_TT,varS_TT,varI_TT)

varT_QNR=(samplerep/(B-1))*(np.var(i_sampleQNR) * B)
varS_QNR=(1/(B*(samplerep-1)))*sum(varQNR)
varI_QNR=(varT_QNR-varS_QNR)/samplerep
print('QNR,VART,VARS,VARI=',varT_QNR,varS_QNR,varI_QNR)

varT_QNI=(samplerep/(B-1))*(np.var(i_sampleQNI) * B)
varS_QNI=(1/(B*(samplerep-1)))*sum(varQNI)
varI_QNI=(varT_QNI-varS_QNI)/samplerep
print('QNI,VART,VARS,VARI=',varT_QNI,varS_QNI,varI_QNI)

varT_RNR=(samplerep/(B-1))*(np.var(i_sampleRNR) *B)
varS_RNR=(1/(B*(samplerep-1)))*sum(varRNR)
varI_RNR=(varT_RNR-varS_RNR)/samplerep
print('RNR,VART,VARS,VARI=',varT_RNR,varS_RNR,varI_RNR)

varT_RNI=(samplerep/(B-1))*(np.var(i_sampleRNI) * B)
varS_RNI=(1/(B*(samplerep-1)))*sum(varRNI)
varI_RNI=(varT_RNI-varS_RNI)/samplerep
print('RNI,VART,VARS,VARI=',varT_RNI,varS_RNI,varI_RNI)

varT_DeathRate=(samplerep/(B-1))*(np.var(i_sampleDeathRate) * B)
varS_DeathRate=(1/(B*(samplerep-1)))*sum(varDeathRate)
varI_DeathRate=(varT_DeathRate-varS_DeathRate)/samplerep
print('DeathRate,VART,VARS,VARI=',varT_DeathRate,varS_DeathRate,varI_DeathRate)

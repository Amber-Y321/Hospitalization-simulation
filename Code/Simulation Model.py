
# Call Center HW Project 
# Current SMP Call Center
# Import needed modules

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

ICUbed.SetUnits(40)
Regbed.SetUnits(360)

# These lists collect the across-rep data
QTR = [] # time in regular queue
QTR_lower = []
QTR_upper = []
QTI = [] # time in ICU queue
QTI_lower = []
QTI_upper = []
QNR = [] # number in regular queue
QNI = [] # number in ICU queue
RNR = [] # number of busy regular resource
RNI = [] # number of busy ICU resource
TT = [] # time in whole system
TT_lower = []
TT_upper = []
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
    
    SP = SimRNG.Uniform(0, 1, 5)
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
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T1[Severity], 6), NewPatient)
                QueueTimeReg.Record(0.0) # sum doesn't change, # of observations would change
        else: # the new patient would get worse until severity level reaches to 4
            NewPatient.Status = "Unknown"
            if Regbed.Busy == Regbed.NumberOfUnits:
                NewPatient.NowTreatment = "None" 
                RegQueue.Add(NewPatient)
            else:
                Regbed.Seize(1)
                NewPatient.Status = "Regular"
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T2[Severity],7), NewPatient)
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
        SimFunctions.SchedulePlus(Calendar, "EOI", SimRNG.Expon(T4[Severity],9), Patient)
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
            # "Unknown" status
            elif NextPatient.NowTreatment == "None":
                NextPatient.NowTreatment = "Regular"
                QueueTimeReg.Record(SimClasses.Clock - NextPatient.CreateTime) 
                SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T3[NextPatient.Severity],8), NextPatient)   

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
              SimFunctions.SchedulePlus(Calendar, "EOR", SimRNG.Expon(T1[3],8), DepartingPatient)
              QueueTimeReg.Record(0.0)
          else:
              TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)
              A_D[0] += 1
      elif DepartingPatient.Status == "Deceased":
         A_D[1] += 1
         TotalTime.Record(SimClasses.Clock - DepartingPatient.CreateTime)

          

# main program starts here
for Reps in range(0, 500, 1):
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
    QTR_lower.append(QueueTimeReg.Mean() - 1.96 * QueueTimeReg.StdDev()/np.sqrt(QueueTimeReg.N()))
    QTR_upper.append(QueueTimeReg.Mean() + 1.96 * QueueTimeReg.StdDev()/np.sqrt(QueueTimeReg.N()))
    
    QTI.append(QueueTimeICU.Mean())
    QTI_lower.append(QueueTimeICU.Mean() - 1.96 * QueueTimeICU.StdDev()/np.sqrt(QueueTimeICU.N()))
    QTI_upper.append(QueueTimeICU.Mean() + 1.96 * QueueTimeICU.StdDev()/np.sqrt(QueueTimeICU.N()))
        
    TT.append(TotalTime.Mean())
    TT_lower.append(TotalTime.Mean() - 1.96 * TotalTime.StdDev()/np.sqrt(TotalTime.N()))
    TT_upper.append(TotalTime.Mean() + 1.96 * TotalTime.StdDev()/np.sqrt(TotalTime.N()))
    
    QNR.append(RegQueue.Mean())        
    QNI.append(ICUQueue.Mean())
    RNR.append(Regbed.Mean())  
    RNI.append(ICUbed.Mean())
    
    dr = A_D[1] / (A_D[0] + A_D[1])
    DeathRate.append(dr)
    



'''
# Measure of Error
#  QTR
QTR_MeanCI = [np.mean(QTR) - 1.96 * np.std(QTR) / np.size(QTR), np.mean(QTR) + 1.96 * np.std(QTR) / np.size(QTR)]
QTR_LowerCI = [np.mean(QTR_lower) - 1.96 * np.std(QTR_lower) / np.size(QTR_lower), np.mean(QTR_lower) + 1.96 * np.std(QTR_lower) / np.size(QTR_lower)]
QTR_UpperCI = [np.mean(QTR_upper) - 1.96 * np.std(QTR_upper) / np.size(QTR_upper), np.mean(QTR_upper) + 1.96 * np.std(QTR_upper) / np.size(QTR_upper)]
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Mean of mean of QTR:', np.mean(QTR))
print('CI of mean of QTR:', QTR_MeanCI)
print('95% CI lower bound of mean of QTR:', np.mean(QTR_lower))
print('95% CI lower bound of mean of QTR:', QTR_LowerCI)
print('95% CI upper bound of mean of QTR:', np.mean(QTR_upper))
print('95% CI upper boundof mean of QTR:', QTR_UpperCI)
#QTI
QTI_MeanCI = [np.mean(QTI) - 1.96 * np.std(QTI) / np.size(QTI), np.mean(QTI) + 1.96 * np.std(QTI) / np.size(QTI)]
QTI_LowerCI = [np.mean(QTI_lower) - 1.96 * np.std(QTI_lower) / np.size(QTI_lower), np.mean(QTI_lower) + 1.96 * np.std(QTI_lower) / np.size(QTI_lower)]
QTI_UpperCI = [np.mean(QTI_upper) - 1.96 * np.std(QTI_upper) / np.size(QTI_upper), np.mean(QTI_upper) + 1.96 * np.std(QTI_upper) / np.size(QTI_upper)]
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Mean of mean of QTI:', np.mean(QTI))
print('CI of mean of QTI:', QTI_MeanCI)
print('95% CI lower bound of mean of QTI:', np.mean(QTI_lower))
print('95% CI lower bound of mean of QTI:', QTI_LowerCI)
print('95% CI upper bound of mean of QTI:', np.mean(QTI_upper))
print('95% CI upper boundof mean of QTI:', QTI_UpperCI)
# TT
TT_MeanCI = [np.mean(TT) - 1.96 * np.std(TT) / np.size(TT), np.mean(TT) + 1.96 * np.std(TT) / np.size(TT)]
TT_LowerCI = [np.mean(TT_lower) - 1.96 * np.std(TT_lower) / np.size(TT_lower), np.mean(TT_lower) + 1.96 * np.std(TT_lower) / np.size(TT_lower)]
TT_UpperCI = [np.mean(TT_upper) - 1.96 * np.std(TT_upper) / np.size(TT_upper), np.mean(TT_upper) + 1.96 * np.std(TT_upper) / np.size(TT_upper)]
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Mean of mean of TT:', np.mean(TT))
print('CI of mean of TT:', TT_MeanCI)
print('95% CI lower bound of mean of TT:', np.mean(TT_lower))
print('95% CI lower bound of mean of TT:', TT_LowerCI)
print('95% CI upper bound of mean of TT:', np.mean(TT_upper))
print('95% CI upper boundof mean of TT:', TT_UpperCI)'''

thedata = {'RegularWaitingTime': QTR, 'ICUWaitingTime': QTI, 'TotalTime': TT, 'RegularQueueNum': QNR, 'ICUQueueNum': QNI, 'RegularBusyNum': RNR, 'ICUBusyNum': RNI, 'DeathRate': DeathRate}
mydata = pd.DataFrame(data=thedata)
print("Means of Our Statistics")
print(mydata.mean())
print("+/- 95% CI")
print(1.96*mydata.std()/np.sqrt(mydata.count()))
print("Relative error")
print(1.96*mydata.std()/np.sqrt(mydata.count())/mydata.mean())
print("Number of reps =", mydata['RegularWaitingTime'].count())
   

'''
for i in range(0,len(QTR)):
    QTR_lower.append(QTR[i] - 1.96 * QTR_std[i]/np.sqrt(QueueTimeReg.N()))
for i in range(0,len(QTR)):
    QTR_upper.append(QTR[i] + 1.96 * QTR_std[i]/np.sqrt(QueueTimeReg.N()))

for i in range(0,len(QTI)):
    QTI_lower.append(QTI[i] - 1.96 * QTI_std[i]/np.sqrt(QueueTimeICU.N()))
for i in range(0,len(QTI)):
    QTI_upper.append(QTI[i] + 1.96 * QTI_std[i]/np.sqrt(QueueTimeICU.N()))
    
for i in range(0,len(TT)):
    TT_lower.append(TT[i] - 1.96 * TT_std[i]/np.sqrt(TotalTime.N()))
for i in range(0,len(TT)):
    TT_upper.append(TT[i] + 1.96 * TT_std[i]/np.sqrt(TotalTime.N())) '''





    
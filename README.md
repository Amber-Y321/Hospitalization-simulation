# Healthcare System Management under COVID-19 Pandemic
Under COVID-19 pandemic, the hospital resource (i.e., doctors, nurses, beds, 
equipment) allocation directly affects the public health. Here, we consider a NYC hospital treatment and developed a discrete-event simulation of emergency department to assess the system performance, predict the future response, and guide the decision making. 

## Data Description
hospitalization: patient admission time, patient ID, patient encounter ID, patient severity level, living status, patient discharge time

ICU: patient occupation date, patient encounter ID, patient ID

NYC hospital resource: the number of ICU beds and regular beds (Mar 26th - Nov 9th) in all of NYC hospitals.

## Data Processing
Datetime transformation: calculate the sevice time (discharge date - admission date), ICU service time (days patient stays in ICU bed), regular service time (days patient stays in regular bed)

Severity level: divide the original value (0.00-0.99) to 5 levels

<img width="426" alt="image" src="https://user-images.githubusercontent.com/74312026/155050890-46353837-5b0a-4cd8-b03f-bafb14413112.png"> 
<img width="344" alt="image" src="https://user-images.githubusercontent.com/74312026/155051308-d3cf9e04-37e0-4203-8e93-06d574fb94de.png">

Hospital bed number ratio: The ratio of regular bed number to ICU bed number was 9:1 at the beginning. But later, due to high demand of ICU, more ICU beds were added, so the ratio was fallen to 5. As the confirmed patient number deceased, this ratio went back to 6 in June. And from July, this ratio stabilized at 7.

<img width="396" alt="image" src="https://user-images.githubusercontent.com/74312026/155052717-ce336800-a9d1-45d7-a1f4-da7b57ecb3e2.png">   <img width="285" alt="image" src="https://user-images.githubusercontent.com/74312026/155052845-1904a801-baa0-4a8b-be68-d62c76a89e37.png">

The processed data is shown as:

<img width="960" alt="image" src="https://user-images.githubusercontent.com/74312026/155051672-f317bd61-54e0-4f32-b47d-eac270b3f32f.png">

## Assumptions 
✓ Assume that only patients with level 4 or 5 would be considered to offer ICU treatment. 
✓ Assume that patients would be transfered to regular bed once severity level drops below 4, considering the high cost and high demand of ICU.
✓ Assume that Patients’ severity levels wouldn't change while waiting for the test results or treatments. (lack of data of severity level change under none-treatment situation)

## Model Components
There are two types of models: input models (patient arrival rate, service time & severity progression probability) and simulation model

#### Patient arrival rate model (Piece-wise non-stationary Poisson)
Patient arrival number per day is shown as:

<img width="262" alt="image" src="https://user-images.githubusercontent.com/74312026/155066246-439fa56d-9a5d-4c08-9e92-3e2ae9193fe3.png">

The figure shows that the patient arrival distribution is non-stationary. So, arrival data is respectively divided with 5-day, 10-day, 15-day intervals, and then calculated mean of each interval, and fitted Poisson distribution:

<img width="365" alt="image" src="https://user-images.githubusercontent.com/74312026/155067750-5fb3ca4a-f3e5-419d-a005-a9a1424cecad.png">

Obviously, the non-stationary Poisson distribution with 5-day intervals is closest to 
the real data. Furthermore, after doing 1000-time bootstraps of goodness-of-fit test (K-S test) , the 95% CI of p-value is [0.95, 0.96]. Both the upper bound and lower bound of p-value cannot reject the null hypothesis.

Then we used thinning approach to generate patients’ inter-arrival time.

#### Severity level, Progression probability, Service time distributions
Patients would be assigned a severity level:

<img width="457" alt="image" src="https://user-images.githubusercontent.com/74312026/155180704-8979131a-9527-4c4d-890b-80f04fa47121.png">

Progression probability is the survival probability for patients with different severity levels:

<img width="224" alt="image" src="https://user-images.githubusercontent.com/74312026/155182270-dedf7635-d9b9-4407-a1a7-9476af803b3c.png">

P1i: probability of patients survive with severity level i under regular treatment

P2i: probability of patients survive with severity level i under ICU treatment

P3i: probability of patients survive with severity level i under regular treatment despite should be under ICU

Service time is the number of days that patients spend until getting to the next stage (ICU, regular, discharge, death):

<img width="322" alt="image" src="https://user-images.githubusercontent.com/74312026/155190826-fbe8ffce-4e64-4016-a71b-c981b0cafc68.png">

T1i: days of patients with severity level i staying in regular bed until discharge

T2i: days of patients with severity level i staying in regular bed until the severity level reaches to 4

T3i: days of patients with severity level i staying in regular bed until death if there is no ICU available

T4i: days of patients with severity level i staying in ICU untill discharge

T5i: days of patients with severity level i staying in ICU until death

T6i: days of patients with severity level i staying in regular bed instead of ICU but discharge in the end

#### Hospitalization system simulation model
The flowchart starts from admission (with a severity level) to discharge (alive/deceased):

<img width="552" alt="image" src="https://user-images.githubusercontent.com/74312026/155194580-c59eee7f-3fa1-48d2-9fa9-25207f514708.png">

If the severity level < 4, the patient needs a regular bed, otherwise, the patient needs ICU treatment immediately. 

1. For patients that should be sent to ICU:

  ICU available: get better and be transfered to regular (or discharge if no regular bed available), or die in ICU
  
  ICU unavailable: be put at the first one of the regular queue, and be added to the ICU queue: get better in regular and discharge, or get worse (enter ICU or die before entering ICU)
 
2. For patients that should be sent to regular beds:

  Get better and discharge
  
  Get worse, and go to the situation above

3. ICU queue:

For patients with severity level > 3: 
o Still in the regular queue.
o Under regular treatment
o Already deceased, then pop the next one in queue.

For patients with severity level <= 3, they get worse while in regular beds:
o Still stays in regular beds.
o Already deceased, thenpop the next one in queue.

4. Regular queue:

For patients with severity level <= 3, pop one by one

For patients with severity level > 3, either get better or get worse under regular treatment. But if they will get worse, check if they have already 
entered ICU. If yes, then pop the next one in queue

## Result Analysis
#### Input uncertainty
Use the sample variance of output fed with b bootstrapped input model to estimate the impact of unput uncertainty. Consider that patient daily arrival rate follows non-stationary Poisson distribution with arrival rate λi. By using parametric Bootstrap method, get within-replication variance, between-replication variance, and then overall input uncertainty variance.

<img width="563" alt="image" src="https://user-images.githubusercontent.com/74312026/155218787-d4a008ef-80d8-4549-895c-365065c7eba6.png">

#### Output analysis
Simulation performance given different resource units: the number of resource units cannot get infinitely large, considering costs of machines, operation and maintainance. So, 70 ICU is a appropriate number since the results are acceptable and even if we increase this number, results won’t have significant change.

  <img width="440" alt="image" src="https://user-images.githubusercontent.com/74312026/155220985-cef9cf03-d588-4b87-a70e-5f43fdad398b.png"><img width="440" alt="image" src="https://user-images.githubusercontent.com/74312026/155221036-5913587f-9c9f-4bbf-9386-bfe1a9a57a68.png">
  
Decide optimal number is: 70 ICU, 650 regular beds

#### Measure of error & risk
Waiting time in regular queue:
<img width="699" alt="image" src="https://user-images.githubusercontent.com/74312026/155222097-8a5ea2be-5b6b-492a-922a-a38a94cd0a49.png">

Waiting time in ICU queue:
<img width="701" alt="image" src="https://user-images.githubusercontent.com/74312026/155222142-399e8e2c-7e9a-4bf0-84a7-678d32fae594.png">

Total time in hospital:
<img width="701" alt="image" src="https://user-images.githubusercontent.com/74312026/155222326-fa70c052-4c09-4a2a-ad1c-9314c8fa3226.png">

Error can be removed by increasing replication time. As the replication time increases, the 95% CIs of the mean, lower bound and upper bound all get narrow. However, inherit risk cannot be simulated away, which means that the results always will be intervals instead of fixed numbers. For example, we can think with certain that the mean, lower bound and upper bound of total time in the system are 10.78, 10.481 and 11.079, but we cannot give a specific system total time.





  

  



























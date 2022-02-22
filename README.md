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

The processed data is shown as:

<img width="960" alt="image" src="https://user-images.githubusercontent.com/74312026/155051672-f317bd61-54e0-4f32-b47d-eac270b3f32f.png">




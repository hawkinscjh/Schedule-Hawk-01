# Schedule-Hawk-01
Full stack scheduling API on Google Cloud Platform using Python/Flask that implements a partner's microservice to generate a downloadable/printable 
CSV of the schedule.

Partner Communication Contract:

Requests:

Request data by calling jsonToTxt.py after exporting json data to local file named 'myJson.json'

Json format should be in the format of the example shown below.

[
    {
        "items": [
            {
                "desc": "Honey Crisp",
                "name": "apple"
            },
            {
                "desc": "Boneless Skinless thighs",
                "name": "Chicken"
            }
        ],
        "title": "Grocery"
    },
    {
        "items": [
            {
                "desc": "Thursday at 9am",
                "name": "Doctor"
            },
            {
                "desc": "Monday 10am",
                "name": "Dentist"
            }
        ],
        "title": "Appointments"
    }
]

Receive:

Receive data by reading local 'tasks.txt' file created by jsonToTxt.py.
Text file created will be in the format shown below.

Grocery 
- apple: Honey Crisp 
- Chicken: Boneless Skinless thighs 

Appointments 
- Doctor: Thursday at 9am 
- Dentist: Monday 10am 

UML Diagram:

![image](https://user-images.githubusercontent.com/59400213/180667332-f6654a71-b9b4-44db-abfe-63e75131147d.png)


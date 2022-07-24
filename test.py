import csv
import json
import subprocess
import time

with open('static\myfile.json', 'r+') as f:
    x = json.load(f)

schedule_info = ['Date', 'Shift', 'Working']
  
with open('static\schedule.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = schedule_info)
    writer.writeheader()
    writer.writerows(x)
csvfile.close()
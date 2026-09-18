import json

with open("../data/courses.json") as my_file:
    data = my_file.read()

courses = json.loads(data)
print(courses)

for course in courses:
    print(course["name"])


import urllib.request

my_request = urllib.request.urlopen("https://studies.cs.helsinki.fi/stats-mock/api/courses")
data = my_request.read()

courses = json.loads(data)
print(courses)
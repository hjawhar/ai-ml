with open("../data/example.txt") as new_file:
    contents = new_file.read()
    print(contents)

print("-"*50)

with open("../data/example.txt") as new_file:
    count = 0
    total_length = 0

    for line in new_file:
        line = line.replace("\n", "")
        count += 1
        print("Line", count, line)
        length = len(line)
        total_length += length

print("Total length of lines:", total_length)

print("-"*50)

with open("../data/grades.csv") as new_file:
    for line in new_file:
        line = line.replace("\n", "")
        parts = line.split(";")
        name = parts[0]
        grades = parts[1:]
        print("Name:", name)
        print("Grades:", grades) 

print("-"*50)

with open("../data/new_file.txt", "w") as my_file:
    my_file.write("Hello there!\n")
    my_file.write("This is the second line\n")
    my_file.write("This is the last line\n")

print("-"*50)

with open("../data/coders.csv", "w") as my_file:
    my_file.write("Eric;Windows;Pascal;10\n")
    my_file.write("Matt;Linux;PHP;2\n")
    my_file.write("Alan;Linux;Java;17\n")
    my_file.write("Emily;Mac;Cobol;9\n")

with open("../data/new_file.txt", "w") as my_file:
    pass

# the command to delete files is in the os module
import os

os.remove("../data/new_file.txt")


try:
    with open("../data/file_not_found.txt") as my_file:
        for line in my_file:
            print(line)
except FileNotFoundError:
    print("The file example.txt was not found")
except PermissionError:
    print("No permission to access the file example.txt")



try:
    with open("../data/file_not_found.txt") as my_file:
        for line in my_file:
            print(line)
except:
    print("There was an error when reading the file.")
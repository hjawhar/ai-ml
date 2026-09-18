def print_stars():
    n = 10 # number of layers in the pyramid
    row = "*"

    while n > 0:
        print(" " * n + row)
        row += "**"
        n -= 1

def basic_loop(start, end, inc): 
    for n in range(start, end, inc):
        print(n)

def basic_iteration[T](n: list[T]): 
    for i in n:
        print(i)

def format_text_basic(name): 
    print(f"My name is {name}")

def smallest(a, b):
    if a < b:
        return a
    return b

def largest(a, b):
    if a > b:
        return a
    return b

def sum(a, b):
    return a + b

def sort_list(list: list[int]): 
    list.sort() 
    return list

def revert_list(list: list[int]): 
    list.reverse() 
    return list

def insert_at(list: list[int], idx: int, value: int): 
    list.insert(idx, value)
    return list

def remove(list: list[int], value: int): 
    list.remove(value)
    return list

def remove_index_at(list: list[int], idx: int): 
    list.pop(idx)
    return list

def anagrams(n1: str, n2: str):
    return sorted(n1) == sorted(n2)

def palindromes(n1: str):  
    return n1 == n1[::-1]

def distinct[T](list: list[T]):  
    return set(list)

def factorial(n: int):
    if n > 1:
        return factorial(n-1) * n
    else:
        return n

# print_stars()
basic_loop(1,100,1)
print("-"*50)
print("Smallest number:", smallest(55,600))
print("Smallest number:", smallest(55,15))
print("-"*50)
print("Largest number:", largest(55,600))
print("Largest number:", largest(55,15))
print("-"*50)
print("Sum of numbers:", sum(55,600))
print("Sum of numbers:", sum(55,15))
print("-"*50)

current_list = [5,3,6,8,99,2,1,7,500,300,200,100]
print("Sort list:", sort_list(current_list))
print("Reverse list:", revert_list(current_list))
print("Insert at index:", insert_at(current_list, 0, 500000))
print("Remove value:", remove(current_list, 500))
print("Remove index:", remove_index_at(current_list, 1))

print("-"*50)
print("Anagrams example:")
print("Anagram:", anagrams("tame", "meta")) # True
print("Anagram:", anagrams("tame", "mate")) # True
print("Anagram:", anagrams("tame", "team")) # True
print("Anagram:", anagrams("tabby", "batty")) # False
print("Anagram:", anagrams("python", "java")) # False

print("-"*50)
print("Palindromes example:")

print("Palindrome:", palindromes("python"))
print("Palindrome:", palindromes("java"))
print("Palindrome:", palindromes("oddoreven"))
print("Palindrome:", palindromes("neveroddoreven"))
print("-"*50)
format_text_basic("Hassan")
print("-"*50)
basic_iteration(["Hassan","Test","Python"])

my_dictionary = {}

my_dictionary["apina"] = "monkey"
my_dictionary["banaani"] = "banana"
my_dictionary["cembalo"] = "harpsichord"

print(len(my_dictionary))
print(my_dictionary)
print(my_dictionary["apina"])

results = {}
results["Mary"] = 4
results["Alice"] = 5
results["Larry"] = 2
print(results)

lists = {}
lists[5] = [1, 2, 3]
lists[42] = [5, 4, 5, 4, 5]
lists[100] = [5, 2, 3]
print(lists)

print(factorial(4))

print("-"*50)

from random import randint

for i in range(10):
    print("The result of the throw:", randint(1, 6))

from datetime import datetime

my_time = datetime.now()
print(my_time)

print("Day:", my_time.day)
print("Month:", my_time.month)
print("Year:", my_time.year)

print(my_time.strftime("%d/%m/%Y"))
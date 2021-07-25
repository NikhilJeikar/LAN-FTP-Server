import hashlib
import os

_Users = []

_ReadUserFile = open('UserData.txt', 'r', encoding='utf-8')
for i in _ReadUserFile.readlines():
    i = i.split(',')
    _Users.append(i[0])

UName = input('Enter the desired user name: ')
UName = UName.encode()
UData = hashlib.sha512(UName).hexdigest()
Pass = input("Enter the password: ")
Pass = Pass.encode()
PData = hashlib.sha512(Pass).hexdigest()
Storage = input("Storage (GB): ")
Storage = int(Storage) * 1024 * 1024 * 1024

if UData not in _Users:
    _WriteUserFile = open('UserData.txt', 'a', encoding='utf-8')
    _WriteUserFile.write(f"{UData},{PData},{Storage}\n")
    os.mkdir(UData)
else:
    print("Unable to create already an user exist in this name")

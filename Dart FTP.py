import socket
import os
import json
from Dart_Constants import *

from Thread import Thread

# Constant
SERVER_HOST = "192.168.1.22"
SERVER_PORT = 24680
BUFFER_SIZE = 1024 * 1024
Max = 10


def UserRefresh():
    global Users, Passwords, Storages
    for i in ReadUserFile.readlines():
        i = i.split(',')
        Users.append(i[0])
        Passwords.append(i[1])
        Storages.append(i[2])


def JSONGen(Dir):
    Directories = []
    Files = []
    Dict = {}
    for root, directories, files in os.walk(Dir, topdown=False):
        for name in files:
            Files.append(os.path.join(root, name))
        for name in directories:
            Directories.append(os.path.join(root, name))

    for i in Directories:
        Pointer = Dict
        for j in i.split('\\'):
            if Pointer.get(j) is not None:
                Pointer = Pointer.get(j)
            else:
                Pointer[j] = {FOLDER_EXCEPTION: {}}
                Pointer = Pointer[j]
    for i in Files:
        Pointer = Dict
        for j in i.split('\\'):
            if Pointer.get(j) is not None:
                Pointer = Pointer.get(j)
            else:
                Pointer[j] = {}
                Pointer = Pointer[j]
    return json.dumps(Dict, indent=4)


# Initialize
Users = []
Passwords = []
Storages = []

WriteUserFile = open('UserData.txt', 'a', encoding='utf-8')
ReadUserFile = open('UserData.txt', 'r', encoding='utf-8')
UserRefresh()


def Command(Client, Address):
    User = None
    Storage = None
    CD = ""
    global ReadUserFile, WriteUserFile
    print(f"[+] {Address} is connected.")
    while True:
        data = Client.recv(BUFFER_SIZE)
        data = data.decode()
        print(data)
        if data != "":
            lis = data.split(SEPARATOR)
            if lis[0] == LOGIN:
                if lis[1] in Users:
                    Use = Users.index(lis[1])
                    if lis[2] == Passwords[Use]:
                        User = lis[1]
                        Storage = Storages[Use]
                        Client.send(f"{LOGIN}{SEPARATOR}{TRUE}{SEPARATOR}{TRUE}".encode())
                    else:
                        Client.send(f"{LOGIN}{SEPARATOR}{TRUE}{SEPARATOR}{FALSE}".encode())
                else:
                    Client.send(f"{LOGIN}{SEPARATOR}{FALSE}".encode())
            elif lis[0] == CREATE:
                if lis[1] == FOLDER:
                    try:
                        os.mkdir(User + "/" + lis[2], mode=0o666)
                        Client.send((CREATE + SEPARATOR + FOLDER).encode())
                    except FileNotFoundError:
                        Client.send((ERROR + SEPARATOR + "Invalid Location").encode())
                    except FileExistsError:
                        Client.send((ERROR + SEPARATOR + "File already exist").encode())
            elif lis[0] == FETCH:
                if lis[1] == METADATA:
                    Client.send((METADATA + SEPARATOR + Storage + SEPARATOR + JSONGen(User)).encode())
        else:
            break
    print(f"[+] {Address} is disconnected.")


def Start():
    Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    Sock.bind((SERVER_HOST, SERVER_PORT))
    Sock.listen(Max)

    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
    while True:
        client, address = Sock.accept()
        print(f"[+] {address} is connecting.")
        t = Thread(target=Command, args=(client, address), daemon=True)
        t.start()
        t.join()


Start()

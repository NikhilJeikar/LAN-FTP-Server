import socket
import os
import shutil
import json
from Dart_Constants import *

from Thread import Thread

# Constant
SERVER_HOST = "192.168.1.22"
SERVER_PORT = 24680
BUFFER_SIZE = 1024 * 1024
Max = 10


# Initialize


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


class Operations:
    def __init__(self, Client):
        self._User = ""
        self._Storage = ""
        self._Size = 0

        self._Client = Client
        self._Users = []
        self._Passwords = []
        self._Storages = []

        self._WriteUserFile = open('UserData.txt', 'a', encoding='utf-8')
        self._ReadUserFile = open('UserData.txt', 'r', encoding='utf-8')
        self.UserRefresh()

    def get_size(self, start_path):
        self._Size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    self._Size += os.path.getsize(fp)

    def UserRefresh(self):
        for i in self._ReadUserFile.readlines():
            i = i.split(',')
            self._Users.append(i[0])
            self._Passwords.append(i[1])
            self._Storages.append(i[2])

    def Login(self, lis):
        if lis[1] in self._Users:
            Use = self._Users.index(lis[1])
            if lis[2] == self._Passwords[Use]:
                self._User = lis[1]
                self._Storage = self._Storages[Use]
                self._Client.send(f"{LOGIN}{SEPARATOR}{TRUE}{SEPARATOR}{TRUE}".encode())
            else:
                self._Client.send(f"{LOGIN}{SEPARATOR}{TRUE}{SEPARATOR}{FALSE}".encode())
        else:
            self._Client.send(f"{LOGIN}{SEPARATOR}{FALSE}".encode())

    def NewFolder(self, lis):
        if lis[1] == FOLDER:
            try:
                os.mkdir(self._User + "/" + lis[2], mode=0o666)
                self._Client.send((CREATE + SEPARATOR + FOLDER).encode())
            except FileNotFoundError:
                self._Client.send((ERROR + SEPARATOR + "Invalid Location").encode())
            except FileExistsError:
                self._Client.send((ERROR + SEPARATOR + "File already exist").encode())

    def Delete(self, lis):
        if lis[1] == FOLDER:
            try:
                shutil.rmtree(self._User + "/" + lis[2])
            except FileExistsError or FileNotFoundError:
                self._Client.send((ERROR + SEPARATOR + "Unable to delete the folder.").encode())
        elif lis[1] == FILE:
            try:
                os.remove(self._User + "/" + lis[2])
            except FileExistsError or FileNotFoundError:
                self._Client.send((ERROR + SEPARATOR + "Unable to delete the file.").encode())
        else:
            self._Client.send((ERROR + SEPARATOR + "Some error occurred try after refreshing").encode())

    def Fetch(self, lis):
        if lis[1] == METADATA:
            self.get_size(self._User)
            self._Client.send((METADATA + SEPARATOR + self._Storage + SEPARATOR + str(
                self._Size) + SEPARATOR + JSONGen(self._User)).encode())

    def WriteFile(self, lis):
        File = open(self._User + "/" + lis[2], "wb+")
        self._Client.send((UPLOAD + SEPARATOR + ACKNOWLEDGE).encode())
        FileSize = int(lis[1])
        Buf = BUFFER_SIZE
        Bytes = bytes()
        while FileSize != len(Bytes):
            if FileSize - len(Bytes) < BUFFER_SIZE:
                Buf = FileSize - len(Bytes)
            Bytes = Bytes + self._Client.recv(Buf)
        Bytes = Bytes.decode()
        Bytes = Bytes.replace('[', '')
        Bytes = Bytes.replace(']', '')
        Bytes = Bytes.replace(' ', '')
        for i in Bytes.split(','):
            File.write(int(i).to_bytes(1, 'big'))
        File.close()
        self.Fetch([FETCH, METADATA])

    def ReadFile(self, lis):
        File = open(self._User + "/" + lis[1], "rb")
        Data = File.read()
        self._Client.send((DOWNLOAD + SEPARATOR + str(len(Data)) + SEPARATOR + lis[2]).encode())
        data = self._Client.recv(BUFFER_SIZE)
        data = data.decode()
        if data == ACKNOWLEDGE:
            self._Client.send(Data)


def Command(Client, Address):
    Op = Operations(Client)
    print(f"[+] {Address} is connected.")
    while True:
        data = Client.recv(BUFFER_SIZE)
        data = data.decode()
        if data != "":
            lis = data.split(SEPARATOR)
            if lis[0] == LOGIN:
                Op.Login(lis)
            elif lis[0] == CREATE:
                Op.NewFolder(lis)
            elif lis[0] == FETCH:
                Op.Fetch(lis)
            elif lis[0] == DELETE:
                Op.Delete(lis)
            elif lis[0] == UPLOAD:
                Op.WriteFile(lis)
            elif lis[0] == DOWNLOAD:
                Op.ReadFile(lis)
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

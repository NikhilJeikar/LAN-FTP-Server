import sys
import threading


class Thread(threading.Thread):
    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.__killed = False
        self.__Parent = None

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self)

    def __run(self):
        sys.settrace(self.__globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def __globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.__localtrace
        else:
            return None

    def __localtrace(self, frame, event, arg):
        if self.__killed:
            if event == 'line':
                raise SystemExit()
        if self.__Parent is not None:
            if not self.__Parent.isAlive():
                raise SystemExit()
        return self.__localtrace

    def Bind(self, Parent):
        self.__Parent = Parent

    def kill(self):
        self.__killed = True


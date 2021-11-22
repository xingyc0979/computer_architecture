import numpy as np
import random

"""
LOOP:	
L.D	F0,0(R1)
MUL.D 	F4,F0,F2
S.D	0(R1),F4
DADDUI	R1,R1,#-8
BNE	R1,R2,LOOP
"""


class Tomasulo:
    def __init__(self):
        self.opKind = ["Load", "Mult", "Store", "Add"]
        self.opType = {"L.D": "Load", "MUL.D": "Mult", "S.D": "Store", "DADDUI": "Add", "BNE": "Add", "DIVD": "Mult"}
        self.latency = {
            "Load": 1,
            "Mult": 10,
            "Store": 1,
            "Add": 2
        }
        self.Clock = 0
        self.issueQuene = [Instruction_status()] * 5
        self.instruct = Instructions()
        self.load = [Load()] * 3
        self.store=[Store()]*3
        self.Add = [Reservation_Station("Add", self.latency["Add"])] * 3
        self.Mult = [Reservation_Station("Mult", self.latency["Mult"])] * 3
        self.Register_result_status = Register_result_status()
        self.run()
        self.isFinished = False

    def run(self):
        while not self.isFinished:
            self.runOneClock()

    def runOneClock(self):
        self.issue()
        self.Comp()
        self.Write()
        self.Clock += 1

    def issue(self):
        for i in range(len(self.issueQuene)):
            if self.issueQuene[i].busy == 'No':
                self.issueQuene[i].Busy = 'yes'
                self.issueQuene[i].issue = self.Clock
                opt, oprand = self.instruct.getInfo(self.instruct.pc)
                opt = self.latency[opt]
                if opt == "Load":
                    rt = oprand[0]
                    for i in range(len(self.load)):
                        if self.load[i].busy == 'No':
                            self.load[i].busy = 'yes'
                            self.load[i].Address = oprand[1].split('(')[0] + '+' + oprand[1].split('(')[1].split(')')[0]
                            self.Register_result_status.FU[int(rt[1:])] = opt + i
                if opt == "Mult":
                    rt = oprand[0]
                    rj = oprand[1]
                    rk = oprand[2]
                    for i in range(len(self.Mult)):
                        if self.Mult[i].busy == 'No':
                            self.Mult[i].busy = 'yes'
                            self.Mult[i].Op=opt
                            self.Register_result_status.FU[int(rt[1:])] = opt + i


class Instructions:
    def __init__(self):
        filename = "test.txt"
        self.ass = []
        self.label = {}
        self.pc = 0
        with open(filename, 'r') as f:
            for line in f.readlines():
                self.ass.append(line.strip())
        self.trans = []

    def getInfo(self, i):
        code = self.ass[i]
        if ':' in code:
            code = code.split(':')
            self.label[code[0]] = i
            code = code[1]
        code = code.split('\t')
        opt = code[0]
        operand = code[1].split(',')
        self.pc += 1
        return opt, operand


class Load:
    def __init__(self):
        self.busy = 'No'
        self.Address = 0

class Store:
    def __init__(self):
        self.busy = 'No'
        self.Address = 0

class Instruction_status:
    def __init__(self):
        self.issue = 0
        self.Comp = 0
        self.Result = 0
        self.busy = 'No'


class Reservation_Station:
    def __init__(self, type, time):
        self.type = type
        self.Time = time
        self.busy = 'No'
        self.Op = ''
        self.Vj = ''
        self.Vk = ''
        self.Qj = ''
        self.Qk = ''


class Register_result_status:
    def __init__(self):
        self.FU = ['']*32


if __name__ == '__main__':
    toma = Tomasulo()

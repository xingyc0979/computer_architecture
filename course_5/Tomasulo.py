import numpy as np
import random

"""
LOOP:	L.D	F0, 0(R1)
	MUL.D 	F4, F0, F2
	S.D	0(R1), F4
	DADDUI	R1, R1, #-8
	BNE	R1, R2, LOOP
"""


class Instruction:
    def __init__(self, filename="test.txt"):
        self.insts = []
        for i in range(2):
            with open(filename, 'r') as f:
                for line in f.readlines():
                    self.insts.append(line.strip())
        self.instruction = self.__insSplit(self.insts)
        self.opKind = ["Load", "Mult", "Store", "Add"]
        self.opType = {"L.D": "Load", "MUL.D": "Mult", "S.D": "Store", "DADDUI": "Add", "BNE": "Add"}
        self.latency = {
            "Load": 1,
            "Mult": 10,
            "Store": 1,
            "Add": 2
        }

    def __insSplit(self, inst):
        instruction = []
        for i in range(len(inst)):
            CMD = []
            cmd = inst[i].split()
            if cmd[0] == "LOOP:":
                cmd = cmd[1: len(cmd)]
            CMD.append(cmd[0])
            reg = cmd[1]
            reg = reg.split(",")
            for j in range(len(reg)):
                if reg[j].startswith("#"):
                    reg[j] = reg[j][1:len(reg[j])]
                a = reg[j].split("(")
                for num in range(len(a)):
                    if a[num].endswith(")"):
                        a[num] = a[num][0:len(a[num]) - 1]
                    CMD.append(a[num])
            instruction.append(CMD)
        return instruction


class InstructionStatus:
    def __init__(self):
        self.status = [[0 for i in range(3)] for i in range(10)]
        """
        Issue   Execute  WriteResult
        
        """


class ReservationStation:
    def __init__(self):
        self.ResStation = [[0 for i in range(9)] for i in range(9)]
        self.UnitIndex = {"Load1": 0, "Load2": 1, "Add3": 2, "Add4": 3, "Add5": 4, "Mult6": 5, "Mult7": 6, "Store8": 7,
                          "Store9": 8}
        self.__setInitVal()
        """
        Time Name  Busy Op Vj Vk Qj Qk A
        0   Load1  No
        0   Load2  No
        0    Add1  No
        0    Add2  No
        0    Add3  No
        0    Mult1 No
        0    Mult2 No
        0  Store1  No
        0  Store2  No
        """

    def __setInitVal(self):
        for i in range(2):
            self.ResStation[i][1] = "Load" + str(i + 1)
        for i in range(2, 5):
            self.ResStation[i][1] = "Add" + str(i + 1)
        for i in range(5, 7):
            self.ResStation[i][1] = "Mult" + str(i + 1)
        for i in range(7, 9):
            self.ResStation[i][1] = "Store" + str(i + 1)
        for i in range(9):
            self.ResStation[i][2] = "No"


class RegisterResultStatus:
    def __init__(self):
        self.clock = 0
        self.FU = {"F" + str(i): 0 for i in range(32)}
        self.RU = {"R" + str(i): 0 for i in range(32)}


class Tomasulo:
    def __init__(self):
        self.Ins = Instruction()
        self.InsSta = InstructionStatus()
        self.RS = ReservationStation()
        self.RegResSta = RegisterResultStatus()
        self.TaskQueue = []
        self.InsCache = []  # 装指令的cache
        self.IssueQueue = []  # 设置最大为5
        self.wbQueue = []
        self.ExeQueue = []
        self.pc = 0
        self.iteration = 1
        self.taskUseUnit = {}
        self.LoadInsCache()
        self.LoadBuffer = []
        self.LoadBufferSize = 3
        self.StoreBuffer = []
        self.StoreBufferSize = 3
        self.awqueue = []
        self.run()

    def run(self):
        while self.pc == 0 or len(self.IssueQueue) != 0 or len(self.TaskQueue) != 0\
                or len(self.wbQueue) != 0 or len(self.awqueue) != 0:
            self.runOneClock()

    def runOneClock(self):
        self.RegResSta.clock += 1
        self.WriteBack()
        self.EXECUTE()
        self.Issue()
        self.printResult()


    def LoadInsCache(self):
        self.InsCache = self.Ins.instruction

    # issue
    def LoadIssueQueue(self):
        while len(self.IssueQueue) <= 5:
            if self.pc >= 10:
                break
            self.IssueQueue.append(self.pc)
            self.pc = self.pc + 1
            # 假设预测成功

    def Issue(self):
        self.LoadIssueQueue()
        if len(self.IssueQueue) == 0:
            return
        InsIndex = self.IssueQueue[0]
        Ins = self.InsCache[InsIndex]
        op = Ins[0]
        checkStatus = self.checkIssue(op)[0]
        AvaUnit = self.checkIssue(op)[1]
        if len(AvaUnit) == 0:
            return
        UseUnitIndex = 0
        UseUnit = AvaUnit[UseUnitIndex]
        if checkStatus:
            UnitRow = list(np.array(self.RS.ResStation).T[1]).index(UseUnit) #第二列第几排
            reg1 = Ins[2]  # Vj
            reg2 = Ins[3]  # Vk
            if op != "L.D" and op != "S.D":
                if op == "BNE":
                    self.IssueBNE(Ins, UnitRow)
                else:
                    self.setIssueResReg(reg1, UnitRow, 4)
                    self.setIssueResReg(reg2, UnitRow, 5)
                    if self.RegType(Ins[1]) == "F":
                        self.RegResSta.FU[Ins[1]] = UseUnit
                    elif self.RegType(Ins[1]) == "R":
                        self.RegResSta.RU[Ins[1]] = UseUnit
            else:
                self.IssueLoadAndStore(Ins, UnitRow, UseUnit)
            self.RS.ResStation[UnitRow][2] = "Yes"  # busy = yes
            self.RS.ResStation[UnitRow][3] = op
            if op == "L.D":
                self.LoadBuffer.append(self.RS.ResStation[UnitRow][:])
            elif op == "S.D":
                self.StoreBuffer.append(self.RS.ResStation[UnitRow][:])
            task = self.IssueQueue.pop(0)
            self.TaskQueue.append(task)
            self.taskUseUnit[task] = UnitRow
            self.RS.ResStation[UnitRow][0] = self.Ins.latency[self.Ins.opType[op]]
            self.InsSta.status[task][0] = self.RegResSta.clock
        return

    def setIssueResReg(self, reg, UnitRow, k):  # k=4时是Vj,k=5时是Vk
        regType = self.RegType(reg)
        if regType == "F":
            if self.RegResSta.FU[reg] != 0:
                self.RS.ResStation[UnitRow][k + 2] = self.RegResSta.FU[reg]  # Qj
            else:
                self.RS.ResStation[UnitRow][k] = reg  # Vj
                self.RS.ResStation[UnitRow][k + 2] = 0  # Qj = 0
        elif regType == "R":
            if self.RegResSta.RU[reg] != 0:
                self.RS.ResStation[UnitRow][k + 2] = self.RegResSta.RU[reg]  # Qj
            else:
                self.RS.ResStation[UnitRow][k] = reg  # Vj
                self.RS.ResStation[UnitRow][k + 2] = 0  # Qj = 0

    def RegType(self, Reg):
        if Reg[0] == "F":
            return "F"
        elif Reg[0] == "R":
            return "R"
        else:
            return "Num"

    def checkIssue(self, op):
        TypeofOp = self.Ins.opType[op]
        AvailableIssueUnit = []
        canIssue = False
        if TypeofOp == "Load":
            for i in range(2):
                if self.RS.ResStation[i][2] == "No":
                    AvailableIssueUnit.append(self.RS.ResStation[i][1])
        elif TypeofOp == "Add":
            for i in range(2, 5):
                if self.RS.ResStation[i][2] == "No":
                    AvailableIssueUnit.append(self.RS.ResStation[i][1])
        elif TypeofOp == "Mult":
            for i in range(5, 7):
                if self.RS.ResStation[i][2] == "No":
                    AvailableIssueUnit.append(self.RS.ResStation[i][1])
        elif TypeofOp == "Store":
            for i in range(7, 9):
                if self.RS.ResStation[i][2] == "No":
                    AvailableIssueUnit.append(self.RS.ResStation[i][1])
        if len(AvailableIssueUnit) != 0:
            canIssue = True
        return [canIssue, AvailableIssueUnit]

    def IssueLoadAndStore(self, Ins, UnitRow, UseUnit):
        op = Ins[0]
        if op != "L.D" and op != "S.D":
            return
        if op == "L.D":
            imm = Ins[2]
            rt = Ins[1]
            rs = Ins[3]
        else:
            imm = Ins[1]
            rt = Ins[3]
            rs = Ins[2]
        rtType = self.RegType(rt)
        self.setIssueResReg(rs, UnitRow, 4)
        self.RS.ResStation[UnitRow][8] = imm
        if op == "L.D":
            if rtType == "F":
                self.RegResSta.FU[rt] = UseUnit
            elif rtType == "R":
                self.RegResSta.RU[rt] = UseUnit
        else:
            if self.RegResSta.FU[rt] != 0:
                if rtType == "F":
                    self.RS.ResStation[UnitRow][7] = self.RegResSta.FU[rt]
                elif rtType == "R":
                    self.RS.ResStation[UnitRow][7] = self.RegResSta.RU[rt]
            else:
                self.RS.ResStation[UnitRow][5] = rt
                self.RS.ResStation[UnitRow][7] = 0

    def IssueBNE(self, Ins, UnitRow):
        vj = Ins[1]
        vk = Ins[2]
        self.setIssueResReg(vj, UnitRow, 4)
        self.setIssueResReg(vk, UnitRow, 5)

    # execute
    def EXECUTE(self):
        self.watchCDB()
        i = 0
        while i < len(self.TaskQueue):
            task = self.TaskQueue[i]
            i += 1
            TaskUseUnit = self.taskUseUnit[task]
            if self.canAct(task):
            #    rd = self.getrd(self.Ins.instruction[i])
            #    self.awqueue[rd].append(task)
                if self.RS.ResStation[TaskUseUnit][0] != 0:
                    self.RS.ResStation[TaskUseUnit][0] -= 1
                else:
                    if self.RS.ResStation[TaskUseUnit][0] == 0:
                        self.InsSta.status[task][1] = self.RegResSta.clock
                        self.awqueue.append(task)
                        self.TaskQueue.remove(task)
                        i -= 1
    def getrd(self, Ins):
        op = Ins[0]
        if op == "L.D" or op == "MUL.D" or op == "DADDUI":
            return Ins[1]
        else:
            return None

    def getrs(self,Ins):
        op = Ins[0]
        if op == "L.D":
            return [Ins[3]]
        elif op == "MUL.D" or op == "S.D":
            return [Ins[2], Ins[3]]
        elif op == "DADDUI":
            return [Ins[2]]
        elif op == "BNE":
            return [Ins[1],Ins[2]]

    def canAct(self, task):
        UnitRow = self.taskUseUnit[task]
        if self.RS.ResStation[UnitRow][6] == 0 and self.RS.ResStation[UnitRow][7] == 0:
            if self.RS.ResStation[UnitRow][1][0] == "L":
                # if self.LoadBuffer[0][1] == UnitRow:
                return True
            elif self.RS.ResStation[UnitRow][1][0] == "S":
                # if self.StoreBuffer[0][1] == UnitRow:
                return True
            else:
                return True
        return False

    def watchCDB(self):
        for task in self.TaskQueue:
            UseUnit = self.taskUseUnit[task]
            for k in range(4, 6):
                if self.RS.ResStation[UseUnit][k + 2] != 0:
                    relateUnit = self.RS.ResStation[UseUnit][k + 2]
                    if relateUnit != 0:
                        relateUnitRow = self.RS.UnitIndex[relateUnit]
                    if self.RS.ResStation[relateUnitRow][2] == "No":
                        self.RS.ResStation[UseUnit][k + 2] = 0
                        self.RS.ResStation[UseUnit][k] = 0



    # write back
    def WriteBack(self):
        i = 0
        while i < len(self.awqueue):
            NoWAR = True
            ins = self.Ins.instruction[self.awqueue[i]]
            task = self.awqueue[i]
            self.RS.ResStation[self.taskUseUnit[task]][2] = "No"
            for j in range(3, 9):
                self.RS.ResStation[self.taskUseUnit[task]][j] = 0
            for j in range(1, 4):
                reg = self.Ins.instruction[self.taskUseUnit[task]][j]
            if reg[0] == "F":
                self.RegResSta.FU[reg] = 0
            elif reg[0] == "R":
                self.RegResSta.RU[reg] = 0
            rd = self.getrd(ins)
            if rd != None:
                if rd[0] == "F":
                    self.RegResSta.FU[rd] = 0
                elif rd[0] == "R":
                    self.RegResSta.RU[rd] = 0
            for j in range(self.awqueue[i]):
                rs = self.getrs(self.Ins.instruction[j])
                if rd in rs:
                    if self.InsSta.status[j][1] == 0:
                        NoWAR = False
                        break
            if NoWAR:
                self.wbQueue.append(self.awqueue.pop(i))
            else:
                i += 1
        for task in self.wbQueue:
            self.InsSta.status[task][2] = self.RegResSta.clock

        self.wbQueue.clear()

    def printResult(self):
        print("Instruction Status:")
        for i in range(10):
            print(self.Ins.insts[i], end='')
            print(" "*(25 - len(self.Ins.insts[i])),end='')
            print(self.InsSta.status[i])

        print("Reservation Stations:")
        print("Time Name    Busy  Op Vj Vk Qj Qk A")
        for i in range(9):
            print(self.RS.ResStation[i])
        print("Register result status:")
        print("clock=", self.RegResSta.clock)
        print(self.RegResSta.FU)
        print(self.RegResSta.RU)
        print("-----------------------------------------------------------")

if __name__ == '__main__':
    tom = Tomasulo()



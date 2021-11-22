"""
LOOP:	
L.D	F0, 0(R1)
MUL.D 	F4, F0, F2
S.D	0(R1), F4
DADDUI	R1, R1, #-8
BNE	R1, R2, LOOP
"""
opKind = ["Load", "Mult", "Store", "Add"]
opType = {"L.D": "Load", "MUL.D": "Mult", "S.D": "Store", "DADDUI": "Add", "BNE": "Add"}
latency = {
    "Load": 1,
    "Mult": 10,
    "Store": 1,
    "Add": 2
}


class Instruction:
    def __init__(self, ite):
        filename = "test.txt"
        self.assembles = []
        for i in range(ite):
            with open(filename, 'r') as f:
                for line in f.readlines():
                    self.assembles.append(line.strip())
        self.instruction = self.assembles_Split(self.assembles)

    def assembles_Split(self, assemble):
        instruction = []
        for i in range(len(assemble)):
            code = []
            cmd = assemble[i].split()
            if cmd[0] == "LOOP:":
                cmd = cmd[1: len(cmd)]
            code.append(cmd[0])
            reg = cmd[1].split(",")
            for j in range(len(reg)):
                if "#" in reg[j]:
                    code.append(reg[j][1:len(reg[j])])
                elif "(" in reg[j]:
                    code.append(reg[j].split('(')[0])
                    code.append(reg[j].split("(")[1].split(")")[0])
                else:
                    code.append(reg[j])
            instruction.append(code)
        return instruction


class InstructionStatus:
    def __init__(self, ite):
        self.status = [[0 for i in range(3)] for i in range(5 * ite)]


class ReservationStation:
    def __init__(self):
        self.ResStation = [[0 for i in range(9)] for i in range(9)]
        self.UnitIndex = {"Load1": 0, "Load2": 1, "Add3": 2, "Add4": 3, "Add5": 4, "Mult6": 5,
                          "Mult7": 6, "Store8": 7, "Store9": 8}
        for i in range(9):
            self.ResStation[i][1] = list(self.UnitIndex.keys())[list(self.UnitIndex.values()).index(i)]
            self.ResStation[i][2] = "No"


class RegisterResultStatus:
    def __init__(self):
        self.FU = {"F" + str(i): 0 for i in range(8)}
        self.RU = {"R" + str(i): 0 for i in range(8)}


class Tomasulo:
    def __init__(self):
        self.ite = 3 #迭代次数
        self.Ins = Instruction(self.ite)
        self.InsSta = InstructionStatus(self.ite)
        self.RS = ReservationStation()
        self.RegResSta = RegisterResultStatus()
        self.TaskQueue = []
        self.InsCache = []
        self.IssueQueue = []  # 最大为5
        self.wbQueue = []
        self.ExeQueue = []
        self.pc = 0
        self.clock=0
        self.taskUseUnit = {}
        self.LoadInsCache()
        self.LoadBuffer = []
        self.LoadBufferSize = 3
        self.StoreBuffer = []
        self.StoreBufferSize = 3
        self.awqueue = []
        self.run()

    def run(self):
        while self.pc == 0 or len(self.IssueQueue) != 0 or len(self.TaskQueue) != 0 \
                or len(self.wbQueue) != 0 or len(self.awqueue) != 0:
            self.runOneClock()

    def runOneClock(self):
        self.clock += 1
        self.WriteBack()
        self.EXECUTE()
        self.Issue()
        self.printResult()

    def LoadInsCache(self):
        self.InsCache = self.Ins.instruction

    def LoadIssueQueue(self):
        while len(self.IssueQueue) <= 5:
            if self.pc >= self.ite * 5:
                break
            self.IssueQueue.append(self.pc)
            self.pc = self.pc + 1

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
            for i in range(9):
                if UseUnit in self.RS.ResStation[i]:
                    UnitRow = i
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
            self.RS.ResStation[UnitRow][2] = "Yes"
            self.RS.ResStation[UnitRow][3] = op
            if op == "L.D":
                self.LoadBuffer.append(self.RS.ResStation[UnitRow][:])
            elif op == "S.D":
                self.StoreBuffer.append(self.RS.ResStation[UnitRow][:])
            task = self.IssueQueue.pop(0)
            self.TaskQueue.append(task)
            self.taskUseUnit[task] = UnitRow
            self.RS.ResStation[UnitRow][0] = latency[opType[op]]
            self.InsSta.status[task][0] = self.clock
        return

    def setIssueResReg(self, reg, UnitRow, k):
        regType = self.RegType(reg)
        if regType == "F":
            if self.RegResSta.FU[reg] != 0:
                self.RS.ResStation[UnitRow][k + 2] = self.RegResSta.FU[reg]  # Qj
            else:
                self.RS.ResStation[UnitRow][k] = reg  # Vj
                self.RS.ResStation[UnitRow][k + 2] = 0  # Qj
        elif regType == "R":
            if self.RegResSta.RU[reg] != 0:
                self.RS.ResStation[UnitRow][k + 2] = self.RegResSta.RU[reg]  # Qj
            else:
                self.RS.ResStation[UnitRow][k] = reg  # Vj
                self.RS.ResStation[UnitRow][k + 2] = 0  # Qj

    def RegType(self, Reg):
        if Reg[0] == "F" or Reg[0] == "R":
            return Reg[0]
        else:
            return "Num"

    def checkIssue(self, op):
        TypeofOp = opType[op]
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
                if self.RS.ResStation[TaskUseUnit][0] != 0:
                    self.RS.ResStation[TaskUseUnit][0] -= 1
                else:
                    if self.RS.ResStation[TaskUseUnit][0] == 0:
                        self.InsSta.status[task][1] = self.clock
                        self.awqueue.append(task)
                        self.TaskQueue.remove(task)
                        i -= 1

    def getrs(self, Ins):
        op = Ins[0]
        if op == "L.D":
            return [Ins[3]]
        elif op == "MUL.D" or op == "S.D":
            return [Ins[2], Ins[3]]
        elif op == "DADDUI":
            return [Ins[2]]
        elif op == "BNE":
            return [Ins[1], Ins[2]]

    def canAct(self, task):
        UnitRow = self.taskUseUnit[task]
        if self.RS.ResStation[UnitRow][6] == 0 and self.RS.ResStation[UnitRow][7] == 0:
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

    def WriteBack(self):
        i = 0
        while i < len(self.awqueue):
            Conflict = True
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
            op = ins[0]
            if op == "L.D" or op == "MUL.D" or op == "DADDUI":
                rd = ins[1]
            else:
                rd = None
            if rd != None:
                if rd[0] == "F":
                    self.RegResSta.FU[rd] = 0
                elif rd[0] == "R":
                    self.RegResSta.RU[rd] = 0
            for j in range(self.awqueue[i]):
                rs = self.getrs(self.Ins.instruction[j])
                if rd in rs:
                    if self.InsSta.status[j][1] == 0:
                        Conflict = False
                        break
            if Conflict:
                self.wbQueue.append(self.awqueue.pop(i))
            else:
                i += 1
        for task in self.wbQueue:
            self.InsSta.status[task][2] = self.clock
        self.wbQueue.clear()

    def printResult(self):
        print("clock: ", self.clock)
        print("Instruction Status:      ", end='')
        print("Issue Exec WriteResult")
        indent = [-1, 0, 1, 0, 1] * 3
        for i in range(15):
            print(self.Ins.assembles[i], end='')
            print(' ' * (25 + indent[i] - len(self.Ins.assembles[i])), end='')
            for j in range(3):
                print(self.InsSta.status[i][j], end=' ' * 5)
            print()
        print("Reservation Stations:")
        print("Time Name    Busy  Op Vj Vk Qj Qk Imm")
        for i in range(9):
            print(self.RS.ResStation[i])
        print("Register result status:")
        print(self.RegResSta.FU)
        print(self.RegResSta.RU)
        print("-" * 80)


if __name__ == '__main__':
    tom = Tomasulo()

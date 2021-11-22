"""
本指令集参照MIPS设计
指令分为三种类型：载入与存储，运算，分支与跳转
载入与存储指令：
LW, SW
运算指令：
ADD, ADDI, SUB, AND, ANDI, OR, ORI, XOR, XORI, SLL, SRL, SLT
控制指令：
J

"""
memoryNum = 32
regNum = 32


# 主存类
class MEMORY:
    def __init__(self, memoryNum=32):
        self.size = memoryNum
        self.val = [i + 1 for i in range(self.size)]


# 通用寄存器类
class REGISTER:
    global val

    def __init__(self, regNum=32):
        self.size = regNum
        self.val = [0 for i in range(self.size)]


# 编译器类
class COMPILE:
    def __init__(self):
        self.error = 0

    def translation(self, assem):
        code = []
        for line in assem:
            line = line.split(' ')
            operand = line[1].split(',')
            if line[0] == 'LW':
                temp = '100011'
                temp += self.creatcode(5, 5, 16, operand, 2, 0, 1)
            elif line[0] == 'SW':
                temp = '101011'
                temp += self.creatcode(5, 5, 16, operand, 2, 0, 1)
            elif line[0] == 'ADD':
                temp = '000000'
                temp += self.creatcode(5, 5, 5, operand, 1, 2, 0)
                temp += '00000100000'
            elif line[0] == 'SUB':
                temp = '000000'
                temp += self.creatcode(5, 5, 5, operand, 1, 2, 0)
                temp += '00000100010'
            elif line[0] == 'AND':
                temp = '000000'
                temp += self.creatcode(5, 5, 5, operand, 1, 2, 0)
                temp += '00000100100'
            elif line[0] == 'OR':
                temp = '000000'
                temp += self.creatcode(5, 5, 5, operand, 1, 2, 0)
                temp += '00000100101'
            elif line[0] == 'XOR':
                temp = '000000'
                temp += self.creatcode(5, 5, 5, operand, 1, 2, 0)
                temp += '00000100110'
            elif line[0] == 'SLT':
                temp = '000000'
                temp += self.creatcode(5, 5, 5, operand, 1, 2, 0)
                temp += '00000101010'
            elif line[0] == 'ADDI':
                temp = '001000'
                temp += self.creatcode(5, 5, 16, operand, 1, 0, 2)
            elif line[0] == 'ANDI':
                temp = '001100'
                temp += self.creatcode(5, 5, 16, operand, 1, 0, 2)
            elif line[0] == 'ORI':
                temp = '001101'
                temp += self.creatcode(5, 5, 16, operand, 1, 0, 2)
            elif line[0] == 'XORI':
                temp = '001110'
                temp += self.creatcode(5, 5, 16, operand, 1, 0, 2)
            elif line[0] == 'SLL':
                temp = '111111'
                temp += self.creatcode(5, 5, 5, operand, 1, 0, 2)
                temp += '00000000000'
            elif line[0] == 'SRA':
                temp = '111111'
                temp += self.creatcode(5, 5, 5, operand, 1, 0, 2)
                temp += '00000000011'
            elif line[0] == 'J':
                temp = '000010'
                temp += format(int(operand[0][1:]), "b").zfill(26)
            else:
                print('Compile error!')
                self.error = 1
                return code
            code.append(temp)
        return code

    def creatcode(self, n1, n2, n3, operand, x1, x2, x3):
        temp = ''
        temp += format(int(operand[x1][1:]), "b").zfill(n1)
        temp += format(int(operand[x2][1:]), "b").zfill(n2)
        temp += format(int(operand[x3][1:]), "b").zfill(n3)
        return temp


# 运算器类
class ALU:
    def __init__(self):
        self.PC = 0

    def calculation(self, mcode):
        while (self.PC < len(mcode)):
            # LW指令
            if mcode[self.PC][0:6] == '100011':
                r1, r2, r3 = self.creatint(5, 5, 16, mcode)
                self.lw(r1, r2, r3)
            elif mcode[self.PC][0:6] == '101011':
                r1, r2, r3 = self.creatint(5, 5, 16, mcode)
                self.sw(r1, r2, r3)
            elif mcode[self.PC][0:6] == '000000':
                r1, r2, r3 = self.creatint(5, 5, 5, mcode)
                if mcode[self.PC][21:] == '00000100000':
                    self.add(r1, r2, r3)
                elif mcode[self.PC][21:] == '00000100010':
                    self.sub(r1, r2, r3)
                elif mcode[self.PC][21:] == '00000100100':
                    self.And(r1, r2, r3)
                elif mcode[self.PC][21:] == '00000100101':
                    self.Or(r1, r2, r3)
                elif mcode[self.PC][21:] == '00000100110':
                    self.Xor(r1, r2, r3)
                elif mcode[self.PC][21:] == '00000101010':
                    self.slt(r1, r2, r3)
            elif mcode[self.PC][0:6] == '001000':
                r1, r2, r3 = self.creatint(5, 5, 16, mcode)
                self.addi(r1, r2, r3)
            elif mcode[self.PC][0:6] == '001100':
                r1, r2, r3 = self.creatint(5, 5, 16, mcode)
                self.andi(r1, r2, r3)
            elif mcode[self.PC][0:6] == '001101':
                r1, r2, r3 = self.creatint(5, 5, 16, mcode)
                self.ori(r1, r2, r3)
            elif mcode[self.PC][0:6] == '001110':
                r1, r2, r3 = self.creatint(5, 5, 16, mcode)
                self.xori(r1, r2, r3)
            elif mcode[self.PC][0:6] == '111111':
                if mcode[self.PC][21:] == '00000000000':
                    r1, r2, r3 = self.creatint(5, 5, 5, mcode)
                    self.sll(r1, r2, r3)
                elif mcode[self.PC][21:] == '00000000011':
                    r1, r2, r3 = self.creatint(5, 5, 5, mcode)
                    self.sra(r1, r2, r3)
            elif mcode[self.PC][0:6] == '000010':
                r1 = int(mcode[self.PC][6:], base=2)
                del mcode[self.PC]
                self.PC += r1
                continue

            print('PC:', self.PC)
            print('assembler:', assembler[self.PC].replace('\n', ''))
            print('machinecode:', mcode[self.PC])
            print('memory:', memory.val)
            print('register:', cpu.reg.val)
            print('\n')
            self.PC += 1

    def creatint(self, n1, n2, n3, mcode):
        r1 = int(mcode[self.PC][6:n1 + 6], base=2)
        r2 = int(mcode[self.PC][n1 + 6:n1 + 6 + n2], base=2)
        r3 = int(mcode[self.PC][n1 + n2 + 6:n1 + n2 + n3 + 6], base=2)
        return r1, r2, r3

    def lw(self, r1, r2, r3):
        cpu.reg.val[r2] = memory.val[cpu.reg.val[r1] + r3]

    def sw(self, r1, r2, r3):
        memory.val[cpu.reg.val[r1] + r3] = cpu.reg.val[r2]

    def add(self, r1, r2, r3):
        cpu.reg.val[r3] = cpu.reg.val[r1] + cpu.reg.val[r2]

    def sub(self, r1, r2, r3):
        cpu.reg.val[r3] = cpu.reg.val[r1] - cpu.reg.val[r2]

    def And(self, r1, r2, r3):
        cpu.reg.val[r3] = cpu.reg.val[r1] & cpu.reg.val[r2]

    def Or(self, r1, r2, r3):
        cpu.reg.val[r3] = cpu.reg.val[r1] | cpu.reg.val[r2]

    def Xor(self, r1, r2, r3):
        cpu.reg.val[r3] = cpu.reg.val[r1] ^ cpu.reg.val[r2]

    def slt(self, r1, r2, r3):
        cpu.reg.val[r3] = 1 if cpu.reg.val[r1] < cpu.reg.val[r2] else 0

    def addi(self, r1, r2, r3):
        cpu.reg.val[r2] = cpu.reg.val[r1] + r3

    def andi(self, r1, r2, r3):
        cpu.reg.val[r2] = cpu.reg.val[r1] & r3

    def ori(self, r1, r2, r3):
        cpu.reg.val[r2] = cpu.reg.val[r1] | r3

    def xori(self, r1, r2, r3):
        cpu.reg.val[r2] = cpu.reg.val[r1] ^ r3

    def sll(self, r1, r2, r3):
        cpu.reg.val[r2] = cpu.reg.val[r1] << r3

    def sra(self, r1, r2, r3):
        cpu.reg.val[r2] = cpu.reg.val[r1] >> r3


# CPU类
class CPU:
    def __init__(self):
        self.reg = REGISTER(regNum)  # 实例化寄存器类，regNum寄存器个数
        self.alu = ALU()  # 实例化运算器类

    def run(self, mcode):
        self.alu.calculation(mcode)


if __name__ == "__main__":

    memory = MEMORY(memoryNum)
    # 从文件中读取汇编代码
    filename = input("please input source file:\n")
    assembler = []
    with open(filename) as source:
        lines = source.readlines()
        for line in lines:
            assembler.append(line)

    # 实例化编译器类
    compile = COMPILE()
    # 通过编译器将汇编语言转化为机器语言
    machinecode = compile.translation(assembler)
    if (compile.error == 0):
        # 将机器语言送入CPU执行
        # CPU中会实例化寄存器类、运算器类和控制器类
        cpu = CPU()
        cpu.run(machinecode)

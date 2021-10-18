"""
Memory:
32-bit address
8-bit cell
Register:
32 32-bit
Program:
Load r1,#0
Load r2,#1
Add r3,r1,r2
Store r3,#3
"""
memory = {'0b00000000000011110000000000000000': '0b10000111',
          '0b00000000000011110000000000000001': '0b00000010',
          '0b00000000000011110000000000000010': '0b00000000',
          '0b00000000000011110000000000000011': '0b00000000'}  # 32位地址寻址,初始化4byte
register = [0] * 32  # 32个32位寄存器，初始化为0,设定
register[31] = 0b00000000000011110000000000000000  # base寄存器，存放基址
opc = {
    'Add': '000000',
    'Load': '100011',
    'Store': '101011'
}  # static optcode
machine_code = []
program = ["Load r1,#0",
           "Load r2,#1",
           "Add r3,r1,r2",
           "Store r3,#3"]


def dec2bin(string_num, bit_wide):  # 十进制转化为长度位length的2进制数
    num = int(string_num)
    mid = []
    while True:
        if num == 0:
            break
        num, rem = divmod(num, 2)
        mid.append(rem)
    if len(mid) <= bit_wide:
        tmp = bit_wide - len(mid)
        for i in range(tmp):
            mid.append(0)
    else:
        er = IOError('Overflow!')
        raise er
    return ''.join([str(x) for x in mid[::-1]])


def parse_instructions(cmd):  # 解释器，将汇编指令转化为mips架构机器语言
    tmp = cmd.split(' ')
    code = opc[tmp[0]]
    if tmp[0] == 'Add':
        rd, rs, rt = tmp[1].strip('\n').split(',')
        code += dec2bin(rs[-1], 5)
        code += dec2bin(rt[-1], 5)
        code += dec2bin(rd[-1], 5)
        code += '00000100000'
    elif tmp[0] == 'Load':
        rt, offset = tmp[1].strip('\n').split(',')
        code += '11111'  # 加入base寄存器
        code += dec2bin(rt[-1], 5)
        code += dec2bin(offset[-1], 16)
    elif tmp[0] == 'Store':
        rt, offset = tmp[1].strip('\n').split(',')
        code += '11111'  # 加入base寄存器
        code += dec2bin(rt[-1], 5)
        code += dec2bin(offset[-1], 16)
    else:
        print("Unrecognized source code!")
    return code


def translation():  # 解释器
        for line in program:
            machine_code.append(parse_instructions(line))


def output_machine():
    print("mips machine code:")
    for it in machine_code:
        print(it)
    print()


def simulation():  # 模拟器
    for it in machine_code:
        optcode = it[0:6]

        if optcode in opc.values():
            tmp = list(opc.keys())[list(opc.values()).index(optcode)]
            if tmp == "Load":
                base = int(it[6:11], base=2)
                rt = int(it[11:16], base=2)
                offset = int(it[16:], base=2)
                load(base, rt, offset)
            elif tmp == "Add":
                rs = int(it[6:11], base=2)
                rt = int(it[11:16], base=2)
                rd = int(it[16:21], base=2)
                add(rs, rt, rd)
            elif tmp == "Store":
                base = int(it[6:11], base=2)
                rt = int(it[11:16], base=2)
                offset = int(it[16:], base=2)
                store(base, rt, offset)
            else:
                print("Unrecognized machine code!")


def add(rs, rt, rd):
    try:
        register[rd] = '0b' + str(dec2bin(int(register[rs], 2) + int(register[rt], 2), 8))
    except IOError as er:
        print(er)
        exit()
    print(register[rs], '+', register[rt], '=', register[rd])


def load(base, rt, offset):
    addr = '0b' + str(dec2bin(register[base] + offset, 32))
    register[rt] = memory[addr]


def store(base, rt, offset):
    addr = '0b' + str(dec2bin(register[base] + offset, 32))
    memory[addr] = register[rt]


if __name__ == "__main__":
    translation()
    output_machine()
    simulation()
    print(memory.values())

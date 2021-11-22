UnitIndex = {"Load1": 0, "Load2": 1, "Add3": 2, "Add4": 3, "Add5": 4, "Mult6": 5, "Mult7": 6, "Store8": 7,
                  "Store9": 8}
ResStation=[0]*10
print(list(UnitIndex.keys())[list(UnitIndex.values()).index(0)])
for i in range(9):
    ResStation[i]= 'Load1'
print(ResStation)
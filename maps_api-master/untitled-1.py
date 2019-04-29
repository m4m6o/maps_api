def func4():
    global w
    print(w)
    w = 20


w = 10
func4()    # 10
print(w)   # 20
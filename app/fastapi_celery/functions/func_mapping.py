import time

#function
def step_1(x: int):
    time.sleep(10)
    return int(x+1)

def step_2(x: int):
    time.sleep(5)
    return int(x+2)

def step_3(x: int):
    time.sleep(15)
    return int(x+3)

def step_4(x: int):
    time.sleep(10)
    return int(x+4)

def step_5(x: int):
    time.sleep(5)
    return int(x+5)

#mapping function
function_dict = {
    'step 1': step_1,
    'step 2': step_2,
    'step 3': step_3,
    'step 4': step_4,
    'step 5': step_5
}

#function exec
def step_exce(func, x):
    return func(x)

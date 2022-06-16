from algorithm import *
from vis import lamportvis, ravis
from absl import flags
from absl import app
import multiprocessing
import time
import os
from option import Options

node_pool = {}
args = Options().parse()

def Mutual_Exclusion():
    os.system("mkdir -p log")
    print("==================================================")
    print("************* Mutual Exclusion Demo **************")
    print("==================================================")

    print("Start Simulation!")
    print("Algorithm: ", args.algorithm)
    print("Node Number: ", args.node_num)
    print("Runtime: ", args.runtime)
    print("Begin Port: ", args.begin_port)
    timeQueue = multiprocessing.Queue()
    simulation_time = time.time()
    for i in range(args.node_num):
        if args.algorithm == "LA":
            node_pool[i] = LA(i, args.node_num, args.runtime,timeQueue, args.begin_port)
        elif args.algorithm == "RA":
            node_pool[i] = RA(i, args.node_num, args.runtime,timeQueue, args.begin_port)
        else:
            print("Not Implemented!!")
            return
        node_pool[i].start()
    
    for i in range(args.node_num):
        node_pool[i].join()
    acc_time = 0 
    simulation_time = (time.time()-simulation_time)*1000
    for _ in range(args.node_num):
        acc_time += timeQueue.get()
    acc_time =  acc_time/(args.node_num*args.runtime) * 1000
    print(f"Average request time is {acc_time} ms")
    print(f"Execution time is {simulation_time} ms")
    print("==================================================")
    print("************** Simulation Complete ***************")
    print("==================================================")
    if args.algorithm == "LA":
        lamportvis.visual_wrapper(args.node_num)
    elif args.algorithm == "RA":
        ravis.visual_wrapper(args.node_num)
    else:
        print("No corresponding Visualization")
        return

if __name__ == '__main__':
    Mutual_Exclusion()
    
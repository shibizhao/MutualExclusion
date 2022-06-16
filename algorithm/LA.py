from .Base import *
import time
import random
import queue
from copy import deepcopy

REQUEST = 1
REPLY = 2
RELEASE = 3
QUIT = 4

COLOR = ['\033[95m','\033[94m','\033[96m','\033[92m','\033[93m','\033[91m']
ENDC = '\033[0m'


class LA(Mutexmodel):
    def __init__(self, i, node_num, runtime, timeQueue, begin_port):
        Mutexmodel.__init__(self,i, node_num, runtime, begin_port)
        self.pq = queue.PriorityQueue()
        self.tag = COLOR[i%6]
        self.requestTime = 0
        self.timeQueue = timeQueue
        
    def run(self):
        serverSoc = self.openListenSocket("127.0.0.1", self.BP + self.id)
        clientSocs = self.openSendSockets()
        time.sleep(1)
        self.connSockets(clientSocs,serverSoc)
        conns = self.accSockets(serverSoc)
        quitNum = 0
        decideQuit = False
        requestNum  = 0
        
        while True:
            self.lamportClock += random.randint(50, 100) 
            newRequest = False
            
            if requestNum < self.runtime:
                newRequest = True #random.random() > 0.3
                if newRequest:
                    self.requestTime -= time.time()
                    self.request(clientSocs)
                    print(f"REQUEST is {self.id} {self.lamportClock}",self.pq.queue,file=self.fout)
                    print(f"{self.tag}******* {self.id} request for critical section @ {self.lamportClock} *******{ENDC}")
                    self.pq.put((deepcopy(self.lamportClock), self.id))
                    requestNum += 1
            
            replyNum = 0
            gotToken = False
            while not gotToken:
                for i in range(self.node_num):
                    if self.id == i:
                        continue

                    try:
                        conns[i].setblocking(0)
                        msg = conns[i].recv(25).decode() 
                    except Exception:
                        continue
                    
                    self.lamportClock += 1
                    info, node, clk = parseMsg(msg)
                    self.lamportClock = max(self.lamportClock, clk) + 1       
                    if info == REQUEST:
                        self.pq.put((clk,node))
                        assert node < len(clientSocs), f"msg = {info, node, clk}, len(client) = {len(clientSocs)}"
                        print(f"REPLY to {node}_{clk} {self.lamportClock}",self.pq.queue,file=self.fout)
                        self.reply(clientSocs[node],node)
                    elif info == REPLY:
                        print(f"REPLY from {node}_{clk} {self.lamportClock}",self.pq.queue,file=self.fout)
                        replyNum += 1
                    elif info == RELEASE:
                        (topClk, topNode) = self.pq.get()
                        print(f"RELEASE from {node}_{clk} {self.lamportClock}",self.pq.queue,file=self.fout)
                    elif info == QUIT:
                        quitNum += 1
                    else:
                        assert False, f"wrong msg {info}\n"

                    if newRequest and replyNum == self.node_num - 1:
                        (topClk, topNode) = self.pq.get()
                        self.pq.put((topClk,topNode))
                        if topNode == self.id:
                            gotToken = True
                            break
                if self.pq.empty():
                    break

            if newRequest:
                # enter CS 
                self.requestTime += time.time()
                self.lamportClock += 1
                print(f"ENTER by {self.id} {self.lamportClock}",self.pq.queue,file=self.fout)
                print(f"{self.tag}+++++++ {topNode} write in critical section @ {self.lamportClock} +++++++{ENDC}")
                globalfout = open("log/global_log.txt", "a")
                globalfout.write(f"******* {topNode} is writing critical section! *******\n")
                globalfout.close()
                
                # leave CS
                self.lamportClock += 1
                (topClk,topNode) = self.pq.get()
                print(f"RELEASE is {self.id} {self.lamportClock}",self.pq.queue,file=self.fout)

                self.release(clientSocs)
            
            if not decideQuit and requestNum >= self.runtime:
                decideQuit = True
                quitNum += 1
                self.lamportClock += 1
                print(f"QUIT on {self.id} {self.lamportClock}",self.pq.queue,file=self.fout)
                self.quit(clientSocs)
                
            if quitNum == self.node_num:
                break

        time.sleep(1)
        for i, clientSoc in enumerate(clientSocs):
            if i == self.id:
                continue
            clientSoc.close()
        serverSoc.close()
        self.fout.close()
        self.timeQueue.put(self.requestTime)
        
import socket
import multiprocessing

REQUEST = 1
REPLY = 2
RELEASE = 3
QUIT = 4


def mkMsg(info, node, clk):
    string = ":".join([str(info), str(node), str(clk)]) + ":"
    string += '0' * (25-len(string))
    return string.encode()

def parseMsg(msg):
    res = msg.split(":")
    return int(res[0]), int(res[1]), int(res[2])

class Mutexmodel(multiprocessing.Process):
    def __init__(self, i, node_num, runtime, begin_port):
        multiprocessing.Process.__init__(self)
        self.id = i
        self.node_num = node_num
        self.runtime = runtime
        self.lamportClock = 0
        self.BP = begin_port
        self.fout = open(f"log/{self.id}_log.txt","w")
    
    def openListenSocket(self, addr = "127.0.0.1", port=0):
        serverSoc = socket.socket()
        serverSoc.bind((addr, port))
        serverSoc.listen(self.node_num * 5)
        return serverSoc
    
    def openSendSockets(self):
        clientSocs = [socket.socket() if i != self.id else None for i in range(self.node_num)]
        return clientSocs
    
    def connSockets(self, socs, serverSoc):
        for i in range(self.node_num):
            if i == self.id:
                continue
            try:
                socs[i].connect(("127.0.0.1", i + self.BP))

            except Exception:
                for j in range(self.node_num):
                    if j == self.id:
                        continue
                    socs[j].close()
                serverSoc.close()
    
    def accSockets(self, serverSoc):
        conns = list()
        for i in range(self.node_num):
            if i == self.id:
                conns.append(None)
                continue
            conn, _ = serverSoc.accept()
            conn.setblocking(0)
            conns.append(conn)
        return conns

    def request(self, clientSocs):
        requestMsg = mkMsg(REQUEST, self.id, self.lamportClock)
        for i in range(self.node_num):
            if i == self.id:
                continue
            clientSocs[i].send(requestMsg)
        return

    def reply(self, clientSoc, node):
        replyMsg = mkMsg(REPLY, self.id, self.lamportClock)
        clientSoc.send(replyMsg)
        return
    
    def release(self, clientSocs):
        releaseMsg = mkMsg(RELEASE, self.id, self.lamportClock)
        for i in range(self.node_num):
            if i == self.id:
                continue
            clientSocs[i].send(releaseMsg)
        return
    
    def quit(self, clientSocs):
        quitMsg = mkMsg(QUIT, self.id, self.lamportClock)
        for i in range(self.node_num):
            if i == self.id:
                continue
            clientSocs[i].send(quitMsg)
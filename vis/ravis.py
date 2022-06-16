import cv2
import numpy as np
import os
from enum import Enum
import copy



class EventType(Enum):
    INIT    = 0
    REQUEST = 1
    REPLY   = 2
    RELEASE = 3
    ENTER   = 4
    QUIT    = 5
    PEND    = 6
    ERROR   = -1

class Event():
    def __init__(self, idx):
        self.id = idx
        self.pq = []
        self.time = 0
        self.type = []
        self.prev = []
        self.succ = []
        self.key = []
        self.status = True
        self.visit = False
        self.layer = 0
        self.pos   = None
    def set_type(self, t):
        self.type.append(t)
    # def add_succ(self, idx):
    #     self.succ.append(idx)
    def add_succ(self, key):
        if key in self.succ:
            return
        else:
            self.succ.append(key)


    # def add_prev(self, idx):
    #     self.prev.append(idx)
    def set_time(self, t):
        self.time = t
    def set_key(self, key):
        self.key = key
    def add_prev(self, key):
        if key in self.prev:
            return
        else:
            self.prev.append(key)
    def quit(self):
        self.status = False

class Controller():
    def __init__(self, proc_num):
        self.globalEventBuffer = []
        self.globalEventMap = {}
        self.proc_num = proc_num
        self.init()

    def init(self):
        self.globalEventBuffer = []
        self.globalEventBuffer = [[] for i in range(self.proc_num)]
        self.globalEventMap    = {}

    def ask_event_num(self, proc_id):
        return len(self.globalEventBuffer[proc_id])
    
    def add_event(self, event, proc_id, event_idx, key):
        assert(len(self.globalEventBuffer[proc_id]) == event_idx)
        self.globalEventBuffer[proc_id].append(event)
        assert(key not in self.globalEventMap.keys())
        self.globalEventMap[key] = (proc_id, event_idx)

    def gen_label(self, event):
        label = ""
        for i in event.type:
            label += str(i.name)[:3] + ", "
        label += str(event.time)
        return label

    def gen_succ(self):
        for i in range(self.proc_num):
            for j in self.globalEventBuffer[i]:
                ekey = j.key
                for k in j.prev:
                    t = self.globalEventMap[k]
                    self.globalEventBuffer[t[0]][t[1]].add_succ(ekey)
    
    def print_key(self, key):
        pt = copy.deepcopy(key)
        pt = "Node_" + pt
        # print(key, pt)
        return pt

    def visual_opencv(self, filename):
        self.gen_succ()
        code_str = "digraph G{\n"
        # print_node
        for i in range(self.proc_num):
            for j in range(len(self.globalEventBuffer[i])):
                code_str += self.print_key(str(self.globalEventBuffer[i][j].key))
                code_str += "[label=\""
                code_str += self.gen_label(self.globalEventBuffer[i][j])
                code_str += "\"];\n"
        # print_cluster
        for i in range(self.proc_num):
            e_num = len(self.globalEventBuffer[i])
            if e_num <= 0:
                continue
            code_str += "subgraph cluster_"+str(i) + " {\n"
            for j in range(e_num - 1):
                code_str += self.print_key(str(self.globalEventBuffer[i][j].key)) + " -> "
            code_str += self.print_key(str(self.globalEventBuffer[i][e_num-1].key)) +"[weight=1000];\n"
            code_str += "label = \"proc " + str(i) + "\";\n"
            code_str += "}\n"
        
        # print_edge
        for i in range(self.proc_num):
            for event in self.globalEventBuffer[i]:
                for prev in event.prev:
                    if self.globalEventMap[str(prev)][0] != i:      
                        code_str += self.print_key(str(prev)) + "->" + self.print_key(str(event.key)) + ";\n"
        
        # constraints
        # top-sort
        q = []
        max_layer_num = 0
        for i in range(self.proc_num):
            for j in range(len(self.globalEventBuffer[i])):  
                if len(self.globalEventBuffer[i][j].prev) == 0:
                    q.append(self.globalEventBuffer[i][j].key)
                    self.globalEventBuffer[i][j].layer = 0
        while len(q) > 0:
            top_key = q.pop(0)
            t = self.globalEventMap[top_key]
            top_proc_id = t[0]
            top_event_idx = t[1]
            self.globalEventBuffer[top_proc_id][top_event_idx].visit = True
            
            for succ in self.globalEventBuffer[top_proc_id][top_event_idx].succ:
                st = self.globalEventMap[succ]
                st_proc_id = st[0]
                st_event_idx = st[1]
                self.globalEventBuffer[st_proc_id][st_event_idx].layer = max(self.globalEventBuffer[st_proc_id][st_event_idx].layer, \
                                                                             self.globalEventBuffer[top_proc_id][top_event_idx].layer + 1)
                max_layer_num = max(max_layer_num, self.globalEventBuffer[st_proc_id][st_event_idx].layer)
                # check all of the prev of this succ
                status = True
                for prev in self.globalEventBuffer[st_proc_id][st_event_idx].prev:
                    pr = self.globalEventMap[prev]
                    pr_proc_id = pr[0]
                    pr_event_idx = pr[1]
                    if self.globalEventBuffer[pr_proc_id][pr_event_idx].visit == False:
                        status = False
                if status:
                    q.append(succ)
        
        layer_key = [[] for i in range(max_layer_num + 1)]
        for i in range(self.proc_num):
            for j in range(len(self.globalEventBuffer[i])):
                cur_layer = self.globalEventBuffer[i][j].layer
                layer_key[cur_layer].append(self.globalEventBuffer[i][j].key)
        
        # print(max_layer_num)

        for i in range(max_layer_num+1):
            if len(layer_key[i]) <= 1:
                continue
            code_str +=  "rank=same {"            
            for j in layer_key[i]:
                code_str += self.print_key(str(j)) + " "
            code_str += "}\n"
        code_str += "}\n"
        # print(code_str) 
        
        x_stride = 200
        y_stride = 120
        line_sx = x_stride * 3
        line_ex = x_stride * (max_layer_num + 8)
        line_sy = y_stride * 2
        # canvas definition
        canvas = np.ones((y_stride * (self.proc_num + 5), x_stride * (max_layer_num + 10), 3), dtype='uint8')
        canvas = canvas * 255
        # process line definition
        for i in range(self.proc_num):
            black = (0,0,0)
            cv2.line(canvas, (line_sx, y_stride * i + line_sy), (line_ex, y_stride * i + line_sy), black, thickness=2)
            cv2.putText(canvas, 'proc_' + str(i), (line_sx, i * y_stride + line_sy - y_stride // 4), cv2.FONT_HERSHEY_SIMPLEX, 0.75, black, thickness=2)
        
        # node definition
        for i in range(max_layer_num+1):
            for j in layer_key[i]:
                t = self.globalEventMap[j] 
                proc_id = t[0]
                event_idx = t[1]
                pos = (line_sx + (i+2) * x_stride + int(np.random.rand() * 40), y_stride * proc_id + line_sy)
                self.globalEventBuffer[proc_id][event_idx].pos = pos
                if event_idx > 0 and (self.globalEventBuffer[proc_id][event_idx].type[0] == EventType.ENTER):
                    cv2.circle(canvas, pos, 5, color=(255,0,0),thickness=5)
                elif event_idx > 0 and self.globalEventBuffer[proc_id][event_idx-1].type[0] == EventType.ENTER:
                    cv2.circle(canvas, pos, 5, color=(255,0,0),thickness=5)
                    cv2.line(canvas, self.globalEventBuffer[proc_id][event_idx-1].pos, pos, black, thickness=5)
                else:
                    cv2.circle(canvas, pos, 3, color=(0,0,255),thickness=3)
                cv2.putText(canvas, self.gen_label(self.globalEventBuffer[proc_id][event_idx]), \
                            (line_sx + (i+2) * x_stride - x_stride // 3, y_stride * proc_id + line_sy + (1 - 2 * (i%2)) * y_stride // 4), \
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, black, thickness=2)
        # message passing definition
        for i in range(self.proc_num):
            for j in self.globalEventBuffer[i]:
                cur_pos = j.pos
                prev = j.prev
                for p in prev:
                    t = self.globalEventMap[p]
                    prev_pos = self.globalEventBuffer[t[0]][t[1]].pos
                    cv2.arrowedLine(canvas, prev_pos, cur_pos, (0,0,0), thickness=1, tipLength=0.0125)
        # canvas saving
        cv2.imwrite(filename, canvas)
        return

    def visual_graphviz(self):
        self.gen_succ()
        from graphviz import Digraph
        g = Digraph(format="png", graph_attr={'splines': 'line'})
        # for i in range(self.proc_num):
        #     for j in self.globalEventBuffer[i]:
        #         g.node(str(j.key), label=self.gen_label(j))
        for i in range(self.proc_num):
            with g.subgraph(name='cluster_'+str(i), attr={'peripheries':'0'}) as c:
                # c.attr['peripheries'] = '0'
                # c.attr(style='filled', color='lightgrey')
                for j in self.globalEventBuffer[i]:
                    c.node(str(j.key), label=self.gen_label(j))
                edge_list = []
                for event in self.globalEventBuffer[i]:
                    for prev in event.prev:
                        print(prev, self.globalEventMap[str(prev)])
                        if self.globalEventMap[str(prev)][0] == i:
                            edge_list.append((str(prev), str(event.key)))
                c.edges(edge_list)
                c.attr(label='proc_'+str(i))
        for i in range(self.proc_num):
            for event in self.globalEventBuffer[i]:
                for prev in event.prev:
                    print(prev, self.globalEventMap[str(prev)])
                    if self.globalEventMap[str(prev)][0] != i:      
                        g.edge(str(prev), str(event.key))
        g.render(filename='test.png', directory="./")
        

def read_log(name, id, globalController):
    # global globalController
    with open(name, "r") as fp:
        content = fp.readlines()
        for line in content:
            if len(line) == 0:
                continue
            idx = line.find('[')
            basic_feature = line[0:idx].split(" ")
            infor_queue   = line[idx:]
            cur_time = int(basic_feature[3])
            cur_key  = str(id) + "_" + str(cur_time)
            event_idx = globalController.ask_event_num(id)

            if cur_key in globalController.globalEventMap.keys():
                t = globalController.globalEventMap[cur_key]
                p_id = t[0]
                e_idx = t[1]
                assert EventType[basic_feature[0]] == EventType.REPLY 
                assert globalController.globalEventBuffer[p_id][e_idx-1].type[0] == EventType.ENTER

                # these reply to can be add prev by the dst
                continue
            else:
                new_event = Event(id)
                new_event.set_type(EventType[basic_feature[0]])
                new_event.set_time(cur_time)
                new_event.set_key(cur_key)
                
                status = True
                if event_idx != 0:
                    prev_key = globalController.globalEventBuffer[id][event_idx - 1].key
                    new_event.add_prev(prev_key)
                    if globalController.globalEventBuffer[id][event_idx - 1].type[0] == EventType.ENTER:
                        status = False
                
                if basic_feature[1] == "from" or basic_feature[1] == "reply":
                    prev_key = basic_feature[2]
                    new_event.add_prev(prev_key)
                if status and basic_feature[1] == "to":
                    prev_key = basic_feature[2]
                    new_event.add_prev(prev_key)
                
                globalController.add_event(new_event, id, event_idx, cur_key)
            

def visual_wrapper(proc_num, filename="ra_visual.png"):
    globalController = Controller(proc_num=proc_num)
    for i in range(proc_num):
        read_log("./log/" + str(i) + "_log.txt", i, globalController)
    globalController.visual_opencv(filename)

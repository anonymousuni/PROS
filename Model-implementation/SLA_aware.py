import json
import math
import operator
import igraph as ig
import louvain
import networkx as nx
import matplotlib.pyplot as plt

import App_placement
import louvain_ext
import random
import numpy as np
from SLAassessment import SLACalculation
from Similaritymeasurment import SLA_Sim_graph
from TSLA import TSLA_cal

CLOUDRAM = 32
CLOUDSTORAGE = 99999999999999
CLOUDSPEED = 100000  # INSTR x MS
CLOUD_CPU_CACHE = 99999999
CLOUD_UP_BANDWITDH = 5000  # BYTES / MS --> 40 Mbits/s
CLOUD_DOWN_BANDWITDH = 5000  # MS
CLOUDBW = 5000
CLOUDPR = 125

# NETWORK
PERCENTATGEOFGATEWAYS = 0.25
func_PROPAGATIONTIME = "random.randint(1,7)"  # MS
func_BANDWITDH = "random.randint(30000,110000)"  # BYTES / MS
func_NETWORKGENERATION = "nx.barabasi_albert_graph(n=200, m=1)"  # algorithm for the generation of the network topology
func_NODERAM = "random.randint(2,16)"  # MB RAM #random distribution for the resources of the fog devices
func_NODESTORAGE = "random.randint(64,256)"  # random distribution for the resources of the fog devices
func_CPU_Core = "random.randint(2,8)"
func_NODESPEED = "random.randint(10000,40000)"  # INTS / MS #random distribution for the speed of the fog devices

# APP and SERVICES
TOTALNUMBEROFAPPS =10
func_APPGENERATION = "nx.gn_graph(random.randint(2,10))"
func_SERVICEINSTR = "random.randint(100,500)"  # INSTR --> taking into account node speed this gives us between 200 and 600 MS
func_SERVICEMESSAGESIZE = "random.randint(1500000,4500000)"  # BYTES and taking into account net bandwidth it gives us between 20 and 60 MS
func_SERVICERAM = "random.randint(1,7)"  # MB of RAM consumed by the service, taking into account noderesources and appgeneration we have to fit approx 1 app per node or about 10 services
func_STORAGE = "random.randint(1,7)"
#func_APPDEADLINE = "random.randint(50,2000)"  # MS

# USERS and IoT DEVICES
func_REQUESTPROB = "random.random()/8"  # Popularidad de la app. threshold que determina la probabilidad de que un dispositivo tenga asociado peticiones a una app. tle threshold es para cada ap
func_USERREQRAT = "random.randint(10,100)"  # MS
pathSimple = "./Realexpriment/medium/"

# SLA parameters
func_AcceptPar = "random.randint(0,1800)"
func_AcceptPar1 = "random.randint(1100,1800)"
#func_vioAcceptance = "random.randint(0,180)"
func_vioAcceptance = 1800
func_vioSuccessPar="random.randint(0,1800)"
func_vioSuccessPar1="random.randint(1100,1800)"
# fun_SuccessPar="random.randint(1,30)"
# fun_SatiPar="random.randint(1,30)"
random.seed(8)
verbose_log = False
ILPoptimization = True
generatePlots = True
graphicTerminal = True

devices = list()
devices1 = list()
nodeRAM = {}
CPUCore = {}
nodeSTORAGE = {}
SumRAM = 0.0
SumStorage = 0.0
SumCore = 0.0
cloudId = 1000
nodeFreeResources = {}
nodeSpeed = {}
nodelat = {}
nodelong = {}
mylabels = {}


# initializing the Network

devices = list()
devices1 = list()
Device_ifo=[{'id': 0, 'name':"CityA", 'IPT': 14000, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 14000}, 'network': {'up_Bw': 140, 'down_Bw': 140, 'Latency':23}, 'storage': 10,'RAM': 8},
            {'id': 1, 'name':"CityAM",'IPT': 7200, 'cpu': {'core_num': 2, 'cache': 4, 'speed': 7200},'network': {'up_Bw': 220, 'down_Bw': 220, 'Latency':7}, 'storage': 10, 'RAM': 4},
            {'id': 2, 'name':"CityAS",'IPT': 7100, 'cpu': {'core_num': 2, 'cache': 4, 'speed': 7100}, 'network': {'up_Bw': 220, 'down_Bw': 220, 'Latency':7}, 'storage': 10,'RAM': 2},
            {'id': 3, 'name':"CityB", 'IPT': 14000, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 14000}, 'network': {'up_Bw': 140, 'down_Bw': 140, 'Latency':23}, 'storage': 10,'RAM': 8},
            {'id': 4, 'name':"CityC", 'IPT': 14000, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 14000}, 'network': {'up_Bw': 140, 'down_Bw': 140, 'Latency':23}, 'storage': 10,'RAM': 8},
            {'id': 5,'name':"CityD", 'IPT': 12000, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 12000}, 'network': {'up_Bw': 220, 'down_Bw': 220, 'Latency':12}, 'storage': 10,'RAM': 8},
            {'id': 6,'name':"CityEL", 'IPT': 58000, 'cpu': {'core_num': 12, 'cache': 4, 'speed': 58000}, 'network': {'up_Bw': 940, 'down_Bw': 940, 'Latency':2}, 'storage': 32,'RAM': 32},
            {'id': 7,'name':"CityEM", 'IPT': 21700, 'cpu': {'core_num': 8, 'cache': 4, 'speed': 21700}, 'network': {'up_Bw': 920, 'down_Bw': 920, 'Latency':2}, 'storage': 32,'RAM': 16},
            {'id': 8,'name':"Jetson", 'IPT': 4080, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 4080}, 'network': {'up_Bw': 840, 'down_Bw': 840, 'Latency':2}, 'storage': 64,'RAM': 4},
            {'id': 9,'name':"RPi4", 'IPT': 5100, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 5100}, 'network': {'up_Bw': 800, 'down_Bw': 800, 'Latency':2}, 'storage': 64,'RAM': 4},
            {'id': 10,'name':"CityF", 'IPT': 14000, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 14000}, 'network': {'up_Bw': 140, 'down_Bw': 140, 'Latency':23}, 'storage': 10,'RAM': 8}]
cloud_info=  [{'id': 1,'name':"CityF", 'IPT': 14000, 'cpu': {'core_num': 4, 'cache': 4, 'speed': 14000}, 'network': {'up_Bw': 140, 'down_Bw': 140, 'Latency':23}, 'storage': 10,'RAM': 8}]

res_num=[{'id': 0, 'num':10},{'id': 1, 'num':10},{'id': 2, 'num':10},{'id': 3, 'num':10},{'id': 4, 'num':10},{'id': 5, 'num':10},{'id': 6, 'num':10},{'id': 7, 'num':10},{'id': 8, 'num':10},{'id': 9, 'num':10}, {'id': 10, 'num':20}]



netMatrix= [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9),(0, 10),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9),(1, 10),
            (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9),(2, 10),
            (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9),(3, 10),
            (4, 5), (4, 6), (4, 7), (4, 8), (4, 9),(4, 10),
            (5, 6), (5, 7), (5, 8), (5, 9),(5, 10),
            (6, 7), (6, 8), (6, 9),(6, 10),
            (7, 8), (7, 9),(7, 10),
            (8, 9),(8, 10),
            (9, 10)]
net_info=[[{'sourceID':0,'desID':1, 'S_name':"CityAM", 'D_name':"CityAS", 'bandwidth':13000, 'latency': 0.5}, {'sourceID':0,'desID':2, 'S_name':"CityAM", 'D_name':"CityAS", 'bandwidth':13000, 'latency': 0.5},{'sourceID':0,'desID':3, 'S_name':"CityAM", 'D_name':"CityB", 'bandwidth':1950, 'latency': 12.5},{'sourceID':0,'desID':4, 'S_name':"CityAM", 'D_name':"CityC", 'bandwidth':3000, 'latency': 7.3},{'sourceID':0,'desID':5, 'S_name':"CityAM", 'D_name':"CityD", 'bandwidth':5000, 'latency': 4.8}, {'sourceID':0,'desID':6, 'S_name':"CityAM", 'D_name':"CityEL", 'bandwidth':950, 'latency': 7.2}, {'sourceID':0,'desID':7, 'S_name':"CityAM", 'D_name':"CityEM", 'bandwidth':900, 'latency': 7.2}, {'sourceID':0,'desID':8, 'S_name':"CityAM", 'D_name':"Jetson", 'bandwidth':900, 'latency': 7.5}, {'sourceID':0,'desID':9, 'S_name':"CityAM", 'D_name':"RPi4", 'bandwidth':900, 'latency': 7.5}, {'sourceID':0,'desID':10, 'D_name':"CityF", 'S_name':"CityAM", 'bandwidth':1500, 'latency': 15}],
                                                                                                                      [{'sourceID':1,'desID':2, 'S_name':"CityAS", 'D_name':"CityAS", 'bandwidth':13000, 'latency': 0.5},{'sourceID':1,'desID':3, 'S_name':"CityAS", 'D_name':"CityB", 'bandwidth':1950, 'latency': 12.5},{'sourceID':1,'desID':4, 'S_name':"CityAS", 'D_name':"CityC", 'bandwidth':3000, 'latency': 7.3},{'sourceID':1,'desID':5, 'S_name':"CityAS", 'D_name':"CityD", 'bandwidth':5000, 'latency': 4.8}, {'sourceID':1,'desID':6, 'S_name':"CityAS", 'D_name':"CityEL", 'bandwidth':950, 'latency': 7.2}, {'sourceID':1,'desID':7, 'S_name':"CityAS", 'D_name':"CityEM", 'bandwidth':900, 'latency': 7.2}, {'sourceID':1,'desID':8, 'S_name':"CityAS", 'D_name':"Jetson", 'bandwidth':900, 'latency': 7.5}, {'sourceID':1,'desID':9, 'S_name':"CityAS", 'D_name':"RPi4", 'bandwidth':900, 'latency': 7.5}, {'sourceID':1,'desID':10, 'D_name':"CityF", 'S_name':"CityAM", 'bandwidth':1500, 'latency': 15}],
                                                                                                                                                                                                                               [{'sourceID':2,'desID':3, 'S_name':"CityAS", 'D_name':"CityB", 'bandwidth':1950, 'latency': 12.5}, {'sourceID':2,'desID':4, 'S_name':"CityAS", 'D_name':"CityC", 'bandwidth':3000, 'latency': 7.3}, {'sourceID':2,'desID':5, 'S_name':"CityAS", 'D_name':"CityD", 'bandwidth':5000, 'latency': 4.8}, {'sourceID':2,'desID':6, 'S_name':"CityAS", 'D_name':"CityEL", 'bandwidth':950, 'latency': 7.2}, {'sourceID':2,'desID':7, 'S_name':"CityAS", 'D_name':"CityEM", 'bandwidth':900, 'latency': 7.2}, {'sourceID':2,'desID':8, 'S_name':"CityAS", 'D_name':"Jetson", 'bandwidth':900, 'latency': 7.5}, {'sourceID':2,'desID':9, 'S_name':"CityAS", 'D_name':"RPi4", 'bandwidth':900, 'latency': 7.5}, {'sourceID':0,'desID':10, 'D_name':"CityF", 'S_name':"CityAS", 'bandwidth':1500, 'latency': 15}],

[{'sourceID':3,'desID':4, 'S_name':"CityB", 'D_name':"CityC", 'bandwidth':3200, 'latency': 6.7},  {'sourceID':3,'desID':5, 'S_name':"CityB", 'D_name':"CityD", 'bandwidth':1400, 'latency': 16.6}, {'sourceID':3,'desID':6, 'S_name':"CityB", 'D_name':"CityEL", 'bandwidth':900, 'latency': 23.2}, {'sourceID':3,'desID':7, 'S_name':"CityB", 'D_name':"CityEM", 'bandwidth':850, 'latency': 23.6}, {'sourceID':3,'desID':8, 'S_name':"CityB", 'D_name':"Jetson", 'bandwidth':700, 'latency': 23.2}, {'sourceID':3,'desID':9, 'S_name':"CityB", 'D_name':"RPi4", 'bandwidth':770, 'latency': 23.6}, {'sourceID':3,'desID':10, 'D_name':"CityF", 'S_name':"CityB", 'bandwidth':900, 'latency': 25.9}],

[{'sourceID':4,'desID':5, 'S_name':"CityC", 'D_name':"CityD", 'bandwidth':2100, 'latency': 11.5}, {'sourceID':4,'desID':6, 'S_name':"CityC", 'D_name':"CityEL", 'bandwidth':930, 'latency': 12.2}, {'sourceID':4,'desID':7, 'S_name':"CityC", 'D_name':"CityEM", 'bandwidth':900, 'latency': 12.5}, {'sourceID':4,'desID':8, 'S_name':"CityC", 'D_name':"Jetson", 'bandwidth':900, 'latency': 12.6}, {'sourceID':4,'desID':9, 'S_name':"CityC", 'D_name':"RPi4", 'bandwidth':850, 'latency': 12.6},{'sourceID':4,'desID':10, 'D_name':"CityF", 'S_name':"CityC", 'bandwidth':1100, 'latency': 21}],

[{'sourceID':5,'desID':6, 'S_name':"CityD", 'D_name':"CityEL", 'bandwidth':930, 'latency': 11.4}, {'sourceID':5,'desID':7, 'S_name':"CityD", 'D_name':"CityEM", 'bandwidth':860, 'latency': 11.5}, {'sourceID':5,'desID':8, 'S_name':"CityD", 'D_name':"Jetson", 'bandwidth':840, 'latency': 12}, {'sourceID':5,'desID':9, 'S_name':"CityD", 'D_name':"RPi4", 'bandwidth':850, 'latency': 11.5},{'sourceID':5,'desID':10, 'S_name':"CityD", 'D_name':"CityF", 'bandwidth':1200, 'latency': 10}],
[{'sourceID':6,'desID':7, 'S_name':"CityEL", 'D_name':"CityEM", 'bandwidth':930, 'latency': 0.5}, {'sourceID':6,'desID':8, 'S_name':"CityEL", 'D_name':"Jetson", 'bandwidth':930, 'latency': 0.5}, {'sourceID':6,'desID':9, 'S_name':"CityEL", 'D_name':"RPi4", 'bandwidth':850, 'latency': 0.5},{'sourceID':6,'desID':10, 'S_name':"CityF", 'D_name':"CityEL", 'bandwidth':920, 'latency': 22.4}],
[{'sourceID':7,'desID':8, 'S_name':"CityEM", 'D_name':"Jetson", 'bandwidth':920, 'latency': 0.5}, {'sourceID':7,'desID':9, 'S_name':"CityEM", 'D_name':"RPi4", 'bandwidth':850, 'latency': 0.5}, {'sourceID':7,'desID':10, 'D_name':"CityF", 'S_name':"CityEM", 'bandwidth':900, 'latency': 22.8}],
[{'sourceID':8,'desID':9, 'S_name':"Jetson", 'D_name':"RPi4", 'bandwidth':920, 'latency': 0.5}, {'sourceID':8,'desID':10, 'D_name':"CityF", 'S_name':"Jetson", 'bandwidth':900, 'latency': 22.8}],
[{'sourceID':9,'desID':10, 'D_name':"CityF", 'S_name':"RPi4", 'bandwidth':850, 'latency': 22.6}]]

net_cloud_info=[{'sourceID':1,'desID':0, 'D_name':"CityAM", 'S_name':"CityF", 'bandwidth':1500, 'latency': 15},  {'sourceID':1,'desID':1, 'D_name':"CityAS", 'S_name':"CityF", 'bandwidth':1500, 'latency': 15}, {'sourceID':1,'desID':2, 'D_name':"CityAS", 'S_name':"CityF", 'bandwidth':1500, 'latency': 15}, {'sourceID':1,'desID':3, 'D_name':"CityB", 'S_name':"CityF", 'bandwidth':900, 'latency': 25.9},{'sourceID':1,'desID':4, 'D_name':"CityC", 'S_name':"CityF", 'bandwidth':1100, 'latency': 21},
                 {'sourceID':1,'desID':5, 'S_name':"CityF", 'D_name':"CityD", 'bandwidth':1200, 'latency': 10}, {'sourceID':1,'desID':6, 'S_name':"CityF", 'D_name':"CityEL", 'bandwidth':920, 'latency': 22.4}, {'sourceID':1,'desID':7, 'S_name':"CityF", 'D_name':"CityEM", 'bandwidth':900, 'latency': 22.8}, {'sourceID':1,'desID':8, 'S_name':"CityF", 'D_name':"Jetson", 'bandwidth':900, 'latency': 22.8}, {'sourceID':1,'desID':9, 'S_name':"CityF", 'D_name':"RPi4", 'bandwidth':850, 'latency': 22.6},  {'sourceID':1,'desID':10, 'S_name':"CityF", 'D_name':"CityF", 'bandwidth':12000, 'latency': 0.5}]

net_info1=[{'sourceID':0,'desID':0, 'S_name':"CityA", 'D_name':"CityAS", 'bandwidth':13000, 'latency': 0.5},
           {'sourceID':1,'desID':1, 'S_name':"CityAM", 'D_name':"CityAS", 'bandwidth':13000, 'latency': 0.5},
           {'sourceID':2,'desID':2, 'S_name':"CityAS", 'D_name':"CityAS", 'bandwidth':13000, 'latency': 0.5},
           {'sourceID':3,'desID':3, 'S_name':"CityB", 'D_name':"CityB", 'bandwidth':12000, 'latency': 0.5},
           {'sourceID':4,'desID':4, 'S_name':"CityC", 'D_name':"CityC", 'bandwidth':12000, 'latency': 0.5},
           {'sourceID':5,'desID':5, 'S_name':"CityD", 'D_name':"CityD", 'bandwidth':12000, 'latency': 0.5},
           {'sourceID':6,'desID':6, 'S_name':"Large", 'D_name':"Large", 'bandwidth':930, 'latency': 0.5},
           {'sourceID':7,'desID':7, 'S_name':"Medium", 'D_name':"Medium", 'bandwidth':860, 'latency': 0.5},
           {'sourceID':8,'desID':8, 'S_name':"Jetson", 'D_name':"Jetson", 'bandwidth':920, 'latency': 0.5},
           {'sourceID':9,'desID':9, 'S_name':"RPi4", 'D_name':"RPi4", 'bandwidth':850, 'latency': 0.5},
           {'sourceID':10,'desID':10, 'S_name':"CityF", 'D_name':"CityF", 'bandwidth':12000, 'latency': 0.5}]
def network_initiat():
    PERCENTATGEOFGATEWAYS = 0.25
    mylabels = {}
    nodeRAM = {}
    CPUCore = {}
    nodeSTORAGE = {}
    nodeFreeResources = {}
    node_Up_BW = {}
    node_Dwon_BW = {}
    nodeSpeed = {}
    SumRAM = 0.0
    SumStorage = 0.0
    SumCore = 0.0
    myCityDs = list()
    nodeID = {}
    Flag = {}
    num = 0
    centralityValuesNoOrdered = 0
    gatewaysDevices = []
    cloudgatewaysDevices = set()


    for i in range(len(Device_ifo)):
        if Device_ifo[i]['id'] == 0:
            for j in range(num, res_num[0]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                nodeID[j] = Device_ifo[i]['id']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
            print("device type:", Device_ifo[i]['id'])
            num = res_num[0]['num']
        elif Device_ifo[i]['id'] == 1:
            for j in range(num, num + res_num[1]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[1]['num']
        elif Device_ifo[i]['id'] == 2:
            for j in range(num, num + res_num[2]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[2]['num']

        elif Device_ifo[i]['id'] == 3:
            for j in range(num, num + res_num[3]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[3]['num']

        elif Device_ifo[i]['id'] == 4:
            for j in range(num, num + res_num[4]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[4]['num']

        elif Device_ifo[i]['id'] == 5:
            for j in range(num, num + res_num[5]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[5]['num']

        elif Device_ifo[i]['id'] == 6:
            for j in range(num, num + res_num[6]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
                if j>66:
                    gatewaysDevices.append(j)
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[6]['num']

        elif Device_ifo[i]['id'] == 7:
            for j in range(num, num + res_num[7]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
                if j>76:
                    gatewaysDevices.append(j)
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[7]['num']

        elif Device_ifo[i]['id'] == 8:
            for j in range(num, num + res_num[8]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
                if j > 86:
                    gatewaysDevices.append(j)

            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[8]['num']

        elif Device_ifo[i]['id'] == 9:
            for j in range(num, num + res_num[9]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[9]['num']
        elif Device_ifo[i]['id'] == 10:
            for j in range(num, num + res_num[10]['num']):
                nodeRAM[j] = Device_ifo[i]['RAM']
                CPUCore[j] = Device_ifo[i]['cpu']['core_num']
                nodeSpeed[j] = Device_ifo[i]['cpu']['speed']
                nodeSTORAGE[j] = Device_ifo[i]['storage']
                SumRAM = SumRAM + nodeRAM[j]
                SumStorage = SumStorage + nodeSTORAGE[j]
                SumCore = SumCore + CPUCore[j]
                Flag[j] = False
                nodeID[j] = Device_ifo[i]['id']
            print("device type:", Device_ifo[i]['id'])
            num = num + res_num[10]['num']
    print("The number of Fog devices:", num)
    netJson = {}

    for i in range(0, num):
        myNode = {'id': i, 'IPT': nodeSpeed[i], 'cpu': {'core_num': CPUCore[i], 'cache': 4, 'speed': nodeSpeed[i]},
                  'storage': nodeSTORAGE[i], 'RAM': nodeRAM[i]}

        devices.append(myNode)

    for i in range(0, num):
        myNode1 = {}
        myNode1['id'] = i
        myNode1['RAM'] = nodeRAM[i]
        myNode1['IPT'] = nodeSpeed[i]
        myNode1['core'] = CPUCore[i]
        myNode1['storage'] = nodeSTORAGE[i]
        devices1.append(myNode1)
    netMatrix1=[]
    all_CityD=[]
    for i in range(0, num):
        CityDs = []
        for j in range(i, num):
            if i == j:
                pass
            else:
                #myLink = {}
                #myLink['s'] = i
                #myLink['d'] = j
                #print(nodeID[i], nodeID[j])
                netMatrix1.append((i, j))
                if nodeID[i] == nodeID[j]:
                    myLink = {}
                    myLink['s'] = i
                    myLink['d'] = j
                    myLink['PR'] = net_info1[nodeID[i]]['latency']
                    myLink['BW'] = net_info1[nodeID[i]]['bandwidth']
                    myCityDs.append(myLink)
                    CityDs.append(myLink)
                else:
                    if j == num:
                        pass
                    else:
                        myLink = {}
                        myLink['s'] = i
                        myLink['d'] = j
                        myLink['PR'] = net_info[nodeID[i]][nodeID[j] - (nodeID[i] + 1)]['latency']
                        myLink['BW'] = net_info[nodeID[i]][nodeID[j] - (nodeID[i] + 1)]['bandwidth']
                        #print(i, j)
                        myCityDs.append(myLink)
                        CityDs.append(myLink)
        all_CityD.append(CityDs)


    print("netMatrix1", netMatrix1)
    #print("MyLink:", all_CityD)
    G = nx.Graph()
    G.add_CityDs_from(netMatrix1)
    for n in range(0, len(G.nodes)):
        mylabels[n] = str(n)

    for e in G.CityDs:
        i = 1
        #print("CityD source and distination:", e[0], " -> ", e[1])
        G[e[0]][e[1]]['PR'] = all_CityD[e[0]][e[1] - (i + e[0])]['PR']
        #print("The graph link latency", G[e[0]][e[1]]['PR'])
        G[e[0]][e[1]]['BW'] = all_CityD[e[0]][e[1] - (i + e[0])]['BW']
        #print("The graph link bandwidth", G[e[0]][e[1]]['BW'])
        G[e[0]][e[1]]['weight'] = 1 / (float(G[e[0]][e[1]]['PR']))
        #print("The graph weigths", G[e[0]][e[1]]['weight'])
        i = i + 2

    cloudId = 1000
    myNode = {'id': cloudId, 'cpu': {'core_num': cloud_info[0]['cpu']['core_num'], 'cache': CLOUD_CPU_CACHE, 'speed': cloud_info[0]['cpu']['speed']},
              'storage': cloud_info[0]['storage'],'RAM': cloud_info[0]['RAM']}
    devices.append(myNode)

    myNode1 = {}
    myNode1['id'] = cloudId
    myNode1['RAM'] = cloud_info[0]['RAM']
    myNode1['IPT'] = cloud_info[0]['cpu']['speed']
    devices1.append(myNode1)

    print("This is node in the graph: ",G.nodes)
    for i in G.nodes:
        myLink = {}
        if i<res_num[0]['num']:
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[0]['latency']
            myLink['BW'] = net_cloud_info[0]['bandwidth']
            #print("The resource type 0")
        elif i<(res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[1]['latency']
            myLink['BW'] = net_cloud_info[1]['bandwidth']
            #print("The resource type 1")
        elif i < (res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[2]['latency']
            myLink['BW'] = net_cloud_info[2]['bandwidth']
            #print("The resource type 2")
        elif i < (res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[3]['latency']
            myLink['BW'] = net_cloud_info[3]['bandwidth']
            #print("The resource type 3")
        elif i < (res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[4]['latency']
            myLink['BW'] = net_cloud_info[4]['bandwidth']
            #print("The resource type 4")
        elif i < (res_num[5]['num']+res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[5]['latency']
            myLink['BW'] = net_cloud_info[5]['bandwidth']
            #print("The resource type 5")
        elif i < (res_num[6]['num']+res_num[5]['num']+res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[6]['latency']
            myLink['BW'] = net_cloud_info[6]['bandwidth']
            #print("The resource type 6")
        elif i < (res_num[7]['num']+res_num[6]['num']+res_num[5]['num']+res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[7]['latency']
            myLink['BW'] = net_cloud_info[7]['bandwidth']
            #print("The resource type 7")
        elif i < (res_num[8]['num']+res_num[7]['num']+res_num[6]['num']+res_num[5]['num']+res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[8]['latency']
            myLink['BW'] = net_cloud_info[8]['bandwidth']
            #print("The resource type 8")
        elif i < (res_num[9]['num']+res_num[8]['num']+res_num[7]['num']+res_num[6]['num']+res_num[5]['num']+res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[9]['latency']
            myLink['BW'] = net_cloud_info[9]['bandwidth']
            #print("The resource type 9")
        elif i < (res_num[10]['num'] +res_num[9]['num'] + res_num[8]['num'] + res_num[7]['num'] + res_num[6]['num'] + res_num[5]['num'] +
                  res_num[4]['num'] + res_num[3]['num'] + res_num[2]['num'] + res_num[1]['num'] + res_num[0]['num']):
            myLink['s'] = i
            myLink['d'] = cloudId
            myLink['PR'] = net_cloud_info[10]['latency']
            myLink['BW'] = net_cloud_info[10]['bandwidth']
        else:
            print("The resource number:", i)
        myCityDs.append(myLink)
    print("The number of devices in the network:", (res_num[9]['num']+res_num[8]['num']+res_num[7]['num']+res_num[6]['num']+res_num[5]['num']+res_num[4]['num']+res_num[3]['num']+res_num[2]['num']+res_num[1]['num']+res_num[0]['num']))
    netJson['entity'] = devices1
    netJson['link'] = myCityDs
    file = open("networkDefinition1.json", "w")
    file.write(json.dumps(netJson))
    file.close()
    initial_len = len(G.nodes)
    initGraph = G.copy()

    return G, initGraph, initial_len, centralityValuesNoOrdered, gatewaysDevices, SumRAM, SumStorage, SumCore, nodeSpeed, nodeRAM, CPUCore, nodeSTORAGE

def network_update_del(G, del_nodes, SumRAM, SumStorage, SumCore, devices):
    mylabels = {}
    print("The number of devices befor deleting nodes:  ", len(devices))

    for i in range(len(del_nodes)):
        G.remove_node(del_nodes[i])
        for j in range(len(devices)):
            if devices[j]['id'] == del_nodes[i]:
                devices.pop(j)
                print("the node (", del_nodes[i], ") was deleted from the network")
                devices1.pop(j)
                SumRAM = SumRAM - devices[j]['RAM']
                SumStorage = SumStorage - devices[j]['storage']
                SumCore = SumCore - devices[j]['cpu']['core_num']
                break
        # SumRAM = SumRAM - nodeRAM0[del_nodes[i]]
        # SumStorage = SumStorage - nodeSTORAGE0[del_nodes[i]]
        # SumCore = SumCore - CPUCore0[del_nodes[i]]
    for n in range(0, len(G.nodes)):
        mylabels[n] = str(n)
    mapping = dict(zip(G, range(len(mylabels))))
    G = nx.relabel_nodes(G, mapping)
    print("The number of devices after deleting nodes:  ", len(devices))
    weightNetwork1(G)
    return G, devices, SumRAM, SumStorage, SumCore


def NETWORKGENERATION(G):
    topology_matrix = nx.to_numpy_matrix(G)
    # print(len(G.nodes))
    return topology_matrix


def GraphGeneration(topo_matrix):
    graph = nx.from_numpy_matrix(topo_matrix)
    return graph


def get_devices():
    return devices


def network_update_add(G, initial_len, tt, newnodes, SumRAM, SumStorage, SumCore, devices):
    PERCENTATGEOFGATEWAYS = 0.25
    gatewaysDevices = set()
    cloudgatewaysDevices = set()
    mylabels = {}
    nodeRAM = {}
    CPUCore = {}
    nodeSpeed = {}
    nodeSTORAGE = {}
    myCityDs = list()
    isolated_Devices = []
    n = len(G.nodes)
    # print("the number of fog devices before adding new devices:  ", len(devices))
    newsize = n + newnodes
    centralityValuesNoOrdered = nx.betweenness_centrality(G, weight="weight")
    centralityValues = sorted(centralityValuesNoOrdered.items(), key=operator.itemgetter(1), reverse=False)
    for id in range(0, len(G.nodes)):
        if G.degree(centralityValues[id][0]) == 0:
            isolated_Devices.append(centralityValues[id][0])
    # print("This is isolated devices: ",isolated_Devices)
    for i in range(n, newsize):
        G.add_node(i)
        if len(isolated_Devices) == 0:
            PR = eval(func_PROPAGATIONTIME)
            BW = eval(func_BANDWITDH)
            G.add_CityD(i, i - 40, PR=PR, BW=BW)
            PR = eval(func_PROPAGATIONTIME)
            BW = eval(func_BANDWITDH)
            G.add_CityD(i, i - 6, PR=PR, BW=BW)
        elif len(isolated_Devices) < 2:
            for dev in isolated_Devices:
                PR = eval(func_PROPAGATIONTIME)
                BW = eval(func_BANDWITDH)
                G.add_CityD(i, dev, PR=PR, BW=BW)
                PR = eval(func_PROPAGATIONTIME)
                BW = eval(func_BANDWITDH)
                G.add_CityD(i, i - 40, PR=PR, BW=BW)
                print("This is isolated devices: ", dev)
        else:
            for dev in isolated_Devices:
                G.add_CityD(i, dev, PR=eval(func_PROPAGATIONTIME), BW=BW)

    for i in range(0, len(G.nodes)):
        mylabels[i] = str(i)
    mapping = dict(zip(G, range(len(mylabels))))
    G = nx.relabel_nodes(G, mapping)

    for i in range(n, newsize):
        nodeRAM[i] = eval(func_NODERAM)
        CPUCore[i] = eval(func_CPU_Core)
        nodeSpeed[i] = eval(func_NODESPEED)
        nodeSTORAGE[i] = eval(func_NODESTORAGE)
        SumRAM = SumRAM + nodeRAM[i]
        SumStorage = SumStorage + nodeSTORAGE[i]
        SumCore = SumCore + CPUCore[i]

    # JSON EXPORT
    netJson = {}
    netJson1 = {}

    for i in range(n, newsize):
        myNode = {'id': initial_len, 'IPT': nodeSpeed[i],
                  'cpu': {'core_num': CPUCore[i], 'cache': 4, 'speed': nodeSpeed[i]}, 'storage': nodeSTORAGE[i],
                  'RAM': nodeRAM[i]}
        initial_len = initial_len + 1
        devices.append(myNode)

    for e in G.CityDs:
        myLink = {}
        myLink['s'] = e[0]
        myLink['d'] = e[1]
        myLink['PR'] = G[e[0]][e[1]]['PR']
        myLink['BW'] = G[e[0]][e[1]]['BW']
        myCityDs.append(myLink)

    for i in range(n, newsize):
        myNode1 = {}
        myNode1['id'] = i
        myNode1['RAM'] = nodeRAM[i]
        myNode1['RAM-norm'] = nodeRAM[i] / SumRAM
        myNode1['IPT'] = nodeSpeed[i]
        myNode1['core'] = CPUCore[i]
        myNode1['storage'] = nodeSTORAGE[i]
        devices1.append(myNode1)

    weightNetwork1(G)

    centralityValuesNoOrdered = nx.betweenness_centrality(G, weight="weight")
    centralityValues = sorted(centralityValuesNoOrdered.items(), key=operator.itemgetter(1), reverse=True)

    highestCentrality = centralityValues[0][1]
    gateway_info = []
    for device in centralityValues:
        if device[1] == highestCentrality:
            cloudgatewaysDevices.add(device[0])

    initialIndx = int((1 - PERCENTATGEOFGATEWAYS) * len(G.nodes))  # Indice del final para los X tanto por ciento nodos
    cloudgateway = True
    for idDev in range(initialIndx - 1, (len(G.nodes))):
        if (cloudgateway == True):
            # cloudgatewaysDevices.add(centralityValues[idDev][0])
            cloudgateway = False
        else:
            gatewaysDevices.add(centralityValues[idDev][0])
            gateway_info.append({'id': centralityValues[idDev][0], 'centrality_value': centralityValues[idDev][1]})
    print("This gateway devices in this certain time window:", gateway_info)

    for cloudGtw in cloudgatewaysDevices:
        myLink = {}
        myLink['s'] = cloudGtw
        myLink['d'] = cloudId
        myLink['PR'] = CLOUDPR
        myLink['BW'] = CLOUDBW

        myCityDs.append(myLink)

    netJson['entity'] = devices
    netJson['link'] = myCityDs
    netJson1['entity'] = devices1
    netJson1['link'] = myCityDs
    netfile = "networkDefinition_" + str(tt) + ".json"
    netfile1 = "networkDefinition1_" + str(tt) + ".json"
    file = open(netfile, "w")
    file.write(json.dumps(netJson))
    file.close()
    file = open(netfile1, "w")
    file.write(json.dumps(netJson1))
    file.close()
    return G, initial_len, devices, centralityValuesNoOrdered, gatewaysDevices, SumRAM, SumStorage, SumCore


def weightNetwork1(G):
    size = float(1)
    for e in G.CityDs:
        G[e[0]][e[1]]['weight'] = float(G[e[0]][e[1]]['PR']) + (size / float(G[e[0]][e[1]]['BW']))


# ***********************************************************************************************************************
# Commmunity calculation based on modularity maximization in multilayer network

# ***********************************************************************************************************************

def initial_partitioning(G, resolution):
    devices = get_devices()
    #print("The number of devices in initial state:  ", len(devices))

    nx.write_graphml(G, 'graph.graphml')  # Export NX graph to file
    Gix = ig.read('graph.graphml', format="graphml")  # Create new IG graph from file

    partitions = louvain.find_partition(Gix, louvain.RBConfigurationVertexPartition, resolution_parameter=resolution)
    membership = partitions.membership

    return partitions, membership


def update_partitions(G, initial_len, new_nodes, del_nodes, tt, pre_topo_par,
                      pre_topo_mem, SumRAM, SumStorage, SumCore):
    devices = get_devices()
    nx.write_graphml(G, 'graph0.graphml')  # Export NX graph to file
    pre_Gix = ig.read('graph0.graphml', format="graphml")
    print("The number of devices in update function before any changes:  ", len(devices))
    G, devices, SumRAM, SumStorage, SumCore = network_update_del(G, del_nodes, SumRAM, SumStorage, SumCore, devices)
    topology_layer = NETWORKGENERATION(G)

    nx.write_graphml(G, 'graph.graphml1')  # Export NX graph to file
    Gix = ig.read('graph.graphml1', format="graphml")
    topo_par, topo_mem = louvain_ext.monolaye_update_partition_del2(del_nodes, pre_Gix, Gix, G, pre_topo_par,
                                                                    pre_topo_mem)

    G, initial_len, devices, centralityValuesNoOrdered, gatewaysDevices, SumRAM, SumStorage, SumCore = network_update_add(
        G, initial_len, tt, new_nodes, SumRAM, SumStorage, SumCore, devices)

    print("number of fog devices: ", len(devices))
    topology_layer = NETWORKGENERATION(G)

    print("deleted nodes: ", del_nodes)
    print("Graph size: ", len(topology_layer))
    # n = work.shape[0]
    n = (len(devices))
    # Here we represent intralayer in a single "supra-adjacency"

    nx.write_graphml(G, 'graph.graphml2')  # Export NX graph to file
    Gix = ig.read('graph.graphml2', format="graphml")  # Create new IG graph from file
    topo_par1, topo_mem1 = louvain_ext.monolaye_update_partition_add2(new_nodes, Gix, topo_par, topo_mem)

    return topo_par1, topo_mem1, G, initial_len, SumRAM, SumStorage, SumCore, centralityValuesNoOrdered, gatewaysDevices


G, initGraph, initial_len, centralityValuesNoOrdered, gatewaysDevices, SumRAM, SumStorage, SumCore, nodeSpeed, nodeRAM, CPUCore, nodeSTORAGE = network_initiat()



def Normalizing(data):
    normalized = []
    d=np.array(data)
    print("This is d:", d)
    min=d.min()
    max=d.max()
    for i in range(len(data)):
        norm= (d[i]-min)/(max-min)*10
        normalized.append(norm)

    return normalized


def SLAPartitioning(SLAValue, partitionmem):
    G_SLA = SLA_Sim_graph(SLAValue)
    partitions, membership = initial_partitioning(G_SLA, resolution=2)
    #print("partitions pased on the SLA assurance values :  ", partitions)
    #print("Memberships pased on the SLA assurance values :  ", membership)
    AVG = []
    Par_SLA_info = []  # The average SLA value of each SLA partition at time t
    sorted_SLAPar = []
    for par in partitions:
        sum = 0.0
        member = []
        for device in par:
            sum = sum + SLAValue[device]
            member.append(partitionmem[device])
        avg = sum / len(par)
        AVG.append(avg)
        Par_SLA_info.append({'member': member, 'SLAValue': avg})
    for sorted_inf in sorted(Par_SLA_info, key=operator.itemgetter('SLAValue'), reverse=True):
        sorted_SLAPar.append(sorted_inf)
        print(" The average SLA of each SLA_PAR:", sorted_SLAPar)
    return sorted_SLAPar, partitions, membership


AcceptPar = []
Vio_accept = []
SuccessPar = []
Vio_success = []
SatiPar = []
Vio_satify = []
SPt = []
NPt = []
SP = []
NP = []

devices = get_devices()

# Calculating feature and network partition
with open("networkDefinition.json", "r") as json_file:
    content = json.load(json_file)
Fog_resources = content['entity']
network_size = (len(Fog_resources)) - 1
Feature_partitions, Feature_membership, topo_par, topo_mem, cpu_layer, storage_layer, RAM_layer, super_adj = App_placement.initial_multilayer_on_layer(
    G, devices)
print("topological partitions:", topo_par)
print("Feature partitions:", Feature_partitions)
Fog_community = App_placement.comm_attribute1(Fog_resources, Feature_partitions, network_size)

plt.figure(0)
com_color = ['#FF9F33', 'g', 'b', 'r', 'y', 'c', 'm', '#8033FF', '#FF338A', '#A08AAD', '#EAC8EC', '#D4C8EC',
             '#93EAAF', 'g', 'b', 'r', 'y', 'c', 'm', 'g', 'b', 'r', 'y', 'c', 'm', '#FF9F33', 'g', 'b', 'r', 'y', 'c', 'm', '#8033FF', '#FF338A', '#A08AAD', '#EAC8EC', '#D4C8EC',
             '#93EAAF', 'g', 'b', 'r', 'y', 'c', 'm', 'g', 'b', 'r', 'y', 'c', 'm']
pos = nx.spring_layout(G)
topo_count = 0
print("This is length of topological partition: ", len(topo_par))
#print(topo_par)
for i in range(len(topo_par)):
    nx.draw_networkx_nodes(G, pos, nodelist=topo_par[i], node_color=com_color[topo_count])
    topo_count = topo_count + 1
nx.draw_networkx_CityDs(G, pos)
nx.draw_networkx_labels(G, pos)

PAr_SLAList = [[] for j in range(len(topo_par))]  # General SLA assurance at different time intervals for different partitions
SA1 = []
SA2 = []
SA3 = []

SLAassurance1 = [[] for j in range(len(topo_par))]  # SLA assurance 1 at different time intervals for different partitions
SLAassurance2 = [[] for j in range(len(topo_par))]  # SLA assurance 2 at different time intervals
SLAassurance3 = [[] for j in range(len(topo_par))]  # SLA assurance 3 at different time intervals
GSLAList = []

#********************************************************************************************************************************
#time=0
#********************************************************************************************************************************
alpha0 = [0.0 for i in range(0, len(devices))]
Beta0 = [0.0 for i in range(0, len(devices))]
SLAPar_info = []
SPt = []
NPt = []
SP0=[]
NP0=[]
SP2=[]
NP2=[]
SLA_par = []
SLA_mem = []
t=0

for i in range(len(devices) - 1):
    SPt.append([0,0,0])
    NPt.append([0,0,0])
SP0.append(SPt)
NP0.append(NPt)
print("This is SP:",SP)
print("NP",NP)


for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP0[-1], NP0[-1], SLAassurance1[i], SLAassurance2[i],
                                             SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals
    PAr_SLAList[i].append(SLAvalue)
    SLA_par_info, SLApar, SLAmem = SLAPartitioning(SLAvalue, topo_par[i])
    SLAPar_info.append(SLA_par_info)
    SLA_par.append(SLApar)
    SLA_mem.append(SLAmem)
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement.Generating_application(t)
print("SLAPar_info: ",SLAPar_info)
appsRequests, myusers = App_placement.request_generation(t, gatewaysDevices)
App_placement.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# *********************** Multilayer placement without considering Failure***************************

App_placement.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)




# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP0, NP0, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] > 0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})

print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)
# **********************************************************************************************

#********************************************************************************************************************************
#time=1
#********************************************************************************************************************************
alpha0 = [0.0 for i in range(0, len(devices))]
Beta0 = [0.0 for i in range(0, len(devices))]
SLAPar_info = []
SPt = []
NPt = []
SLA_par = []
SLA_mem = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
t=1
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [2, 0, 2, 0, 0, 2], '2': [2, 0, 2, 0, 0, 2], '3': [2, 0, 2, 0, 0, 2], '4': [2, 0, 2, 0, 0, 2], '5': [2, 0, 2, 0, 0, 2], '6': [1, 0, 1, 0, 1, 0], '7': [2, 0, 2, 0, 0, 2], '8': [2, 0, 2, 0, 0, 2], '9': [1, 0, 1, 0, 1, 0], '10': [2, 0, 0, 2, 0, 0], '11': [0, 0, 0, 0, 0, 0], '12': [0, 0, 0, 0, 0, 0], '13': [0, 0, 0, 0, 0, 0], '14': [0, 0, 0, 0, 0, 0], '15': [0, 0, 0, 0, 0, 0], '16': [0, 0, 0, 0, 0, 0], '17': [0, 0, 0, 0, 0, 0], '18': [0, 0, 0, 0, 0, 0], '19': [0, 0, 0, 0, 0, 0], '20': [0, 0, 0, 0, 0, 0], '21': [1, 0, 1, 0, 1, 0], '22': [0, 0, 0, 0, 0, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [1, 0, 1, 0, 0, 1], '29': [1, 0, 1, 0, 0, 1], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [0, 0, 0, 0, 0, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [0, 0, 0, 0,0, 0], '38': [0, 0, 0, 0, 0, 0], '39': [0, 0, 0, 0, 0, 0], '40': [1, 0, 0, 1, 0, 0], '41': [1, 0, 1, 0, 1, 0], '42': [2, 0, 2, 0, 2, 0], '43': [2, 0, 2, 0, 2, 0], '44': [0, 0, 0, 0, 0, 0], '45': [1, 0, 1, 0, 1, 0], '46': [0, 0, 0, 0, 0, 0], '47': [0, 0, 0, 0, 0, 0], '48': [1, 0, 1, 0, 1, 0], '49': [2, 0, 2, 0, 2, 0], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [0, 0, 0, 0, 0, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [7, 0, 7, 0, 0, 7], '69': [10, 0, 10, 0, 10, 0], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0],
'75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81':[0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar.append(SLA_info[j][0])
    Vio_accept.append(SLA_info[j][1])
    Vio_success.append(SLA_info[j][2])
    SuccessPar.append(SLA_info[j][3])
    SatiPar.append(SLA_info[j][4])
    Vio_satify.append(SLA_info[j][5])
    SPt.append([AcceptPar[i], SuccessPar[i], SatiPar[i]])
    NPt.append([Vio_accept[i], Vio_success[i], Vio_satify[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar[i], 'SuccessPar': SuccessPar[i], 'SatiPar': SatiPar[i]})
    i=i+1

AcceptPar_n=Normalizing(AcceptPar)
Vio_accept_n=Normalizing(Vio_accept)
SuccessPar_n=Normalizing(SuccessPar)
Vio_success_n=Normalizing(Vio_success)
SatiPar_n = Normalizing(SatiPar)
Vio_satify_n = Normalizing(Vio_satify)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

print("SLA_Dict in time window", t,":", SLA_Dict)
SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]

#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    #Fail_t.append((SPt[item][0]/1800)*3600)
    Fail_t.append((SPt[item][1] / 1800) * 3600)
L= "Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+"\n"+str(Fail_t)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")

Failure_info1 = open(pathSimple+"Failure_info1.txt", "w")
Failure_info1.write(L)
Failure_info1.write("\n")

print(Fail_t)
SPt_info=[]
NPt_info=[]
for i in range(len(SPt)):
    SPt_info.append({"id":i, "SLA_value":SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id":i, "SLAVio_value":NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify)
print("This is the deadline violation values of Fog devices: ", Vio_satify)
Failure_info1.write(L)
Failure_info1.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L="This is the SLA parameters of Fog devices:"+ str(SPt_info)
Failure_info1.write(L)
Failure_info1.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+ str(NPt_info)
Failure_info1.write(L)
Failure_info1.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)

for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i], SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals
    Sinf_t.append({'topo_id':i, 'members': topo_par[i], 'SLAvalue': SLAvalue ,'Acceptance_rate':SA1, 'success_rate':SA2, 'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par_info, SLApar, SLAmem = SLAPartitioning(SLAvalue, topo_par[i])
    SLAPar_info.append(SLA_par_info)
    SLA_par.append(SLApar)
    SLA_mem.append(SLAmem)
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement.Generating_application(t)
print("SLA value for different topological partitions:",Sinf_t)
print("SLAPar_info: ",SLAPar_info)
#appsRequests, myusers = App_placement.request_generation(t, gatewaysDevices)
#appsRequests, myusers = App_placement.request_generation(t, gatewaysDevices)
App_placement.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# *********************** Multilayer placement without considering Failure***************************

App_placement.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L="high_integrity:"+str(high_integrity)
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))
Failure_info1.write(L)
Failure_info1.write("\n")
Failure_info1.close()
App_placement.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)
# **********************************************************************************************

#********************************************************************************************************************************
#time=2
#********************************************************************************************************************************
t=2
AcceptPar1 = []
Vio_accept1 = []
SuccessPar1 = []
Vio_success1 = []
SatiPar1 = []
Vio_satify1 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
NPt_norm=[]
SPt_norm=[]

SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [2, 0, 2, 0, 0, 2], '4': [2, 0, 2, 0, 0, 2], '5': [2, 0, 2, 0, 0, 2], '6': [2, 0, 2, 0, 0, 2], '7': [2, 0, 2, 0, 0, 2], '8': [2, 0, 2, 0, 0, 2], '9': [2, 0, 2, 0, 0, 2], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 2, 0], '12': [1, 0, 1, 0, 1, 0], '13': [0, 0, 0, 0, 0, 0], '14': [0, 0, 0, 0, 0, 0], '15': [0, 0, 0, 0, 0, 0], '16': [0, 0, 0, 0, 0, 0], '17': [0, 0, 0, 0, 0, 0], '18': [0, 0, 0, 0, 0, 0], '19': [0, 0, 0, 0, 0, 0], '20': [0, 0, 0, 0, 0, 0], '21': [2, 0, 2, 0, 2, 0], '22': [0, 0, 0, 0, 0, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [1, 0, 1, 0, 0, 1], '29': [1, 0, 1, 0, 0, 1], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [0, 0, 0, 0, 0, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [0, 0, 0, 0, 0, 0], '38': [0, 0, 0, 0, 0, 0], '39': [0, 0, 0, 0, 0, 0], '40': [1, 0, 0, 1, 0, 0], '41': [2, 0, 2, 0, 2, 0], '42': [2, 0, 2, 0, 2, 0], '43': [2, 0, 2, 0, 2, 0], '44': [1, 0, 1, 0, 1, 0], '45': [0, 0, 0, 0, 0, 0], '46': [0, 0, 0, 0, 0, 0], '47': [0, 0, 0, 0, 0, 0], '48': [1, 0, 1, 0, 1, 0], '49': [2, 0, 2, 0, 2, 0], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [0, 0, 0, 0, 0, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [7, 0, 7, 0, 0, 7], '69': [12, 0, 12, 0, 12, 0], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar1.append(SLA_info[j][0])
    Vio_accept1.append(SLA_info[j][1])
    Vio_success1.append(SLA_info[j][2])
    SuccessPar1.append(SLA_info[j][3])
    SatiPar1.append(SLA_info[j][4])
    Vio_satify1.append(SLA_info[j][5])
    SPt.append([AcceptPar1[i], SuccessPar1[i], SatiPar1[i]])
    NPt.append([Vio_accept1[i], Vio_success1[i], Vio_satify1[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar1[i], 'SuccessPar': SuccessPar1[i], 'SatiPar': SatiPar1[i]})
    i=i+1
print("SLA_Dict in time window", t, ":", SLA_Dict)
AcceptPar_n=Normalizing(AcceptPar1)
Vio_accept_n=Normalizing(Vio_accept1)
SuccessPar_n=Normalizing(SuccessPar1)
Vio_success_n=Normalizing(Vio_success1)
SatiPar_n = Normalizing(SatiPar1)
Vio_satify_n = Normalizing(Vio_satify1)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]

#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L= "Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+ str(Fail_t)
Failure_info2 = open(pathSimple+"Failure_info2", "w")
Failure_info2.write(L)
Failure_info2.write("\n")
SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify1)
L= "This is the deadline violation values of Fog devices: "+ str(Vio_satify1)
Failure_info2.write(L)
Failure_info2.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+ str(SPt_info)
Failure_info2.write(L)
Failure_info2.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L= "This is the SLA violation values of Fog devices: "+ str(NPt_info)
Failure_info2.write(L)
Failure_info2.write("\n")

print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SP=[[[10,7,5],[23,17,12],[20,18,17],[12,12,11],[25,20,20]], [[10,7,5],[23,17,12],[20,18,17],[12,12,11],[25,20,20]]]#SLA parameters of devices at different times
# NP=[[[13,3,5],[10,6,11],[3,2,3],[0,0,1],[5,5,0]],[[13,3,5],[10,6,11],[3,2,3],[0,0,1],[5,5,0]]]


# For the previous times

#print(SLAassurance1)
app_requests = []
my_users = []
cloudId = 500
FOG_DEVICES = []
number_Of_Services = []
apps_ = []
apps_Deadlines = []
apps_Resources = []
app_storage = []
apps_SourceMessage = []
apps_TotalMIPS = []
map_Service2App = []
map_ServiceId2ServiceName = []
apps_Communities = []
services_Resources = []
service_set = []
SLAPar_info = []
SLA_par = []
SLA_mem = []
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],
                                                 SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals
    Sinf_t.append(
        {'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})

    PAr_SLAList[i].append(SLAvalue)
    SLA_par_info, SLApar, SLAmem = SLAPartitioning(SLAvalue, topo_par[i])
    SLAPar_info.append(SLA_par_info)
    SLA_par.append(SLApar)
    SLA_mem.append(SLAmem)
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)

#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement.Generating_application(t)
#appsRequests, myusers = App_placement.request_generation(t, gatewaysDevices)

App_placement.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)
#print("This is SLA partitions insides the network partitions: ", SLAPar_info)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance3)


# *********************** Multilayer placement without considering Failure***************************

App_placement.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)



# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L="high_integrity:"+str(high_integrity)
Failure_info2.write(L)
Failure_info2.write("\n")
Failure_info2.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)
# **********************************************************************************************
#********************************************************************************************************************************
#time=3
#********************************************************************************************************************************

# For the new time interval
t=3
AcceptPar2 = []
Vio_accept2 = []
SuccessPar2 = []
Vio_success2 = []
SatiPar2 = []
Vio_satify2 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [2, 0, 2, 0, 0, 2], '2': [1, 0, 1, 0, 1, 0], '3': [1, 0, 1, 0, 1, 0], '4': [0, 0, 0, 0, 0, 0], '5': [1, 0, 1, 0, 1, 0], '6': [2, 0, 2, 0, 0, 2], '7': [2, 0, 2, 0, 0, 2], '8': [2, 0, 2, 0, 0, 2], '9': [1, 0, 1, 0, 1, 0], '10': [0, 0, 0, 0, 0, 0], '11': [1, 0, 1, 0, 1, 0], '12': [2, 0, 2, 0, 2, 0], '13': [2, 0, 2, 0, 2, 0], '14': [2, 0, 2, 0, 2, 0], '15': [2, 0, 2, 0, 2, 0], '16': [1, 0, 1, 0, 0, 1], '17': [0, 0, 0, 0, 0, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 0, 2], '20': [0, 0, 0, 0, 0, 0], '21': [0, 0, 0, 0, 0, 0], '22': [0, 0, 0, 0, 0, 0], '23': [0, 0, 0, 0, 0, 0], '24': [1, 0, 1, 0, 0, 1], '25': [1, 0, 1, 0, 0, 1], '26': [1, 0, 1, 0, 0, 1], '27': [0, 0, 0, 0, 0, 0], '28': [1, 0, 1, 0, 0, 1], '29': [1, 0, 1, 0, 0, 1], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [0, 0, 0, 0, 0, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [1, 0, 1, 0, 1, 0], '39': [2, 0, 2, 0, 2, 0], '40': [0, 0, 0, 0, 0, 0], '41': [2, 0, 2, 0, 2, 0], '42': [2, 0, 2, 0, 2, 0], '43': [2, 0, 2, 0, 2, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [2, 0, 2, 0, 2, 0], '47': [1, 0, 1, 0, 1, 0], '48': [1, 0, 1, 0, 1, 0], '49': [0, 0, 0, 0, 0, 0], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [0, 0, 0, 0, 0, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [4, 0, 4, 0, 4, 0], '59': [4, 0, 4, 0, 4, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [7, 0, 7, 0, 0, 7], '69': [8, 0, 8, 0, 8, 0], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [0, 0, 0, 0, 0, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar2.append(SLA_info[j][0])
    Vio_accept2.append(SLA_info[j][1])
    Vio_success2.append(SLA_info[j][2])
    SuccessPar2.append(SLA_info[j][3])
    SatiPar2.append(SLA_info[j][4])
    Vio_satify2.append(SLA_info[j][5])
    SPt.append([AcceptPar2[i], SuccessPar2[i], SatiPar2[i]])
    NPt.append([Vio_accept2[i], Vio_success2[i], Vio_satify2[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar2[i], 'SuccessPar': SuccessPar2[i], 'SatiPar': SatiPar2[i]})
    i=i+1
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar2)
Vio_accept_n=Normalizing(Vio_accept2)
SuccessPar_n=Normalizing(SuccessPar2)
Vio_success_n=Normalizing(Vio_success2)
SatiPar_n = Normalizing(SatiPar2)
Vio_satify_n = Normalizing(Vio_satify2)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L="Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+str(Fail_t)
Failure_info3 = open(pathSimple+"Failure_info3", "w")
Failure_info3.write(L)
Failure_info3.write("\n")

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify2)
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify2)
Failure_info3.write(L)
Failure_info3.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info3.write(L)
Failure_info3.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info3.write(L)
Failure_info3.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,5],[23,17,12],[20,18,17],[12,12,11],[25,20,20]]
# NPt=[[13,3,5],[10,6,11],[3,2,3],[0,0,1],[5,5,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement.Generating_application(t)
#appsRequests, myusers = App_placement.request_generation(t, gatewaysDevices)
App_placement.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance3)


# *********************** Multilayer placement without considering Failure***************************

App_placement.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)



# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L= "high_integrity:"+str(high_integrity)
Failure_info3.write(L)
Failure_info3.write("\n")
Failure_info3.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************
#********************************************************************************************************************************
#time=4
#********************************************************************************************************************************

# For the new time interval
t=4
AcceptPar3 = []
Vio_accept3 = []
SuccessPar3 = []
Vio_success3 = []
SatiPar3 = []
Vio_satify3 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar3.append(SLA_info[j][0])
    Vio_accept3.append(SLA_info[j][1])
    Vio_success3.append(SLA_info[j][2])
    SuccessPar3.append(SLA_info[j][3])
    SatiPar3.append(SLA_info[j][4])
    Vio_satify3.append(SLA_info[j][5])
    SPt.append([AcceptPar3[i], SuccessPar3[i], SatiPar3[i]])
    NPt.append([Vio_accept3[i], Vio_success3[i], Vio_satify3[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar3[i], 'SuccessPar': SuccessPar3[i], 'SatiPar': SatiPar3[i]})
    i=i+1
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar3)
Vio_accept_n=Normalizing(Vio_accept3)
SuccessPar_n=Normalizing(SuccessPar3)
Vio_success_n=Normalizing(Vio_success3)
SatiPar_n = Normalizing(SatiPar3)
Vio_satify_n = Normalizing(Vio_satify3)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L="Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+str(Fail_t)
Failure_info4 = open(pathSimple+"Failure_info4", "w")
Failure_info4.write(L)
Failure_info4.write("\n")

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify3)
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify3)
Failure_info4.write(L)
Failure_info4.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info4.write(L)
Failure_info4.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info4.write(L)
Failure_info4.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,5],[34,17,12],[20,18,17],[12,12,11],[25,20,20]]
# NPt=[[14,4,5],[10,6,11],[4,2,4],[0,0,1],[5,5,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3= SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement.Generating_application(t)
#appsRequests, myusers = App_placement.request_generation(t, gatewaysDevices)
App_placement.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance4)


# *********************** Multilayer placement without considering Failure***************************

App_placement.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)



# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L= "high_integrity:"+str(high_integrity)
Failure_info4.write(L)
Failure_info4.write("\n")
Failure_info4.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************

#********************************************************************************************************************************
#time=5
#********************************************************************************************************************************

# For the new time interval
t=5
AcceptPar4 = []
Vio_accept4 = []
SuccessPar4 = []
Vio_success4 = []
SatiPar4 = []
Vio_satify4 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar4.append(SLA_info[j][0])
    Vio_accept4.append(SLA_info[j][1])
    Vio_success4.append(SLA_info[j][2])
    SuccessPar4.append(SLA_info[j][3])
    SatiPar4.append(SLA_info[j][4])
    Vio_satify4.append(SLA_info[j][5])
    SPt.append([AcceptPar4[i], SuccessPar4[i], SatiPar4[i]])
    NPt.append([Vio_accept4[i], Vio_success4[i], Vio_satify4[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar4[i], 'SuccessPar': SuccessPar4[i], 'SatiPar': SatiPar4[i]})
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar4)
Vio_accept_n=Normalizing(Vio_accept4)
SuccessPar_n=Normalizing(SuccessPar4)
Vio_success_n=Normalizing(Vio_success4)
SatiPar_n = Normalizing(SatiPar4)
Vio_satify_n = Normalizing(Vio_satify4)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L="Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+str(Fail_t)
Failure_info5 = open(pathSimple+"Failure_info5", "w")
Failure_info5.write(L)
Failure_info5.write("\n")

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify4)
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify4)
Failure_info5.write(L)
Failure_info5.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info5.write(L)
Failure_info5.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info5.write(L)
Failure_info5.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,5],[23,17,12],[20,18,17],[12,12,11],[25,20,20]]
# NPt=[[13,3,5],[10,6,11],[3,2,3],[0,0,1],[5,5,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement7.Generating_application(t)
#appsRequests, myusers = App_placement7.request_generation(t, gatewaysDevices)
App_placement7.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance3)


# *********************** Multilayer placement without considering Failure***************************

App_placement7.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)



# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L= "high_integrity:"+str(high_integrity)
Failure_info5.write(L)
Failure_info5.write("\n")
Failure_info5.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement7.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************

# **********************************************************************************************
#********************************************************************************************************************************
#time=6
#********************************************************************************************************************************

# For the new time interval
t=6
AcceptPar5 = []
Vio_accept5 = []
SuccessPar5 = []
Vio_success5 = []
SatiPar5 = []
Vio_satify5 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar5.append(SLA_info[j][0])
    Vio_accept5.append(SLA_info[j][1])
    Vio_success5.append(SLA_info[j][2])
    SuccessPar5.append(SLA_info[j][3])
    SatiPar5.append(SLA_info[j][4])
    Vio_satify5.append(SLA_info[j][5])
    SPt.append([AcceptPar5[i], SuccessPar5[i], SatiPar5[i]])
    NPt.append([Vio_accept5[i], Vio_success5[i], Vio_satify5[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar5[i], 'SuccessPar': SuccessPar5[i], 'SatiPar': SatiPar5[i]})
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar5)
Vio_accept_n=Normalizing(Vio_accept5)
SuccessPar_n=Normalizing(SuccessPar5)
Vio_success_n=Normalizing(Vio_success5)
SatiPar_n = Normalizing(SatiPar5)
Vio_satify_n = Normalizing(Vio_satify5)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L="Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+str(Fail_t)
Failure_info6 = open(pathSimple+"Failure_info6", "w")
Failure_info6.write(L)
Failure_info6.write("\n")

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify5)
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify5)
Failure_info6.write(L)
Failure_info6.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info6.write(L)
Failure_info6.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info6.write(L)
Failure_info6.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,6],[23,17,12],[20,18,17],[12,12,11],[26,20,20]]
# NPt=[[13,3,6],[10,6,11],[3,2,3],[0,0,1],[6,6,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement6.Generating_application(t)
#appsRequests, myusers = App_placement6.request_generation(t, gatewaysDevices)
App_placement7.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance3)


# *********************** Multilayer placement without considering Failure***************************

App_placement7.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L="high_integrity:"+str(high_integrity)
Failure_info6.write(L)
Failure_info6.write("\n")
Failure_info6.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement7.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************
#********************************************************************************************************************************
#time=7
#********************************************************************************************************************************

# For the new time interval
t=7
AcceptPar6 = []
Vio_accept6 = []
SuccessPar6 = []
Vio_success6 = []
SatiPar6 = []
Vio_satify6 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar6.append(SLA_info[j][0])
    Vio_accept6.append(SLA_info[j][1])
    Vio_success6.append(SLA_info[j][2])
    SuccessPar6.append(SLA_info[j][3])
    SatiPar6.append(SLA_info[j][4])
    Vio_satify6.append(SLA_info[j][5])
    SPt.append([AcceptPar6[i], SuccessPar6[i], SatiPar6[i]])
    NPt.append([Vio_accept6[i], Vio_success6[i], Vio_satify6[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar6[i], 'SuccessPar': SuccessPar6[i], 'SatiPar': SatiPar6[i]})
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar6)
Vio_accept_n=Normalizing(Vio_accept6)
SuccessPar_n=Normalizing(SuccessPar6)
Vio_success_n=Normalizing(Vio_success6)
SatiPar_n = Normalizing(SatiPar6)
Vio_satify_n = Normalizing(Vio_satify6)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L="Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+str(Fail_t)
Failure_info7 = open(pathSimple+"Failure_info7", "w")
Failure_info7.write(L)
Failure_info7.write("\n")

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify6)
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify5)
Failure_info7.write(L)
Failure_info7.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info7.write(L)
Failure_info7.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info7.write(L)
Failure_info7.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,6],[23,17,12],[20,18,17],[12,12,11],[26,20,20]]
# NPt=[[13,3,6],[10,6,11],[3,2,3],[0,0,1],[6,6,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement6.Generating_application(t)
#appsRequests, myusers = App_placement6.request_generation(t, gatewaysDevices)
App_placement7.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)



# *********************** Multilayer placement without considering Failure***************************

App_placement7.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L="high_integrity:"+str(high_integrity)
Failure_info7.write(L)
Failure_info7.write("\n")
Failure_info7.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement7.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************
#********************************************************************************************************************************
#time=8
#********************************************************************************************************************************

# For the new time interval
t=8
AcceptPar7 = []
Vio_accept7 = []
SuccessPar7 = []
Vio_success7 = []
SatiPar7 = []
Vio_satify7 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar7.append(SLA_info[j][0])
    Vio_accept7.append(SLA_info[j][1])
    Vio_success7.append(SLA_info[j][2])
    SuccessPar7.append(SLA_info[j][3])
    SatiPar7.append(SLA_info[j][4])
    Vio_satify7.append(SLA_info[j][5])
    SPt.append([AcceptPar7[i], SuccessPar7[i], SatiPar7[i]])
    NPt.append([Vio_accept7[i], Vio_success7[i], Vio_satify7[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar7[i], 'SuccessPar': SuccessPar7[i], 'SatiPar': SatiPar7[i]})
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar7)
Vio_accept_n=Normalizing(Vio_accept7)
SuccessPar_n=Normalizing(SuccessPar7)
Vio_success_n=Normalizing(Vio_success7)
SatiPar_n = Normalizing(SatiPar7)
Vio_satify_n = Normalizing(Vio_satify7)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L="Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+ "\n"+str(Fail_t)
Failure_info8 = open(pathSimple+"Failure_info8", "w")
Failure_info8.write(L)
Failure_info8.write("\n")

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify7)
L="This is the deadline violation values of Fog devices: "+ str(Vio_satify7)
Failure_info8.write(L)
Failure_info8.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info8.write(L)
Failure_info8.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info8.write(L)
Failure_info8.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,6],[23,17,12],[20,18,17],[12,12,11],[26,20,20]]
# NPt=[[13,3,6],[10,6,11],[3,2,3],[0,0,1],[6,6,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})
    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("SLA value for different topological partitions:",Sinf_t)
#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement6.Generating_application(t)
#appsRequests, myusers = App_placement6.request_generation(t, gatewaysDevices)
App_placement7.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance3)


# *********************** Multilayer placement without considering Failure***************************

App_placement7.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L="high_integrity:"+str(high_integrity)
Failure_info8.write(L)
Failure_info8.write("\n")
Failure_info8.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement7.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************


#********************************************************************************************************************************
#time=9
#********************************************************************************************************************************

# For the new time interval
t=9
AcceptPar8 = []
Vio_accept8 = []
SuccessPar8 = []
Vio_success8 = []
SatiPar8 = []
Vio_satify8 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]

devices = get_devices()
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar8.append(SLA_info[j][0])
    Vio_accept8.append(SLA_info[j][1])
    Vio_success8.append(SLA_info[j][2])
    SuccessPar8.append(SLA_info[j][3])
    SatiPar8.append(SLA_info[j][4])
    Vio_satify8.append(SLA_info[j][5])
    SPt.append([AcceptPar8[i], SuccessPar8[i], SatiPar8[i]])
    NPt.append([Vio_accept8[i], Vio_success8[i], Vio_satify8[i]])
    SLA_Dict.append({'id': i, 'AcceptPar': AcceptPar8[i], 'SuccessPar': SuccessPar8[i], 'SatiPar': SatiPar8[i]})
print("SLA_Dict in time window", t, ":", SLA_Dict)

AcceptPar_n=Normalizing(AcceptPar8)
Vio_accept_n=Normalizing(Vio_accept8)
SuccessPar_n=Normalizing(SuccessPar8)
Vio_success_n=Normalizing(Vio_success8)
SatiPar_n = Normalizing(SatiPar8)
Vio_satify_n = Normalizing(Vio_satify8)

for i in range(len(devices) - 1):
    SPt_norm.append([AcceptPar_n[i], SuccessPar_n[i], SatiPar_n[i]])
    NPt_norm.append([Vio_accept_n[i], Vio_success_n[i], Vio_satify_n[i]])

SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
L= "Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+"\n"+str(Fail_t)
Failure_info9 = open(pathSimple+"Failure_info9", "w")
Failure_info9.write(L)
Failure_info9.write("\n")
SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify8)
L="This is the deadline violation values of Fog devices: "+str(Vio_satify8)
Failure_info9.write(L)
Failure_info9.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info9.write(L)
Failure_info9.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info9.write(L)
Failure_info9.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)
# SPt=[[10,7,5],[23,17,12],[20,18,17],[12,12,11],[25,20,20]]
# NPt=[[13,3,5],[10,6,11],[3,2,3],[0,0,1],[5,5,0]]
for i in range(len(topo_par)):
    SLAvalue, SA1, SA2, SA3 = SLACalculation(topo_par[i], i, SP[-1], NP[-1], SLAassurance1[i], SLAassurance2[i],SLAassurance3[i])  # The general SLA assurance of each device in the partition at time t based on SLA value in previous time intervals

    Sinf_t.append({'topo_id': i, 'members': topo_par[i], 'SLAvalue': SLAvalue, 'Acceptance_rate': SA1, 'success_rate': SA2,'satisfation_rate': SA3})

    PAr_SLAList[i].append(SLAvalue)
    SLA_par = SLAPartitioning(SLAvalue, topo_par[i])
    #print("This is SLA values for partition i:", i, "with these members:", partitions[i], " :  ", SLAvalue)
    #print(SLA_par)
    GSLAList.append(SLAvalue)
print("SLAPar_info: ",SLAPar_info)
print("`SLA value for different topological partitions:",Sinf_t)

#numberOfServices, serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName = App_placement7.Generating_application(t)
#appsRequests, myusers = App_placement7.request_generation(t, gatewaysDevices)
App_placement7.Multilayerplacement(t, G, devices, topo_mem,topo_par, Fog_community, SLAPar_info, gatewaysDevices,
                                      centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                      appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)


# print(SLAassurance1)
# print(SLAassurance2)
# print(SLAassurance3)


# *********************** Multilayer placement without considering Failure***************************

App_placement7.Multilayerplacement_NF(t,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,
                                     centralityValuesNoOrdered, numberOfServices,serviceset,appsDeadlines,
                                     appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)



# ************************************ State of the art*****************************************

integrity, reputation, utility, alpha0, Beta0 = TSLA_cal(t,SP2, NP2, alpha0, Beta0)
high_integrity = []
for i in range(len(integrity)):
    if integrity[i] >  0.7:
        high_integrity.append({"id": i, "integrity": integrity[i]})
L="high_integrity:"+str(high_integrity)
Failure_info9.write(L)
Failure_info9.write("\n")
Failure_info9.close()
print("high_integrity:",high_integrity)
print("number of devices with high integrity value:",len(high_integrity))

App_placement7.Multilayerplc_SOTA(t, G, devices, topo_mem,topo_par, Fog_community, high_integrity, gatewaysDevices,
                                 centralityValuesNoOrdered, numberOfServices, serviceset, appsDeadlines,
                                 appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests)

# **********************************************************************************************

AcceptPar9 = []
Vio_accept9 = []
SuccessPar9 = []
Vio_success9 = []
SatiPar9 = []
Vio_satify9 = []
SPt = []
NPt = []
SLA_Dict=[]
Sinf_t=[]
SPt_norm=[]
NPt_norm=[]
devices = get_devices()
t=10
SLA_info={'0': [0, 1, 0, 0, 0, 0], '1': [0, 0, 0, 0, 0, 0], '2': [0, 0, 0, 0, 0, 0], '3': [0, 0, 0, 0, 0, 0], '4': [0, 0, 0, 0, 0, 0], '5': [0, 0, 0, 0, 0, 0], '6': [0, 0, 0, 0, 0, 0], '7': [0, 0, 0, 0, 0, 0], '8': [0, 0, 0, 0, 0, 0], '9': [0, 0, 0, 0, 0, 0], '10': [1, 0, 0, 1, 0, 0], '11': [2, 0, 2, 0, 0, 2], '12': [1, 0, 1, 0, 0, 1], '13': [2, 0, 2, 0, 0, 2], '14': [2, 0, 2, 0, 0, 2], '15': [1, 0, 1, 0, 1, 0], '16': [2, 0, 2, 0, 2, 0], '17': [2, 0, 2, 0, 2, 0], '18': [1, 0, 1, 0, 1, 0], '19': [2, 0, 2, 0, 2, 0], '20': [0, 0, 0, 0, 0, 0], '21': [3, 0, 3, 0, 3, 0], '22': [3, 0, 3, 0, 3, 0], '23': [0, 0, 0, 0, 0, 0], '24': [0, 0, 0, 0, 0, 0], '25': [0, 0, 0, 0, 0, 0], '26': [0, 0, 0, 0, 0, 0], '27': [0, 0, 0, 0, 0, 0], '28': [0, 0, 0, 0, 0, 0], '29': [0, 0, 0, 0, 0, 0], '30': [0, 1, 0, 0, 0, 0], '31': [0, 0, 0, 0, 0, 0], '32': [3, 0, 3, 0, 3, 0], '33': [0, 0, 0, 0, 0, 0], '34': [0, 0, 0, 0, 0, 0], '35': [0, 0, 0, 0, 0, 0], '36': [0, 0, 0, 0, 0, 0], '37': [1, 0, 1, 0, 1, 0], '38': [0, 0, 0, 0, 0, 0], '39': [1, 0, 1, 0, 1, 0], '40': [0, 0, 0, 0, 0, 0], '41': [0, 0, 0, 0, 0, 0], '42': [2, 0, 2, 0, 2, 0], '43': [1, 0, 1, 0, 1, 0], '44': [0, 0, 0, 0, 0, 0], '45': [0, 0, 0, 0, 0, 0], '46': [3, 0, 3, 0, 0, 3], '47': [2, 0, 2, 0, 2, 0], '48': [2, 0, 2, 0, 2, 0], '49': [2, 0, 2, 0, 0, 2], '50': [0, 1, 0, 0, 0, 0], '51': [0, 0, 0, 0, 0, 0], '52': [0, 0, 0, 0, 0, 0], '53': [4, 0, 4, 0, 4, 0], '54': [0, 0, 0, 0, 0, 0], '55': [0, 0, 0, 0, 0, 0], '56': [0, 0, 0, 0, 0, 0], '57': [0, 0, 0, 0, 0, 0], '58': [3, 0, 3, 0, 3, 0], '59': [0, 0, 0, 0, 0, 0], '60': [0, 1, 0, 0, 0, 0], '61': [0, 0, 0, 0, 0, 0], '62': [0, 0, 0, 0, 0, 0], '63': [0, 1, 0, 0, 0, 0], '64': [0, 0, 0, 0, 0, 0], '65': [0, 0, 0, 0, 0, 0], '66': [0, 0, 0, 0, 0, 0], '67': [0, 0, 0, 0, 0, 0], '68': [0, 0, 0, 0, 0, 0], '69': [13, 0, 13, 0, 10, 3], '70': [0, 1, 0, 0, 0, 0], '71': [0, 0, 0, 0, 0, 0], '72': [0, 0, 0, 0, 0, 0], '73': [0, 0, 0, 0, 0, 0], '74': [0, 0, 0, 0, 0, 0], '75': [0, 0, 0, 0, 0, 0], '76': [0, 0, 0, 0, 0, 0], '77': [0, 0, 0, 0, 0, 0], '78': [8, 0, 8, 0, 8, 0], '79': [8, 0, 8, 0, 8, 0], '80': [0, 1, 0, 0, 0, 0], '81': [0, 0, 0, 0, 0, 0], '82': [0, 0, 0, 0, 0, 0], '83': [0, 0, 0, 0, 0, 0], '84': [0, 0, 0, 0, 0, 0], '85': [0, 0, 0, 0, 0, 0], '86': [0, 0, 0, 0, 0, 0], '87': [0, 0, 0, 0, 0, 0], '88': [0, 0, 0, 0, 0, 0], '89': [0, 0, 0, 0, 0, 0], '90': [0, 1, 0, 0, 0, 0], '91': [0, 1, 0, 0, 0, 0], '92': [0, 1, 0, 0, 0, 0], '93': [0, 0, 0, 0, 0, 0], '94': [0, 0, 0, 0, 0, 0], '95': [0, 0, 0, 0, 0, 0], '96': [0, 0, 0, 0, 0, 0], '97': [0, 0, 0, 0, 0, 0], '98': [0, 0, 0, 0, 0, 0], '99': [0, 0, 0, 0, 0, 0], '100': [0, 0, 0, 0, 0, 0], '101': [0, 0, 0, 0, 0, 0], '102': [0, 0, 0, 0, 0, 0], '103': [0, 0, 0, 0, 0, 0], '104': [0, 0, 0, 0, 0, 0], '105': [0, 0, 0, 0, 0, 0], '106': [0, 0, 0, 0, 0, 0], '107': [0, 0, 0, 0, 0, 0], '108': [0, 0, 0, 0, 0, 0], '109': [0, 0, 0, 0, 0, 0], '110': [0, 1, 0, 0, 0, 0], '111': [0, 0, 0, 0, 0, 0], '112': [0, 0, 0, 0, 0, 0], '113': [0, 0, 0, 0, 0, 0], '114': [0, 0, 0, 0, 0, 0], '115': [0, 0, 0, 0, 0, 0], '116': [0, 0, 0, 0, 0, 0], '117': [0, 0, 0, 0, 0, 0], '118': [0, 0, 0, 0, 0, 0], '119': [0, 0, 0, 0, 0, 0]}
i=0
for j in SLA_info:
    AcceptPar9.append(SLA_info[j][0])
    Vio_accept9.append(SLA_info[j][1])
    Vio_success9.append(SLA_info[j][2])
    SuccessPar9.append(SLA_info[j][3])
    SatiPar9.append(SLA_info[j][4])
    Vio_satify9.append(SLA_info[j][5])
    SPt.append([AcceptPar9[i], SuccessPar9[i], SatiPar9[i]])
    NPt.append([Vio_accept9[i], Vio_success9[i], Vio_satify9[i]])
    SPt_norm= Normalizing(SPt)
    NPt_norm=Normalizing(NPt)
SP.append(SPt_norm)
NP.append(NPt_norm)
SP2.append(SPt)
NP2.append(NPt)
Fail_t=[]
#print("Hellllooooo")
#print("This is the SLA parameters of Fog devices:", NPt)
for item in range(len(NPt)):
    Fail_t.append((SPt[item][1]/1800)*3600)
"""print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)
print("This is the deadline violation values of Fog devices: ", Vio_satify4)
print("This is the SLA parameters of Fog devices:", SPt)
print("This is the SLA violation values of Fog devices: ", NPt)
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)"""

L= "Failure time of Fog devices in one hour for simulation in time interval"+str(t)+":"+"\n"+str(Fail_t)
Failure_info10 = open(pathSimple+"Failure_info10", "w")
Failure_info10.write(L)
Failure_info10.write("\n")
print("Failure time of Fog devices in one hour for simulation in time interval",t,":")
print(Fail_t)

SPt_info = []
NPt_info = []
for i in range(len(SPt)):
    SPt_info.append({"id": i, "SLA_value": SPt[i]})

for i in range(len(NPt)):
    NPt_info.append({"id": i, "SLAVio_value": NPt[i]})

slafile = "SLA_value" + str(t) + ".json"
file = open(slafile, "w")
file.write(json.dumps(SPt_info))
file.close()
vioslafile = "SLAVio_value" + str(t) + ".json"
file = open(vioslafile, "w")
file.write(json.dumps(NPt_info))
file.close()

print("This is the deadline violation values of Fog devices: ", Vio_satify9)
L="This is the deadline violation values of Fog devices: "+str(Vio_satify9)
Failure_info10.write(L)
Failure_info10.write("\n")
print("This is the SLA parameters of Fog devices:", SPt_info)
L= "This is the SLA parameters of Fog devices:"+str(SPt_info)
Failure_info10.write(L)
Failure_info10.write("\n")
print("This is the SLA violation values of Fog devices: ", NPt_info)
L="This is the SLA violation values of Fog devices: "+str(NPt_info)
Failure_info10.write(L)
Failure_info10.write("\n")
print("This is the SLA parameters of Fog devices:", SP)
print("This is the SLA violation values of Fog devices: ", NP)

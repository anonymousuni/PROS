#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import math

import louvain
import networkx as nx
import igraph as ig
import random
import operator
import json
import numpy as np
import Similaritymeasurment
import louvain_ext

APPDEADLINE=[500, 500, 500, 500,500, 2500,2500, 2500,2500,2500]
# USERS and IoT DEVICES
func_REQUESTPROB = "random.random()/8"  # Popularidad de la app. threshold que determina la probabilidad de que un dispositivo tenga asociado peticiones a una app. tle threshold es para cada ap
func_USERREQRAT = "random.randint(10,100)"  # MS


# ***********************************************************************************************************************
# Commmunity calculation based on modularity maximization in multilayer network

# ***********************************************************************************************************************
def NETWORKGENERATION(G):
    topology_matrix = nx.to_numpy_matrix(G)
    # print(len(G.nodes))
    return topology_matrix


def initial_multilayer_on_layer(G, devices):
    print("The number of devices in initial state:  ", len(devices))
    layer_name = {0: 'cpu', 1: 'storage', 2: 'RAM', 4: 'topology'}
    cpu_layer = Similaritymeasurment.layer_creation('cpu', devices)
    storage_layer = Similaritymeasurment.layer_creation('storage', devices)
    RAM_layer = Similaritymeasurment.layer_creation('RAM', devices)
    topology_layer = NETWORKGENERATION(G)

    n = (len(topology_layer)) + 1
    l = len(layer_name) - 1
    # Here we represent intralayer in a single "supra-adjacency"
    super_adj = np.zeros((l * n, l * n))
    super_adj[:n, :n] = cpu_layer
    super_adj[n:2 * n, n:2 * n] = storage_layer
    super_adj[2 * n:3 * n, 2 * n:3 * n] = RAM_layer

    print(super_adj)

    #
    inter_elist = [(i, i + n) for i in range(n)] + \
                  [(i + n, 2 * n + i) for i in range(n)] + \
                  [(2 * n + i, i) for i in range(n)]

    C = np.zeros((3 * n, 3 * n))
    for i, j in inter_elist:
        C[i, j] = 1
        C[j, i] = 1

    layer_vec = np.array([i // n for i in range(3 * n)])


    partitions = []
    membership = []
    mult_part_ens = louvain_ext.parallel_multilayer_louvain_from_adj(intralayer_adj=super_adj,
                                                                     interlayer_adj=C, layer_vec=layer_vec,
                                                                     progress=True, numprocesses=2,
                                                                     inter_directed=False, intra_directed=False,
                                                                     gamma_range=[0, 4], ngamma=5,
                                                                     omega_range=[0, 4], nomega=5, maxpt=[4, 10])

    for i in range(len(mult_part_ens)):
        if mult_part_ens[i]['coupling'] == 1:
            if mult_part_ens[i]['resolution'] == 4:
                partitions.append(mult_part_ens[i]['part'])
                membership.append(mult_part_ens[i]['membership'])


    nx.write_graphml(G, 'graph.graphml')  # Export NX graph to file
    Gix = ig.read('graph.graphml', format="graphml")  # Create new IG graph from file
    print("This is the graph:", Gix.es["weight"])

    topo_par = louvain.find_partition(Gix, louvain.RBConfigurationVertexPartition,weights='weight',
                                          resolution_parameter=1)
    topo_mem = topo_par.membership

    return partitions, membership, topo_par, topo_mem, cpu_layer, storage_layer, RAM_layer, super_adj

# **********************************************************************************************

# Functions for statistics of multilayer_community_detection

# **********************************************************************************************
# (deadline,shortestdistance):occurrences
statisticsDistanceDeadline = {}
cpu_usage = 0.0
# (service,deadline):occurrences
statisticsServiceInstances = {}

# distance:numberOfuserThatRequest
statisticsDistancesRequest = {}

# nodeid:numberOfuserThatRequest
statisticsNodesRequest = {}

# (nodeid,serviceId):ocurrences
statisticsNodesServices = {}

# (centrality,resources):occurrences
statisticsCentralityResources = {}


def calculateNodeUsage(service2DevicePlacementMatrix, nodeRAM, nodeSTORAGE, CPUCore, nodeBussyResources, nodeBussyStorage,nodeBussyCore):
    nodeResUse = list()
    nodeStorUse = list()
    nodeCoreUse = list()
    nodeNumServ = list()
    num_node_usage = 0
    Resource_usage = 0
    for i in service2DevicePlacementMatrix[0]:
        nodeResUse.append(0.0)
        nodeStorUse.append(0.0)
        nodeCoreUse.append(0.0)
        nodeNumServ.append(0)

    for idServ in range(0, len(service2DevicePlacementMatrix)):
        for idDev in range(0, len(service2DevicePlacementMatrix[idServ])):
            if service2DevicePlacementMatrix[idServ][idDev] == 1:
                nodeNumServ[idDev] = nodeNumServ[idDev] + 1
    for idDev in range(0, len(service2DevicePlacementMatrix[0])):
        nodeResUse[idDev] = nodeBussyResources[idDev] / nodeRAM[idDev]
        Resource_usage = Resource_usage + nodeBussyResources[idDev]
        nodeStorUse[idDev] = nodeBussyStorage[idDev] / nodeSTORAGE[idDev]
        nodeCoreUse[idDev] = nodeBussyCore[idDev] / CPUCore[idDev]
        if (nodeResUse[idDev] != 0):
            num_node_usage = num_node_usage + 1
        # nodeResUse[idDev] = nodeBussyResources[idDev]
    nodeResUse = sorted(nodeResUse)
    nodeStorUse = sorted(nodeStorUse)
    nodeCoreUse = sorted(nodeCoreUse)
    nodeNumServ = sorted(nodeNumServ)
    print("This is the number of devices used in multi_layer partiotioning:", num_node_usage)
    return nodeResUse, nodeNumServ, nodeStorUse, nodeCoreUse




def writeStatisticsAllocation(G,appsDeadlines, tempServiceAlloc, clientId, appId):

    for talloc_ in tempServiceAlloc.items():

        dist_ = nx.shortest_path_length(G, source=clientId, target=talloc_[1], weight="weight")

        mykey_ = dist_
        if mykey_ in statisticsDistancesRequest:
            statisticsDistancesRequest[mykey_] = statisticsDistancesRequest[mykey_] + 1
        else:
            statisticsDistancesRequest[mykey_] = 1

        mykey_ = talloc_[1]
        if mykey_ in statisticsNodesRequest:
            statisticsNodesRequest[mykey_] = statisticsNodesRequest[mykey_] + 1
        else:
            statisticsNodesRequest[mykey_] = 1

        mykey_ = (talloc_[1], talloc_[0])
        if mykey_ in statisticsNodesServices:
            statisticsNodesServices[mykey_] = statisticsNodesServices[mykey_] + 1
        else:
            statisticsNodesServices[mykey_] = 1

        mykey_ = (appsDeadlines[appId], dist_)
        if mykey_ in statisticsDistanceDeadline:
            statisticsDistanceDeadline[mykey_] = statisticsDistanceDeadline[mykey_] + 1
        else:
            statisticsDistanceDeadline[mykey_] = 1

        mykey_ = (talloc_[0], appsDeadlines[appId])
        if mykey_ in statisticsServiceInstances:
            statisticsServiceInstances[mykey_] = statisticsServiceInstances[mykey_] + 1
        else:
            statisticsServiceInstances[mykey_] = 1
statisticsCentralityResources = {}


def writeStatisticsDevices(G,devices,nodeBussyResources, centralityValuesNoOrdered, service2DevicePlacementMatrix):
    for devId in G.nodes:
        mypercentageResources_ = float(nodeBussyResources[devId]) / float(devices[devId]['RAM'])
        mycentralityValues_ = centralityValuesNoOrdered[devId]
        mykey_ = (mycentralityValues_, mypercentageResources_)
        if mykey_ in statisticsCentralityResources:
            statisticsCentralityResources[mykey_] = statisticsCentralityResources[mykey_] + 1
        else:
            statisticsCentralityResources[mykey_] = 1


statisticsResources = {}


def writeStatisticsDevices1(service2DevicePlacementMatrix,G,nodeBussyResources,nodeRAM):
    for devId in G.nodes:
        mypercentageResources_ = float(nodeBussyResources[devId]) / float(nodeRAM[devId])
        deviceId = devId
        mykey_ = (deviceId, mypercentageResources_)
        if mykey_ in statisticsResources:
            statisticsResources[mykey_] = statisticsResources[mykey_] + 1
        else:
            statisticsResources[mykey_] = 1

# **********************************************************************************************

# Functions for statistics of multilayer_community_detection without considering device failure

# **********************************************************************************************
# (deadline,shortestdistance):occurrences
statisticsDistanceDeadline_NF = {}
cpu_usage_NF = 0.0
# (service,deadline):occurrences
statisticsServiceInstances_NF = {}

# distance:numberOfuserThatRequest
statisticsDistancesRequest_NF = {}

# nodeid:numberOfuserThatRequest
statisticsNodesRequest_NF = {}

# (nodeid,serviceId):ocurrences
statisticsNodesServices_NF = {}

# (centrality,resources):occurrences
statisticsCentralityResources_NF = {}


def calculateNodeUsage_NF(service2DevicePlacementMatrix_NF, nodeRAM, nodeSTORAGE, CPUCore, nodeBussyResources_NF, nodeBussyStorage_NF,nodeBussyCore_NF):
    nodeResUse_NF = list()
    nodeStorUse_NF = list()
    nodeCoreUse_NF = list()
    nodeNumServ_NF = list()
    num_node_usage_NF = 0
    Resource_usage_NF = 0
    for i in service2DevicePlacementMatrix_NF[0]:
        nodeResUse_NF.append(0.0)
        nodeStorUse_NF.append(0.0)
        nodeCoreUse_NF.append(0.0)
        nodeNumServ_NF.append(0)

    for idServ in range(0, len(service2DevicePlacementMatrix_NF)):
        for idDev in range(0, len(service2DevicePlacementMatrix_NF[idServ])):
            if service2DevicePlacementMatrix_NF[idServ][idDev] == 1:
                nodeNumServ_NF[idDev] = nodeNumServ_NF[idDev] + 1
    for idDev in range(0, len(service2DevicePlacementMatrix_NF[0])):
        nodeResUse_NF[idDev] = nodeBussyResources_NF[idDev] / nodeRAM[idDev]
        Resource_usage_NF = Resource_usage_NF + nodeBussyResources_NF[idDev]
        nodeStorUse_NF[idDev] = nodeBussyStorage_NF[idDev] / nodeSTORAGE[idDev]
        nodeCoreUse_NF[idDev] = nodeBussyCore_NF[idDev] / CPUCore[idDev]
        if (nodeResUse_NF[idDev] != 0):
            num_node_usage_NF = num_node_usage_NF + 1
        # nodeResUse[idDev] = nodeBussyResources[idDev]
    nodeResUse_NF = sorted(nodeResUse_NF)
    nodeStorUse_NF = sorted(nodeStorUse_NF)
    nodeCoreUse_NF = sorted(nodeCoreUse_NF)
    nodeNumServ_NF = sorted(nodeNumServ_NF)
    print("This is the number of devices used in multi_layer partiotioning:", num_node_usage_NF)
    return nodeResUse_NF, nodeNumServ_NF, nodeStorUse_NF, nodeCoreUse_NF




def writeStatisticsAllocation_NF(G,appsDeadlines, tempServiceAlloc_NF, clientId, appId):

    for talloc_ in tempServiceAlloc_NF.items():

        dist_ = nx.shortest_path_length(G, source=clientId, target=talloc_[1], weight="weight")

        mykey_ = dist_
        if mykey_ in statisticsDistancesRequest_NF:
            statisticsDistancesRequest_NF[mykey_] = statisticsDistancesRequest_NF[mykey_] + 1
        else:
            statisticsDistancesRequest_NF[mykey_] = 1

        mykey_ = talloc_[1]
        if mykey_ in statisticsNodesRequest_NF:
            statisticsNodesRequest_NF[mykey_] = statisticsNodesRequest_NF[mykey_] + 1
        else:
            statisticsNodesRequest_NF[mykey_] = 1

        mykey_ = (talloc_[1], talloc_[0])
        if mykey_ in statisticsNodesServices_NF:
            statisticsNodesServices_NF[mykey_] = statisticsNodesServices_NF[mykey_] + 1
        else:
            statisticsNodesServices_NF[mykey_] = 1

        mykey_ = (appsDeadlines[appId], dist_)
        if mykey_ in statisticsDistanceDeadline_NF:
            statisticsDistanceDeadline_NF[mykey_] = statisticsDistanceDeadline_NF[mykey_] + 1
        else:
            statisticsDistanceDeadline_NF[mykey_] = 1

        mykey_ = (talloc_[0], appsDeadlines[appId])
        if mykey_ in statisticsServiceInstances_NF:
            statisticsServiceInstances_NF[mykey_] = statisticsServiceInstances_NF[mykey_] + 1
        else:
            statisticsServiceInstances_NF[mykey_] = 1
statisticsCentralityResources_NF = {}


def writeStatisticsDevices_NF(G,devices,nodeBussyResources_NF, centralityValuesNoOrdered_NF, service2DevicePlacementMatrix_NF):
    for devId in G.nodes:
        mypercentageResources_NF = float(nodeBussyResources_NF[devId]) / float(devices[devId]['RAM'])
        mycentralityValues_NF = centralityValuesNoOrdered_NF[devId]
        mykey_ = (mycentralityValues_NF, mypercentageResources_NF)
        if mykey_ in statisticsCentralityResources_NF:
            statisticsCentralityResources_NF[mykey_] = statisticsCentralityResources_NF[mykey_] + 1
        else:
            statisticsCentralityResources_NF[mykey_] = 1
statisticsResources_NF = {}


def writeStatisticsDevices1_NF(service2DevicePlacementMatrix_NF,G,nodeBussyResources_NF,nodeRAM):
    for devId in G.nodes:
        mypercentageResources_NF = float(nodeBussyResources_NF[devId]) / float(nodeRAM[devId])
        deviceId = devId
        mykey_ = (deviceId, mypercentageResources_NF)
        if mykey_ in statisticsResources_NF:
            statisticsResources_NF[mykey_] = statisticsResources_NF[mykey_] + 1
        else:
            statisticsResources_NF[mykey_] = 1




# **********************************************************************************************

# Functions for statistics of multilayer_community_detection with SOTA reputation policy

# **********************************************************************************************
# (deadline,shortestdistance):occurrences
statisticsDistanceDeadline_S = {}
cpu_usage_S = 0.0
# (service,deadline):occurrences
statisticsServiceInstances_S = {}

# distance:numberOfuserThatRequest
statisticsDistancesRequest_S = {}

# nodeid:numberOfuserThatRequest
statisticsNodesRequest_S = {}

# (nodeid,serviceId):ocurrences
statisticsNodesServices_S = {}

# (centrality,resources):occurrences
statisticsCentralityResources_S = {}


def calculateNodeUsage_S(service2DevicePlacementMatrix_S, nodeRAM, nodeSTORAGE, CPUCore, nodeBussyResources_S, nodeBussyStorage_S,nodeBussyCore_S):
    nodeResUse_S = list()
    nodeStorUse_S = list()
    nodeCoreUse_S = list()
    nodeNumServ_S = list()
    num_node_usage_S = 0
    Resource_usage_S = 0
    for i in service2DevicePlacementMatrix_S[0]:
        nodeResUse_S.append(0.0)
        nodeStorUse_S.append(0.0)
        nodeCoreUse_S.append(0.0)
        nodeNumServ_S.append(0)

    for idServ in range(0, len(service2DevicePlacementMatrix_S)):
        for idDev in range(0, len(service2DevicePlacementMatrix_S[idServ])):
            if service2DevicePlacementMatrix_S[idServ][idDev] == 1:
                nodeNumServ_S[idDev] = nodeNumServ_S[idDev] + 1
    for idDev in range(0, len(service2DevicePlacementMatrix_S[0])):
        nodeResUse_S[idDev] = nodeBussyResources_S[idDev] / nodeRAM[idDev]
        Resource_usage_S = Resource_usage_S + nodeBussyResources_S[idDev]
        nodeStorUse_S[idDev] = nodeBussyStorage_S[idDev] / nodeSTORAGE[idDev]
        nodeCoreUse_S[idDev] = nodeBussyCore_S[idDev] / CPUCore[idDev]
        if (nodeResUse_S[idDev] != 0):
            num_node_usage_S = num_node_usage_S + 1
        # nodeResUse[idDev] = nodeBussyResources[idDev]
    nodeResUse_S = sorted(nodeResUse_S)
    nodeStorUse_S = sorted(nodeStorUse_S)
    nodeCoreUse_S = sorted(nodeCoreUse_S)
    nodeNumServ_S = sorted(nodeNumServ_S)
    print("This is the number of devices used in multi_layer partiotioning:", num_node_usage_S)
    return nodeResUse_S, nodeNumServ_S, nodeStorUse_S, nodeCoreUse_S




def writeStatisticsAllocation_S(G,appsDeadlines, tempServiceAlloc_S, clientId, appId):

    for talloc_ in tempServiceAlloc_S.items():

        dist_ = nx.shortest_path_length(G, source=clientId, target=talloc_[1], weight="weight")

        mykey_ = dist_
        if mykey_ in statisticsDistancesRequest_S:
            statisticsDistancesRequest_S[mykey_] = statisticsDistancesRequest_S[mykey_] + 1
        else:
            statisticsDistancesRequest_S[mykey_] = 1

        mykey_ = talloc_[1]
        if mykey_ in statisticsNodesRequest_S:
            statisticsNodesRequest_S[mykey_] = statisticsNodesRequest_S[mykey_] + 1
        else:
            statisticsNodesRequest_S[mykey_] = 1

        mykey_ = (talloc_[1], talloc_[0])
        if mykey_ in statisticsNodesServices_S:
            statisticsNodesServices_S[mykey_] = statisticsNodesServices_S[mykey_] + 1
        else:
            statisticsNodesServices_S[mykey_] = 1

        mykey_ = (appsDeadlines[appId], dist_)
        if mykey_ in statisticsDistanceDeadline_S:
            statisticsDistanceDeadline_S[mykey_] = statisticsDistanceDeadline_S[mykey_] + 1
        else:
            statisticsDistanceDeadline_S[mykey_] = 1

        mykey_ = (talloc_[0], appsDeadlines[appId])
        if mykey_ in statisticsServiceInstances_S:
            statisticsServiceInstances_S[mykey_] = statisticsServiceInstances_S[mykey_] + 1
        else:
            statisticsServiceInstances_S[mykey_] = 1
statisticsCentralityResources_S = {}


def writeStatisticsDevices_S(G,devices,nodeBussyResources_S, centralityValuesNoOrdered_S, service2DevicePlacementMatrix_S):
    for devId in G.nodes:
        mypercentageResources_S = float(nodeBussyResources_S[devId]) / float(devices[devId]['RAM'])
        mycentralityValues_S = centralityValuesNoOrdered_S[devId]
        mykey_ = (mycentralityValues_S, mypercentageResources_S)
        if mykey_ in statisticsCentralityResources_S:
            statisticsCentralityResources_S[mykey_] = statisticsCentralityResources_S[mykey_] + 1
        else:
            statisticsCentralityResources_S[mykey_] = 1
statisticsResources_S = {}


def writeStatisticsDevices1_S(service2DevicePlacementMatrix_S,G,nodeBussyResources_S,nodeRAM):
    for devId in G.nodes:
        mypercentageResources_S = float(nodeBussyResources_S[devId]) / float(nodeRAM[devId])
        deviceId = devId
        mykey_ = (deviceId, mypercentageResources_S)
        if mykey_ in statisticsResources_S:
            statisticsResources_S[mykey_] = statisticsResources_S[mykey_] + 1
        else:
            statisticsResources_S[mykey_] = 1
# ****************************************************************************************************
# Generating application
# ****************************************************************************************************

def Generating_application(tt):
    numberOfServices = 0
    App1 = [[(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 5), (2, 3), (2, 5), (2, 6), (2, 7)],
            [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 5), (2, 3), (2, 5), (2, 6), (2, 7)],
            [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 5), (2, 3), (2, 5), (2, 6), (2, 7)],
            [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 5), (2, 3), (2, 5), (2, 6), (2, 7)],
            [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 5), (2, 3), (2, 5), (2, 6), (2, 7)],
            [(0, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 4), (3, 5), (4, 5), (5, 6)],
            [(0, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 4), (3, 5), (4, 5), (5, 6)],
            [(0, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 4), (3, 5), (4, 5), (5, 6)],
            [(0, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 4), (3, 5), (4, 5), (5, 6)],
            [(0, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 4), (3, 5), (4, 5), (5, 6)]
            ]
    sum = 0
    service = []
    Serviceset = []
    k=0
    for i in range(len(App1)):
        service = []
        if (k<5):
            for j in range(0, 8):
                service.append(sum)
                sum = sum + 1
        else:
            for j in range(0, 7):
                service.append(sum)
                sum = sum + 1
        Serviceset.append(service)
        k+=1
    print("This is the service set: ", Serviceset)

    """APP1_info = [{'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 0.5},

                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 2,
                  'RAM':2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'storage': 1, 'RAM':1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'RAM':1, 'MES_size': 5.5}
                 ]
"""
    APP1_info = [{'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 7610, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 7610, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 2,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'Avg-time': 0.052, 'requiredcpu': 7700,
                  'storage': 1, 'RAM': 1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 2,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'Avg-time': 0.052, 'requiredcpu': 7700,
                  'storage': 1, 'RAM': 1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 2,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'Avg-time': 0.052, 'requiredcpu': 7700,
                  'storage': 1, 'RAM': 1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 2,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'Avg-time': 0.052, 'requiredcpu': 7700,
                  'storage': 1, 'RAM': 1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 0, 'name': "Web-UI", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 1, 'name': "Login", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 2, 'name': "Orders", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 2,
                  'RAM': 2, 'MES_size': 0.5},
                 {'id': 3, 'name': "Shopping-cart", 'cpu': {'core_num': 4}, 'inst(MI)': 400, 'deadline': 0,
                  'Avg-time': 0.052, 'requiredcpu': 7700,
                  'storage': 1, 'RAM': 1, 'MES_size': 0.5},
                 {'id': 4, 'name': "Catalogue", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 5, 'name': "Accounts", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 6, 'name': "Payment", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0, 'Avg-time': 0.046,
                  'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},
                 {'id': 7, 'name': "Shipping", 'cpu': {'core_num': 4}, 'inst(MI)': 350, 'deadline': 0,
                  'Avg-time': 0.046, 'requiredcpu': 7610, 'storage': 1,
                  'RAM': 1, 'MES_size': 0.5},

                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'Avg-time': 0.34,
                  'requiredcpu': 17700, 'storage': 2,
                  'RAM': 2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'Avg-time': 0.57,
                  'requiredcpu': 24000, 'storage': 1,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'Avg-time': 0.3, 'requiredcpu': 12000,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'Avg-time': 0.34,
                  'requiredcpu': 17700, 'storage': 2,
                  'RAM': 2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'Avg-time': 0.57,
                  'requiredcpu': 24000, 'storage': 1,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'Avg-time': 0.3, 'requiredcpu': 12000,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'Avg-time': 0.34,
                  'requiredcpu': 17700, 'storage': 2,
                  'RAM': 2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'Avg-time': 0.57,
                  'requiredcpu': 24000, 'storage': 1,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'Avg-time': 0.3, 'requiredcpu': 12000,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'Avg-time': 0.34,
                  'requiredcpu': 17700, 'storage': 2,
                  'RAM': 2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'Avg-time': 0.57,
                  'requiredcpu': 24000, 'storage': 1,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'Avg-time': 0.3, 'requiredcpu': 12000,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 0, 'name': "Encode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'Avg-time': 0.34,
                  'requiredcpu': 17700, 'storage': 2,
                  'RAM': 2, 'MES_size': 2.5},
                 {'id': 1, 'name': "Frame", 'cpu': {'core_num': 4}, 'inst(MI)': 13500, 'deadline': 0, 'Avg-time': 0.57,
                  'requiredcpu': 24000, 'storage': 1,
                  'RAM': 1, 'MES_size': 5.5},
                 {'id': 2, 'name': "Low-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 3, 'name': "High-accuracy-train", 'cpu': {'core_num': 4}, 'inst(MI)': 0, 'deadline': 0,
                  'Avg-time': 5000, 'requiredcpu': 7610,
                  'storage': 2, 'RAM': 4, 'MES_size': 5.5},
                 {'id': 4, 'name': "High-accuracy-inference", 'cpu': {'core_num': 4}, 'inst(MI)': 3500, 'deadline': 0,
                  'Avg-time': 0.3, 'requiredcpu': 12000,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 5, 'name': "Transcode", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'storage': 1, 'RAM': 1, 'MES_size': 5.5},
                 {'id': 6, 'name': "Package", 'cpu': {'core_num': 4}, 'inst(MI)': 6000, 'deadline': 0, 'storage': 1,
                  'Avg-time': 0.34, 'requiredcpu': 17700,
                  'RAM': 1, 'MES_size': 5.5},

                 ]
    apps = list()
    appsDeadlines = {}
    appsResources = list()
    appsReqcpu = list()
    appstorage = list()
    appsSourceService = list()
    appsSourceMessage = list()
    appsTotalMIPS = list()
    mapService2App = list()
    mapServiceId2ServiceName = list()
    appsSourceMessage1 = list()
    mapService2App1 = list()
    mapServiceId2ServiceName1 = list()
    appsCommunities = list()
    service_name = list()
    service_inst = list()
    appJson = list()
    appJson1 = list()
    servicesResources = {}
    servicesStorage = {}
    servicesreqcpu = {}
    serviceTotalMIPS = {}
    service_in = {}
    service_out = {}
    APP11=[]
    for i in range(10):
        myApp = {}
        mylabels = {}

        APP = nx.DiGraph()
        print(App1[i])
        APP.add_edges_from(App1[i])
        APP11.append(APP)
        for n in range(0, len(APP.nodes)):
            mylabels[n] = str(n)
        edgeList_ = list()
        for m in APP.edges:
            edgeList_.append(m)
        """"for m in edgeList_:
            APP.remove_edge(m[0], m[1])
            APP.add_edge(m[1], m[0])"""


        mapping = dict(zip(APP.nodes(), range(numberOfServices, numberOfServices + len(APP.nodes))))
        APP = nx.relabel_nodes(APP, mapping)


        numberOfServices = numberOfServices + len(APP.nodes)
        apps.append(APP)
        for j in APP.nodes:
            servicesResources[j] = APP1_info[j]['RAM']
            servicesStorage[j] = APP1_info[j]['storage']
            servicesreqcpu[j] = APP1_info[j]['requiredcpu']
            serviceTotalMIPS[j] = 0.0
            service_in[j] = 0.0
            service_out[j] = 0.0
        appsReqcpu.append(servicesreqcpu)
        appsResources.append(servicesResources)
        appstorage.append(servicesStorage)

        topologicorder_ = list(nx.topological_sort(APP))
        source = topologicorder_[0]
        source=Serviceset[i][0]

        #appsCommunities.append(transitiveClosureCalculation(source, APP))
        #transitiveClosureCalculation(source, APP)

        appsSourceService.append(source)
        print("source", appsSourceService)
        appsDeadlines[i] = APPDEADLINE[i]
        myApp['id'] = i
        myApp['name'] = str(i)
        myApp['deadline'] = appsDeadlines[i]

        myApp['module'] = list()

        edgeNumber = 0
        myApp['message'] = list()

        myApp['transmission'] = list()

        totalMIPS = 0
        SERVICEINSTR1 = []
        SERVICEMESSAGESIZE1 = []

        for n in APP.nodes:

            mapService2App.append(str(i))
            mapServiceId2ServiceName.append(str(i) + '_' + str(n))
            myNode = {}
            myNode['id'] = n
            myNode['name'] = str(i) + '_' + str(n)
            myNode['RAM'] = servicesResources[n]
            myNode['storage'] = servicesStorage[n]
            myNode['type'] = 'MODULE'
            myNode['INST'] = APP1_info[n]['inst(MI)']
            myNode['requiredcpu'] = APP1_info[n]['requiredcpu']

            #print("HellooZara")


            if source == n:
                myEdge = {}
                myEdge['id'] = edgeNumber
                edgeNumber = edgeNumber + 1
                myEdge['name'] = "M.USER.APP." + str(i)
                myEdge['s'] = "None"
                myEdge['d'] = str(i) + '_' + str(n)
                #print("HellooZara3",n)

                #myEdge['reqcpu'] = APP1_info[n]['requiredcpu']
                myEdge['instructions'] = APP1_info[n]['inst(MI)']
                SERVICEINSTR1.append(myEdge['instructions'])
                myEdge['instructions'] = myNode['INST']
                totalMIPS = totalMIPS + myEdge['instructions']
                myEdge['bytes'] = APP1_info[n]['MES_size']
                SERVICEMESSAGESIZE1.append(myEdge['bytes'])
                myApp['message'].append(myEdge)
                appsSourceMessage.append(myEdge)

                for o in APP.edges:
                    if o[0] == source:
                        myTransmission = {}
                        myTransmission['module'] = str(i) + '_' + str(source)
                        myTransmission['message_in'] = "M.USER.APP." + str(i)
                        myTransmission['message_out'] = str(i) + '_(' + str(o[0]) + "-" + str(o[1]) + ")"
                        myApp['transmission'].append(myTransmission)

            myApp['module'].append(myNode)

        for n in APP.edges:
            myEdge = {}
            myEdge['id'] = edgeNumber
            edgeNumber = edgeNumber + 1
            myEdge['name'] = str(i) + '_(' + str(n[0]) + "-" + str(n[1]) + ")"
            myEdge['s'] = str(i) + '_' + str(n[0])
            myEdge['d'] = str(i) + '_' + str(n[1])
            #print("HellooZara2",n)
            #myEdge['reqcpu'] = APP1_info[n]['requiredcpu']
            myEdge['instructions'] = APP1_info[n[0]]['inst(MI)']
            SERVICEINSTR1.append(myEdge['instructions'])
            totalMIPS = totalMIPS + myEdge['instructions']
            myEdge['bytes'] = APP1_info[n[0]]['MES_size']
            SERVICEMESSAGESIZE1.append(myEdge['bytes'])
            myApp['message'].append(myEdge)
            destNode = n[1]
            for o in APP.edges:
                if o[0] == destNode:
                    myTransmission = {}
                    myTransmission['module'] = str(i) + '_' + str(n[1])
                    myTransmission['message_in'] = str(i) + '_(' + str(n[0]) + "-" + str(n[1]) + ")"
                    myTransmission['message_out'] = str(i) + '_(' + str(o[0]) + "-" + str(o[1]) + ")"
                    myApp['transmission'].append(myTransmission)

        for n in APP.nodes:
            outgoingEdges = False
            for m in APP.edges:
                if m[0] == n:
                    outgoingEdges = True
                    break
            if not outgoingEdges:
                for m in APP.edges:
                    if m[1] == n:
                        myTransmission = {}
                        myTransmission['module'] = str(i) + '_' + str(n)
                        myTransmission['message_in'] = str(i) + '_(' + str(m[0]) + "-" + str(m[1]) + ")"
                        myApp['transmission'].append(myTransmission)
        appsTotalMIPS.append(totalMIPS)
        myApp['appsTotalMIPS'] = totalMIPS

        messages = myApp['message']
        modules = myApp['module']
        for n in range(len(messages)):
            service_name.append(messages[n]['d'])
            service_inst.append(messages[n]['instructions'])
        for j in range(len(modules)):
            for n in range(len(service_name)):
                if service_name[n] == modules[j]['name']:
                    modules[j]['INST'] = modules[j]['INST'] + service_inst[n]
            myApp['module'][j]['INST'] = modules[j]['INST']

        appJson.append(myApp)


        app_file = "appDefinition" + str(tt) + ".json"
        file = open(app_file, "w")
        file.write(json.dumps(appJson))
        file.close()


    #return numberOfServices,Serviceset, apps, appsDeadlines, appsResources, appstorage, appsSourceMessage, appsTotalMIPS, mapService2App, mapServiceId2ServiceName, appsCommunities, servicesResources
    return numberOfServices, Serviceset, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName



    #return numberOfServices, service_set, appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName


def weightNetwork(appsSourceMessage,appId, G):
    size = float(appsSourceMessage[appId]['bytes'])
    for e in G.edges:
        G[e[0]][e[1]]['weight'] = float(G[e[0]][e[1]]['PR']) + (size / float(G[e[0]][e[1]]['BW']))


def weightNetwork1(G):
    size = float(1)
    for e in G.edges:
        G[e[0]][e[1]]['weight'] = float(G[e[0]][e[1]]['PR']) + (size / float(G[e[0]][e[1]]['BW']))


def comm_attribute1(Fog_resources, partitions, network_size):
    cpu_core = []
    cpu_cache = []
    cpu_speed = []
    storage = []
    RAM = []
    flag = []
    community_info = []


    for nodes in range(network_size):
        flag.append('false')


    for i in range(len(partitions)):
        for j in range(len(partitions[i])):
            sum_cpu_core = 0
            sum_cpu_cache = 0
            sum_cpu_speed = 0
            sum_storage = 0
            sum_ram = 0
            comm_node = 0
            comm_member = []

            for nodes in range(network_size):
                flag[nodes] = 'false'
            for k in range(len(partitions[i][j])):
                #print(partitions[i][j][k])
                d = partitions[i][j][k] % network_size
                #print(partitions[i][j][k])
                if (flag[d] == 'false'):
                    comm_node = comm_node + 1
                    comm_member.append(d)
                    sum_cpu_core = Fog_resources[d]['cpu']['core_num'] + sum_cpu_core
                    sum_cpu_cache = Fog_resources[d]['cpu']['cache'] + sum_cpu_cache
                    sum_cpu_speed = Fog_resources[d]['cpu']['speed'] + sum_cpu_speed
                    sum_storage = Fog_resources[d]['storage'] + sum_storage
                    sum_ram = Fog_resources[d]['RAM'] + sum_ram
                    flag[d] = 'true'

            cpu_core.append(sum_cpu_core / comm_node)
            cpu_cache.append(sum_cpu_cache / comm_node)
            cpu_speed.append(sum_cpu_speed / comm_node)
            storage.append(sum_storage / comm_node)
            RAM.append(sum_ram / comm_node)
            community_info.append({'Id': j, 'member': comm_member,
                                   'cpu': {'core_num': cpu_core[j], 'cache': cpu_cache[j], 'speed': cpu_speed[j]},
                                   'RAM': RAM[j], 'storage': storage[j]})

    print("The Fog communities based on their features:     ", community_info)
    return community_info


# ****************************************************************************************************

# Second-level #Placement (services to devices) using communities

# ****************************************************************************************************


def sim_com_module(G, Fog_community, requiredcpu, requiredRAM, requiredStrorage, pre_device, A, clientId):
    sim = []
    pre_device = -1
    for j in range(len(Fog_community)):

        device_id = Fog_community[j]['member']
        netTime = {}
        for devId in device_id:
            if nx.has_path(G, source=clientId, target=devId) == True:
                if (pre_device == -1):
                    netTime[devId] = nx.shortest_path_length(G, source=clientId, target=devId,
                                                             weight="weight")  # network time between client and device
                else:
                    netTime[devId] = nx.shortest_path_length(G, source=pre_device, target=devId,
                                                             weight="weight")  # network time between client and device
            else:

                netTime[devId] = 10000000000

        sorted_ = sorted(netTime.items(), key=operator.itemgetter(1))

        sortedList = list()

        for i in sorted_:
            sortedList.append(i[1])

        delay = 1 / (1 + sortedList[0])


        simRAM = Similaritymeasurment.Euclidean_similarity(
            [requiredRAM], [Fog_community[j]['RAM']])
        simCPU = Similaritymeasurment.Euclidean_similarity(
            [requiredcpu], [Fog_community[j]['cpu']['speed']])
        simStorage = Similaritymeasurment.Euclidean_similarity(
            [requiredStrorage] , [Fog_community[j]['storage']])
        sim.append(simRAM + simCPU + simStorage)
        sim[j] = A * sim[j] + (1 / math.sqrt(A)) * delay


    return sim


def check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage, available_RAM, available_CPUCore):
    allocating = False

    if (available_RAM >= requiredRAM):
        if (available_Storage >= requiredStrorage):
            if (available_CPUCore >= 1):
                allocating = True

    return allocating


def map_com_NF(G, comm, requiredcpu, requiredRAM, requiredStrorage, clientId, available_Storage, available_RAM,
            available_CPUCore):
    mapped = -1
    sim = []
    path = True
    sorted_sim = []
    device_id = comm['member']
    netTime = {}
    for devId in device_id:
        if nx.has_path(G, source=clientId, target=devId) == True:
            netTime[devId] = nx.shortest_path_length(G, source=clientId, target=devId,
                                                     weight="weight")  # network time between client and device
        else:
            netTime[devId] = -1
            print("There is no path from device ", devId, "to device", clientId)
    sorted_ = sorted(netTime.items(), key=operator.itemgetter(1))

    sortedList = list()

    for i in sorted_:
        sortedList.append(i[0])

    for i in sortedList:
        device_id = i
        if netTime[i] != -1:
            # print("There is no path from device",i, "to the device", clientId )

            allocat = check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage[device_id],
                                available_RAM[device_id], available_CPUCore[device_id])
            if (allocat):
                # available_cpu_speed[device_id] = available_cpu_speed[device_id] - requiredRAM
                # available_storage[device_id] = available_storage[device_id] - requiredStrorage
                # available_RAM[device_id] = available_RAM[device_id] - requiredRAM
                mapped = device_id
                break

    return mapped

def map_com(G, comm,topo_mem, SLAPar_info, requiredcpu, requiredRAM, requiredStrorage, clientId, available_Storage, available_RAM,
            available_CPUCore):
    mapped = -1

    device_id = comm['member']
    netTime = {}
    for devId in device_id:
        if nx.has_path(G, source=clientId, target=devId) == True:
            netTime[devId] = nx.shortest_path_length(G, source=clientId, target=devId,
                                                     weight="weight")  # network time between client and device
        else:
            netTime[devId] = -1
            print("There is no path from device ", devId, "to device", clientId)
    sorted_ = sorted(netTime.items(), key=operator.itemgetter(1))

    sortedList = list()

    for i in sorted_:
        sortedList.append(i[0])
    #topo_id=topo_mem[sortedList[0]]

    for i in sortedList:
        topo_id = topo_mem[i]
        #print(topo_id)
        #print(SLAPar_info)
        #print("Topo_mem", topo_mem)
        #print("length",len(SLAPar_info))
        for SP in range(len(SLAPar_info[topo_id])):
            if SLAPar_info[topo_id][SP]['SLAValue']> 0.6:
                mem=SLAPar_info[topo_id][SP]['member']
                netTime = {}
                for devId in mem:
                    if nx.has_path(G, source=clientId, target=devId) == True:
                        netTime[devId] = nx.shortest_path_length(G, source=clientId, target=devId,
                                                                 weight="weight")  # network time between client and device
                    else:
                        netTime[devId] = -1
                        print("There is no path from device ", devId, "to device", clientId)
                sortedmem = sorted(netTime.items(), key=operator.itemgetter(1))
                sortedmemList=list()
                for i in sortedmem:
                    sortedmemList.append(i[0])
                for i in sortedmemList:
                    if i in comm['member']:
                        device_id = i
                        if netTime[i] != -1:
                            allocat = check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage[device_id],
                                                available_RAM[device_id], available_CPUCore[device_id])
                            if (allocat):
                                mapped = device_id
                                return mapped
    return mapped
def map_com_SOTA(G, comm,topo_mem, SLA_info, requiredcpu, requiredRAM, requiredStrorage, clientId, available_Storage, available_RAM,
            available_CPUCore):
    mapped = -1

    device_id = comm['member']
    netTime = {}
    for devId in device_id:
        if nx.has_path(G, source=clientId, target=devId) == True:
            netTime[devId] = nx.shortest_path_length(G, source=clientId, target=devId,
                                                     weight="weight")  # network time between client and device
        else:
            netTime[devId] = -1
            print("There is no path from device ", devId, "to device", clientId)
    sorted_ = sorted(netTime.items(), key=operator.itemgetter(1))

    sortedList = list()

    for i in sorted_:
        sortedList.append(i[0])
    #topo_id=topo_mem[sortedList[0]]
    id=[]
    for device_id in sortedList:

        for d in range(len(SLA_info)):
            id.append(SLA_info[d]['id'])
            #print("devices with high SLA value:",id)
        if device_id in id:
            allocat = check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage[device_id],
                                available_RAM[device_id], available_CPUCore[device_id])
            if (allocat):
                mapped = device_id
                return mapped
    return mapped


def comm_update(device_id,Fog_resources, community):
    updated_mem = []
    updated_info = []
    node_num = len(community['member'])
    com_mem = community['member']
    for i in range(len(community['member'])):
        if (com_mem[i] != device_id):
            updated_mem.append(com_mem[i])

    sum_cpu_core = community['cpu']['core_num'] * node_num
    sum_cpu_cache = community['cpu']['cache'] * node_num
    sum_cpu_speed = community['cpu']['speed'] * node_num
    sum_up_bw = community['network']['up_Bw'] * node_num
    sum_down_bw = community['network']['down_Bw'] * node_num
    sum_storage = community['storage'] * node_num
    sum_ram = community['RAM'] * node_num

    cpu_core = (sum_cpu_core - Fog_resources[device_id]['cpu']['core_num']) / (node_num - 1)
    cpu_cache = (sum_cpu_cache - Fog_resources[device_id]['cpu']['cache']) / (node_num - 1)
    cpu_speed = (sum_cpu_speed - Fog_resources[device_id]['cpu']['speed']) / (node_num - 1)
    up_bw = (sum_up_bw - Fog_resources[device_id]['network']['up_Bw']) / (node_num - 1)
    down_bw = (sum_down_bw - Fog_resources[device_id]['network']['down_Bw']) / (node_num - 1)
    storage = (sum_storage - Fog_resources[device_id]['storage']) / (node_num - 1)
    RAM = (sum_ram - Fog_resources[device_id]['RAM']) / (node_num - 1)

    updated_info.append(
        {'Id': community['Id'], 'member': updated_mem,
         'cpu': {'core_num': cpu_core, 'cache': cpu_cache, 'speed': cpu_speed},
         'network': {'up_Bw': up_bw, 'down_Bw': down_bw}, 'RAM': RAM})

    return updated_info


def topo_comm_tag(device, Fog_comm, topo_com):
    device_tags = []
    topo_num = np.zeros(len(Fog_comm))
    topology_inf = []
    sorted_topo_inf = []
    for k in range(len(device)):
        for i in range(len(Fog_comm)):
            if (i >= topo_com[0]):

                for j in range(len(Fog_comm[i]['member'])):
                    if (Fog_comm[i]['member'][j] == device[k]['device_id']):
                        topo_tag = i
                        device_tags.append(
                            {'device_id': device[k]['device_id'], 'feat_comm_id': device[k]['community_Id'],
                             'topo_comm_id': topo_tag})
                        topo_num[i] = topo_num[i] + 1

    for i in range(len(Fog_comm)):
        topology_inf.append({'topo_com_id': i, 'count': topo_num[i]})

    for sorted_inf in sorted(topology_inf, key=operator.itemgetter("count"), reverse=True):
        sorted_topo_inf.append(sorted_inf)

    return device_tags


# ****************************************************************************************************
# Generation of IoT devices (users) that request each application
# ****************************************************************************************************

def request_generation(t, gatewaysDevices):
    userJson = {}
    myUsers = list()
    appsRequests = list()

    for i in range(0, TOTALNUMBEROFAPPS):
        userRequestList = set()
        probOfRequested = eval(func_REQUESTPROB)
        atLeastOneAllocated = False
        for j in gatewaysDevices:
            if random.random() < probOfRequested:
                myOneUser = {}
                myOneUser['app'] = str(i)
                myOneUser['message'] = "M.USER.APP." + str(i)
                myOneUser['id_resource'] = j
                myOneUser['lambda'] = eval(func_USERREQRAT)
                userRequestList.add(j)
                myUsers.append(myOneUser)
                atLeastOneAllocated = True
        if not atLeastOneAllocated:
            j = random.randint(0, len(gatewaysDevices) - 1)
            myOneUser = {}
            myOneUser['app'] = str(i)
            myOneUser['message'] = "M.USER.APP." + str(i)
            myOneUser['id_resource'] = j
            myOneUser['lambda'] = eval(func_USERREQRAT)
            userRequestList.add(j)
            myUsers.append(myOneUser)
        appsRequests.append(userRequestList)

    userJson['sources'] = myUsers
    req_file = "usersDefinition" + str(t) + ".json"
    file = open(req_file, "w")
    file.write(json.dumps(userJson))
    file.close()
    return appsRequests, myUsers


# ****************************************************************************************************

# Multilayer placement without any failure

# ****************************************************************************************************

def Multilayerplacement_NF(tt,G,devices,topo_mem,topo_par,Fog_community,gatewaysDevices,centralityValuesNoOrdered, numberOfServices, service_set,appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests):
    cloudId = 1000
    FOG_DEVICES = []

    print("this is the gateway devices in time window: ", tt, gatewaysDevices)
    with open("networkDefinition.json", "r") as json_file:
        content = json.load(json_file)
    Fog_resources = content['entity']
    network_size = (len(Fog_resources)) - 1
    FOG_DEVICES.append(Fog_resources)
    available_cpu_speed_NF = {}
    available_Storage_NF = {}
    available_CPUCore_NF = {}
    available_RAM_NF = {}
    nodeBussy_cpu_speed_NF = {}
    nodeBussy_RAM_NF = {}

    for device_id in range(network_size):
        nodeBussy_cpu_speed_NF[device_id] = 0.0
        nodeBussy_RAM_NF[device_id] = 0.0
        available_cpu_speed_NF[device_id] = (Fog_resources[device_id]['cpu']['speed'])
        available_RAM_NF[device_id] = Fog_resources[device_id]['RAM']
        available_Storage_NF[device_id] = Fog_resources[device_id]['storage']
        available_CPUCore_NF[device_id] = Fog_resources[device_id]['cpu']['core_num']


    service2DevicePlacementMatrix_NF = [[0 for j in range(len(G.nodes))] for i in range(numberOfServices)]

    nodeBussyResources_NF = {}
    for i in G.nodes:
        nodeBussyResources_NF[i] = 0.0

    nodeBussyStorage_NF = {}
    for i in G.nodes:
        nodeBussyStorage_NF[i] = 0.0

    nodeBussyCore_NF = {}
    for i in G.nodes:
        nodeBussyCore_NF[i] = 0.0

    app_file = "appDefinition0.json"
    with open(app_file, "r") as json_file:
        content_app = json.load(json_file)
    sortedAppsDeadlines = sorted(appsDeadlines.items(), key=operator.itemgetter(1))
    print("Starting Multi_layer placement policy without considering failure in time window", tt, " .....")
    App_num = 0
    Service_num = 0
    App_req_num = 0
    cpu_usage = 0.0
    #t = time.time()

    for appToAllocate in sortedAppsDeadlines:
        App_num = App_num + 1
        appId = appToAllocate[0]
        weightNetwork(appsSourceMessage,appId, G)
        nodesWithClients = appsRequests[appId]
        for clientId in nodesWithClients:
            App_req_num = App_req_num + 1
            requiredStrorage1 = 0.0
            requiredRAM1 = 0.0
            requiredcpu1 = 0.0
            alloc_devices = []
            serset_id = 0
            device_id = -1

            modules = content_app[appId]['module']
            App_deadline = content_app[appId]['deadline']
            A = App_deadline / 10000
            App_size = (len(modules))  # the number of modules in one app
            tempServiceAlloc_NF = {}
            for i in range(App_size):
                requiredcpu1 = requiredcpu1 + modules[i]['requiredcpu']
                requiredStrorage1 = requiredStrorage1 + modules[i]['storage']
                requiredRAM1 = requiredRAM1 + modules[i]['RAM']
                Service_num = Service_num + 1
            ser_id = 0
            for serviceSet in service_set[appId]:
                requiredStrorage = 0.0
                requiredRAM = 0.0
                requiredcpu = 0.0
                requiredcpu = requiredcpu + modules[ser_id]['requiredcpu']
                requiredStrorage = requiredStrorage + modules[ser_id]['storage']
                requiredRAM = requiredRAM + modules[ser_id]['RAM']
                ser_id = ser_id + 1


                if (device_id != -1):
                    placed = check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage_NF[device_id],
                                       available_RAM_NF[device_id], available_CPUCore_NF[device_id])
                    if (placed):
                        alloc_devices.append({'device_id': device_id, 'community_Id': comm_id})
                        tempServiceAlloc_NF[serviceSet] = device_id
                        service2DevicePlacementMatrix_NF[serviceSet][device_id] = 1
                        Overload = False
                        nodeBussy_cpu_speed_NF[device_id] = nodeBussy_cpu_speed_NF[device_id] + requiredcpu
                        nodeBussy_RAM_NF[device_id] = nodeBussy_RAM_NF[device_id] + requiredRAM
                        nodeBussyResources_NF[device_id] = nodeBussyResources_NF[device_id] + requiredRAM
                        nodeBussyStorage_NF[device_id] = nodeBussyStorage_NF[device_id] + requiredStrorage
                        nodeBussyCore_NF[device_id] = nodeBussyCore_NF[device_id] + 1
                        available_RAM_NF[device_id] = available_RAM_NF[device_id] - requiredRAM
                        available_Storage_NF[device_id] = available_Storage_NF[device_id] - requiredStrorage
                        available_CPUCore_NF[device_id] = available_CPUCore_NF[device_id] - 1
                        serset_id = serset_id + 1
                        requiredcpu1 = requiredcpu1 - requiredcpu
                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                        requiredRAM1 = requiredRAM1 - requiredRAM
                    else:
                        similarity = sim_com_module(G,Fog_community, requiredcpu, requiredRAM, requiredStrorage,
                                                    device_id, A, clientId)
                        community = []
                        sorted_comm = []

                        for j in range(len(Fog_community)):
                            community.append({'comm_id': j, 'sim_value': similarity[j]})

                        for sorted_com in sorted(community, key=operator.itemgetter("sim_value"), reverse=True):
                            sorted_comm.append(sorted_com)

                        for j in range(len(sorted_comm)):
                            comm_id = sorted_comm[j]['comm_id']
                            overlapp = True

                            if (overlapp):

                                device_id = map_com_NF(G, Fog_community[comm_id], requiredcpu, requiredRAM, requiredStrorage, clientId, available_Storage_NF,
                                 available_RAM_NF,available_CPUCore_NF)
                                # after finishing the task every thing (used fog node) should come back to it's first step before updatathing
                                if (device_id != -1):
                                    alloc_devices.append({'device_id': device_id, 'community_Id': comm_id})

                                    if (serset_id == 0):
                                        topology_com_id0 = topo_mem[device_id]
                                        service2DevicePlacementMatrix_NF[serviceSet][device_id] = 1
                                        tempServiceAlloc_NF[serviceSet] = device_id
                                        nodeBussy_RAM_NF[device_id] = nodeBussy_RAM_NF[device_id] + requiredRAM
                                        nodeBussyResources_NF[device_id] = nodeBussyResources_NF[device_id] + requiredRAM
                                        nodeBussyStorage_NF[device_id] = nodeBussyStorage_NF[device_id] + requiredStrorage
                                        nodeBussyCore_NF[device_id] = nodeBussyCore_NF[device_id] + 1
                                        available_RAM_NF[device_id] = available_RAM_NF[device_id] - requiredRAM
                                        available_Storage_NF[device_id] = available_Storage_NF[device_id] - requiredStrorage
                                        available_CPUCore_NF[device_id] = available_CPUCore_NF[device_id] - 1
                                        serset_id = serset_id + 1
                                        requiredcpu1 = requiredcpu1 - requiredcpu
                                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                        requiredRAM1 = requiredRAM1 - requiredRAM
                                        break
                                    else:
                                        topology_com_id1 = topo_mem[device_id]
                                        if (topology_com_id1 == topology_com_id0):
                                            service2DevicePlacementMatrix_NF[serviceSet][device_id] = 1
                                            tempServiceAlloc_NF[serviceSet] = device_id
                                            nodeBussy_cpu_speed_NF[device_id] = nodeBussy_cpu_speed_NF[
                                                                                 device_id] + requiredcpu
                                            nodeBussy_RAM_NF[device_id] = nodeBussy_RAM_NF[device_id] + requiredRAM
                                            nodeBussyResources_NF[device_id] = nodeBussyResources_NF[device_id] + requiredRAM
                                            nodeBussyStorage_NF[device_id] = nodeBussyStorage_NF[device_id] + requiredStrorage
                                            nodeBussyCore_NF[device_id] = nodeBussyCore_NF[device_id] + 1
                                            available_RAM_NF[device_id] = available_RAM_NF[device_id] - requiredRAM
                                            available_Storage_NF[device_id] = available_Storage_NF[
                                                                               device_id] - requiredStrorage
                                            available_CPUCore_NF[device_id] = available_CPUCore_NF[device_id] - 1
                                            serset_id = serset_id + 1
                                            requiredcpu1 = requiredcpu1 - requiredcpu
                                            requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                            requiredRAM1 = requiredRAM1 - requiredRAM
                                            break
                else:
                    similarity = sim_com_module(G, Fog_community, requiredcpu, requiredRAM, requiredStrorage, device_id,
                                                A, clientId)
                    community = []
                    sorted_comm = []

                    for j in range(len(Fog_community)):
                        community.append({'comm_id': j, 'sim_value': similarity[j]})
                    for sorted_com in sorted(community, key=operator.itemgetter("sim_value"), reverse=True):
                        sorted_comm.append(sorted_com)

                    for j in range(len(sorted_comm)):
                        comm_id = sorted_comm[j]['comm_id']
                        overlapp = True

                        if (overlapp):

                            device_id = map_com_NF(G, Fog_community[comm_id], requiredcpu, requiredRAM, requiredStrorage, clientId, available_Storage_NF,
                                 available_RAM_NF,available_CPUCore_NF)

                            if (device_id != -1):
                                alloc_devices.append({'device_id': device_id, 'community_Id': comm_id})

                                if (serset_id == 0):
                                    topology_com_id0 = topo_mem[device_id]
                                    tempServiceAlloc_NF[serviceSet] = device_id
                                    service2DevicePlacementMatrix_NF[serviceSet][device_id] = 1
                                    nodeBussy_RAM_NF[device_id] = nodeBussy_RAM_NF[device_id] + requiredRAM
                                    nodeBussyResources_NF[device_id] = nodeBussyResources_NF[device_id] + requiredRAM
                                    nodeBussyStorage_NF[device_id] = nodeBussyStorage_NF[device_id] + requiredStrorage
                                    nodeBussyCore_NF[device_id] = nodeBussyCore_NF[device_id] + 1
                                    available_RAM_NF[device_id] = available_RAM_NF[device_id] - requiredRAM
                                    available_Storage_NF[device_id] = available_Storage_NF[device_id] - requiredStrorage
                                    available_CPUCore_NF[device_id] = available_CPUCore_NF[device_id] - 1
                                    serset_id = serset_id + 1
                                    requiredcpu1 = requiredcpu1 - requiredcpu
                                    requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                    requiredRAM1 = requiredRAM1 - requiredRAM
                                    break
                                else:
                                    topology_com_id1 = topo_mem[device_id]
                                    if (topology_com_id1 == topology_com_id0):
                                        tempServiceAlloc_NF[serviceSet] = device_id
                                        service2DevicePlacementMatrix_NF[serviceSet][device_id] = 1
                                        nodeBussy_cpu_speed_NF[device_id] = nodeBussy_cpu_speed_NF[device_id] + requiredcpu
                                        nodeBussy_RAM_NF[device_id] = nodeBussy_RAM_NF[device_id] + requiredRAM
                                        nodeBussyResources_NF[device_id] = nodeBussyResources_NF[device_id] + requiredRAM
                                        nodeBussyStorage_NF[device_id] = nodeBussyStorage_NF[device_id] + requiredStrorage
                                        nodeBussyCore_NF[device_id] = nodeBussyCore_NF[device_id] + 1
                                        available_RAM_NF[device_id] = available_RAM_NF[device_id] - requiredRAM
                                        available_Storage_NF[device_id] = available_Storage_NF[device_id] - requiredStrorage
                                        available_CPUCore_NF[device_id] = available_CPUCore_NF[device_id] - 1
                                        serset_id = serset_id + 1
                                        requiredcpu1 = requiredcpu1 - requiredcpu
                                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                        requiredRAM1 = requiredRAM1 - requiredRAM
                                        break



# ****************************************************************************************************

# Multilayer placement

# ****************************************************************************************************

def Multilayerplacement(tt,G,devices,topo_mem,topo_par,Fog_community,SLAPar_info,gatewaysDevices,centralityValuesNoOrdered, numberOfServices, service_set,appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests):
    cloudId = 1000
    FOG_DEVICES = []

    print("this is the gateway devices in time window: ", tt, gatewaysDevices)
    with open("networkDefinition.json", "r") as json_file:
        content = json.load(json_file)
    Fog_resources = content['entity']
    network_size = (len(Fog_resources)) - 1
    FOG_DEVICES.append(Fog_resources)
    available_cpu_speed = {}
    available_Storage = {}
    available_CPUCore = {}
    available_RAM = {}
    nodeBussy_cpu_speed = {}
    nodeBussy_RAM = {}

    for device_id in range(network_size):
        nodeBussy_cpu_speed[device_id] = 0.0
        nodeBussy_RAM[device_id] = 0.0
        available_cpu_speed[device_id] = (Fog_resources[device_id]['cpu']['speed'])
        available_RAM[device_id] = Fog_resources[device_id]['RAM']
        available_Storage[device_id] = Fog_resources[device_id]['storage']
        available_CPUCore[device_id] = Fog_resources[device_id]['cpu']['core_num']


    service2DevicePlacementMatrix = [[0 for j in range(len(G.nodes))] for i in range(numberOfServices)]

    nodeBussyResources = {}
    for i in G.nodes:
        nodeBussyResources[i] = 0.0

    nodeBussyStorage = {}
    for i in G.nodes:
        nodeBussyStorage[i] = 0.0

    nodeBussyCore = {}
    for i in G.nodes:
        nodeBussyCore[i] = 0.0
    app_file = "appDefinition0.json"

    with open(app_file, "r") as json_file:
        content_app = json.load(json_file)
    sortedAppsDeadlines = sorted(appsDeadlines.items(), key=operator.itemgetter(1))
    print("Starting Multi_layer placement policy in time window", tt, " .....")
    App_num = 0
    Service_num = 0
    App_req_num = 0
    cpu_usage = 0.0
    #t = time.time()

    for appToAllocate in sortedAppsDeadlines:
        App_num = App_num + 1
        appId = appToAllocate[0]
        weightNetwork(appsSourceMessage,appId, G)
        nodesWithClients = appsRequests[appId]
        for clientId in nodesWithClients:
            App_req_num = App_req_num + 1
            requiredStrorage1 = 0.0
            requiredRAM1 = 0.0
            requiredcpu1 = 0.0
            alloc_devices = []
            serset_id = 0
            device_id = -1

            modules = content_app[appId]['module']
            App_deadline = content_app[appId]['deadline']
            A = App_deadline / 10000
            App_size = (len(modules))  # the number of modules in one app
            tempServiceAlloc = {}
            for i in range(App_size):
                #requiredcpu1 = requiredcpu1 + modules[i]['requiredcpu']
                requiredcpu1 = requiredcpu1 + modules[i]['requiredcpu']
                requiredStrorage1 = requiredStrorage1 + modules[i]['storage']
                requiredRAM1 = requiredRAM1 + modules[i]['RAM']
                Service_num = Service_num + 1
            ser_id = 0
            for serviceSet in service_set[appId]:
                requiredStrorage = 0.0
                requiredRAM = 0.0
                requiredcpu = 0.0
                #requiredcpu = requiredcpu + modules[ser_id]['INST']
                requiredcpu = requiredcpu + modules[ser_id]['requiredcpu']
                requiredStrorage = requiredStrorage + modules[ser_id]['storage']
                requiredRAM = requiredRAM + modules[ser_id]['RAM']
                ser_id = ser_id + 1


                if (device_id != -1):
                    placed = check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage[device_id],
                                       available_RAM[device_id], available_CPUCore[device_id])
                    if (placed):
                        alloc_devices.append({'device_id': device_id, 'community_Id': comm_id})
                        tempServiceAlloc[serviceSet] = device_id
                        service2DevicePlacementMatrix[serviceSet][device_id] = 1
                        Overload = False
                        nodeBussy_cpu_speed[device_id] = nodeBussy_cpu_speed[device_id] + requiredcpu
                        nodeBussy_RAM[device_id] = nodeBussy_RAM[device_id] + requiredRAM
                        nodeBussyResources[device_id] = nodeBussyResources[device_id] + requiredRAM
                        nodeBussyStorage[device_id] = nodeBussyStorage[device_id] + requiredStrorage
                        nodeBussyCore[device_id] = nodeBussyCore[device_id] + 1
                        available_RAM[device_id] = available_RAM[device_id] - requiredRAM
                        available_Storage[device_id] = available_Storage[device_id] - requiredStrorage
                        available_CPUCore[device_id] = available_CPUCore[device_id] - 1
                        serset_id = serset_id + 1
                        requiredcpu1 = requiredcpu1 - requiredcpu
                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                        requiredRAM1 = requiredRAM1 - requiredRAM
                    else:
                        similarity = sim_com_module(G,Fog_community, requiredcpu, requiredRAM, requiredStrorage,
                                                    device_id, A, clientId)
                        community = []
                        sorted_comm = []

                        for j in range(len(Fog_community)):
                            community.append({'comm_id': j, 'sim_value': similarity[j]})

                        for sorted_com in sorted(community, key=operator.itemgetter("sim_value"), reverse=True):
                            sorted_comm.append(sorted_com)

                        for j in range(len(sorted_comm)):
                            comm_id = sorted_comm[j]['comm_id']
                            overlapp = True

                            if (overlapp):

                                device_id = map_com(G, Fog_community[comm_id],topo_mem, SLAPar_info, requiredcpu, requiredRAM, requiredStrorage,
                                                clientId, available_Storage, available_RAM, available_CPUCore)
                                # after finishing the task every thing (used fog node) should come back to it's first step before updatathing
                                if (device_id != -1):
                                    alloc_devices.append({'device_id': device_id, 'community_Id': comm_id})

                                    if (serset_id == 0):
                                        topology_com_id0 = topo_mem[device_id]
                                        service2DevicePlacementMatrix[serviceSet][device_id] = 1
                                        tempServiceAlloc[serviceSet] = device_id
                                        nodeBussy_RAM[device_id] = nodeBussy_RAM[device_id] + requiredRAM
                                        nodeBussyResources[device_id] = nodeBussyResources[device_id] + requiredRAM
                                        nodeBussyStorage[device_id] = nodeBussyStorage[device_id] + requiredStrorage
                                        nodeBussyCore[device_id] = nodeBussyCore[device_id] + 1
                                        available_RAM[device_id] = available_RAM[device_id] - requiredRAM
                                        available_Storage[device_id] = available_Storage[device_id] - requiredStrorage
                                        available_CPUCore[device_id] = available_CPUCore[device_id] - 1
                                        serset_id = serset_id + 1
                                        requiredcpu1 = requiredcpu1 - requiredcpu
                                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                        requiredRAM1 = requiredRAM1 - requiredRAM
                                        break
                                    else:
                                        topology_com_id1 = topo_mem[device_id]
                                        if (topology_com_id1 == topology_com_id0):
                                            service2DevicePlacementMatrix[serviceSet][device_id] = 1
                                            tempServiceAlloc[serviceSet] = device_id
                                            nodeBussy_cpu_speed[device_id] = nodeBussy_cpu_speed[
                                                                                 device_id] + requiredcpu
                                            nodeBussy_RAM[device_id] = nodeBussy_RAM[device_id] + requiredRAM
                                            nodeBussyResources[device_id] = nodeBussyResources[device_id] + requiredRAM
                                            nodeBussyStorage[device_id] = nodeBussyStorage[device_id] + requiredStrorage
                                            nodeBussyCore[device_id] = nodeBussyCore[device_id] + 1
                                            available_RAM[device_id] = available_RAM[device_id] - requiredRAM
                                            available_Storage[device_id] = available_Storage[
                                                                               device_id] - requiredStrorage
                                            available_CPUCore[device_id] = available_CPUCore[device_id] - 1
                                            serset_id = serset_id + 1
                                            requiredcpu1 = requiredcpu1 - requiredcpu
                                            requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                            requiredRAM1 = requiredRAM1 - requiredRAM
                                            break
                else:
                    similarity = sim_com_module(G, Fog_community, requiredcpu, requiredRAM, requiredStrorage, device_id,
                                                A, clientId)
                    community = []
                    sorted_comm = []

                    for j in range(len(Fog_community)):
                        community.append({'comm_id': j, 'sim_value': similarity[j]})
                    for sorted_com in sorted(community, key=operator.itemgetter("sim_value"), reverse=True):
                        sorted_comm.append(sorted_com)

                    for j in range(len(sorted_comm)):
                        comm_id = sorted_comm[j]['comm_id']
                        overlapp = True

                        if (overlapp):

                            device_id = map_com(G, Fog_community[comm_id],topo_mem, SLAPar_info, requiredcpu, requiredRAM, requiredStrorage,
                                                clientId, available_Storage, available_RAM, available_CPUCore)

                            if (device_id != -1):
                                alloc_devices.append({'device_id': device_id, 'community_Id': comm_id})

                                if (serset_id == 0):
                                    topology_com_id0 = topo_mem[device_id]
                                    tempServiceAlloc[serviceSet] = device_id
                                    service2DevicePlacementMatrix[serviceSet][device_id] = 1
                                    nodeBussy_RAM[device_id] = nodeBussy_RAM[device_id] + requiredRAM
                                    nodeBussyResources[device_id] = nodeBussyResources[device_id] + requiredRAM
                                    nodeBussyStorage[device_id] = nodeBussyStorage[device_id] + requiredStrorage
                                    nodeBussyCore[device_id] = nodeBussyCore[device_id] + 1
                                    available_RAM[device_id] = available_RAM[device_id] - requiredRAM
                                    available_Storage[device_id] = available_Storage[device_id] - requiredStrorage
                                    available_CPUCore[device_id] = available_CPUCore[device_id] - 1
                                    serset_id = serset_id + 1
                                    requiredcpu1 = requiredcpu1 - requiredcpu
                                    requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                    requiredRAM1 = requiredRAM1 - requiredRAM
                                    break
                                else:
                                    topology_com_id1 = topo_mem[device_id]
                                    if (topology_com_id1 == topology_com_id0):
                                        tempServiceAlloc[serviceSet] = device_id
                                        service2DevicePlacementMatrix[serviceSet][device_id] = 1
                                        nodeBussy_cpu_speed[device_id] = nodeBussy_cpu_speed[device_id] + requiredcpu
                                        nodeBussy_RAM[device_id] = nodeBussy_RAM[device_id] + requiredRAM
                                        nodeBussyResources[device_id] = nodeBussyResources[device_id] + requiredRAM
                                        nodeBussyStorage[device_id] = nodeBussyStorage[device_id] + requiredStrorage
                                        nodeBussyCore[device_id] = nodeBussyCore[device_id] + 1
                                        available_RAM[device_id] = available_RAM[device_id] - requiredRAM
                                        available_Storage[device_id] = available_Storage[device_id] - requiredStrorage
                                        available_CPUCore[device_id] = available_CPUCore[device_id] - 1
                                        serset_id = serset_id + 1
                                        requiredcpu1 = requiredcpu1 - requiredcpu
                                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                        requiredRAM1 = requiredRAM1 - requiredRAM
                                        break


# ****************************************************************************************************
# ****************************************************************************************************

# Multilayer placement with SOTA Reputation

# ****************************************************************************************************

def Multilayerplc_SOTA(tt,G,devices,topo_mem,topo_par,Fog_community,SLA_info,gatewaysDevices,centralityValuesNoOrdered, numberOfServices, service_set,appsDeadlines, appsSourceMessage, mapService2App, mapServiceId2ServiceName, appsRequests):
    cloudId = 1000
    id=[]
    FOG_DEVICES = []
    for d in range(len(SLA_info)):
        id.append(SLA_info[d]['id'])
    print("devices with high SLA value:", id)
    print("this is the gateway devices in time window: ", tt, gatewaysDevices)
    with open("networkDefinition.json", "r") as json_file:
        content = json.load(json_file)
    Fog_resources = content['entity']
    network_size = (len(Fog_resources)) - 1
    FOG_DEVICES.append(Fog_resources)
    available_cpu_speed_S = {}
    available_Storage_S = {}
    available_CPUCore_S = {}
    available_RAM_S = {}
    nodeBussy_cpu_speed_S = {}
    nodeBussy_RAM_S = {}

    for device_id in range(network_size):
        nodeBussy_cpu_speed_S[device_id] = 0.0
        nodeBussy_RAM_S[device_id] = 0.0
        available_cpu_speed_S[device_id] = Fog_resources[device_id]['cpu']['speed']
        available_RAM_S[device_id] = Fog_resources[device_id]['RAM']
        available_Storage_S[device_id] = Fog_resources[device_id]['storage']
        available_CPUCore_S[device_id] = Fog_resources[device_id]['cpu']['core_num']

    service2DevicePlacementMatrix_S = [[0 for j in range(len(G.nodes))] for i in range(numberOfServices)]

    nodeBussyResources_S = {}
    for i in G.nodes:
        nodeBussyResources_S[i] = 0.0

    nodeBussyStorage_S = {}
    for i in G.nodes:
        nodeBussyStorage_S[i] = 0.0

    nodeBussyCore_S = {}
    for i in G.nodes:
        nodeBussyCore_S[i] = 0.0
    app_file = "appDefinition0.json"

    with open(app_file, "r") as json_file:
        content_app = json.load(json_file)
    sortedAppsDeadlines = sorted(appsDeadlines.items(), key=operator.itemgetter(1))
    print("Starting Multi_layer placement with SOTA reputation policy in time window", tt, " .....")
    App_num = 0
    Service_num = 0
    App_req_num = 0
    cpu_usage = 0.0
    #t = time.time()

    for appToAllocate in sortedAppsDeadlines:
        App_num = App_num + 1
        appId = appToAllocate[0]
        weightNetwork(appsSourceMessage,appId, G)
        nodesWithClients = appsRequests[appId]
        for clientId in nodesWithClients:
            App_req_num = App_req_num + 1
            requiredStrorage1 = 0.0
            requiredRAM1 = 0.0
            requiredcpu1 = 0.0
            alloc_devices_S = []
            serset_id = 0
            device_id = -1

            modules = content_app[appId]['module']
            App_deadline = content_app[appId]['deadline']
            A = App_deadline / 10000
            App_size = (len(modules))  # the number of modules in one app
            tempServiceAlloc_S = {}
            for i in range(App_size):
                requiredcpu1 = requiredcpu1 + modules[i]['requiredcpu']
                requiredStrorage1 = requiredStrorage1 + modules[i]['storage']
                requiredRAM1 = requiredRAM1 + modules[i]['RAM']
                Service_num = Service_num + 1
            ser_id = 0
            for serviceSet in service_set[appId]:
                requiredStrorage = 0.0
                requiredRAM = 0.0
                requiredcpu = 0.0
                requiredcpu = requiredcpu + modules[ser_id]['requiredcpu']
                requiredStrorage = requiredStrorage + modules[ser_id]['storage']
                requiredRAM = requiredRAM + modules[ser_id]['RAM']
                ser_id = ser_id + 1


                if (device_id != -1):
                    placed = check_res(requiredcpu, requiredStrorage, requiredRAM, available_Storage_S[device_id],
                                       available_RAM_S[device_id], available_CPUCore_S[device_id])
                    if (placed):
                        alloc_devices_S.append({'device_id': device_id, 'community_Id': comm_id})
                        tempServiceAlloc_S[serviceSet] = device_id
                        service2DevicePlacementMatrix_S[serviceSet][device_id] = 1
                        Overload = False
                        nodeBussy_cpu_speed_S[device_id] = nodeBussy_cpu_speed_S[device_id] + requiredcpu
                        nodeBussy_RAM_S[device_id] = nodeBussy_RAM_S[device_id] + requiredRAM
                        nodeBussyResources_S[device_id] = nodeBussyResources_S[device_id] + requiredRAM
                        nodeBussyStorage_S[device_id] = nodeBussyStorage_S[device_id] + requiredStrorage
                        nodeBussyCore_S[device_id] = nodeBussyCore_S[device_id] + 1
                        available_RAM_S[device_id] = available_RAM_S[device_id] - requiredRAM
                        available_Storage_S[device_id] = available_Storage_S[device_id] - requiredStrorage
                        available_CPUCore_S[device_id] = available_CPUCore_S[device_id] - 1
                        serset_id = serset_id + 1
                        requiredcpu1 = requiredcpu1 - requiredcpu
                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                        requiredRAM1 = requiredRAM1 - requiredRAM
                    else:
                        similarity = sim_com_module(G,Fog_community, requiredcpu, requiredRAM, requiredStrorage,
                                                    device_id, A, clientId)
                        community = []
                        sorted_comm = []

                        for j in range(len(Fog_community)):
                            community.append({'comm_id': j, 'sim_value': similarity[j]})

                        for sorted_com in sorted(community, key=operator.itemgetter("sim_value"), reverse=True):
                            sorted_comm.append(sorted_com)

                        for j in range(len(sorted_comm)):
                            comm_id = sorted_comm[j]['comm_id']
                            overlapp = True

                            if (overlapp):

                                device_id = map_com_SOTA(G, Fog_community[comm_id],topo_mem, SLA_info, requiredcpu, requiredRAM, requiredStrorage,
                                                clientId, available_Storage_S, available_RAM_S, available_CPUCore_S)
                                # after finishing the task every thing (used fog node) should come back to it's first step before updatathing
                                if (device_id != -1):
                                    alloc_devices_S.append({'device_id': device_id, 'community_Id': comm_id})

                                    if (serset_id == 0):
                                        topology_com_id0 = topo_mem[device_id]
                                        service2DevicePlacementMatrix_S[serviceSet][device_id] = 1
                                        tempServiceAlloc_S[serviceSet] = device_id
                                        nodeBussy_RAM_S[device_id] = nodeBussy_RAM_S[device_id] + requiredRAM
                                        nodeBussyResources_S[device_id] = nodeBussyResources_S[device_id] + requiredRAM
                                        nodeBussyStorage_S[device_id] = nodeBussyStorage_S[device_id] + requiredStrorage
                                        nodeBussyCore_S[device_id] = nodeBussyCore_S[device_id] + 1
                                        available_RAM_S[device_id] = available_RAM_S[device_id] - requiredRAM
                                        available_Storage_S[device_id] = available_Storage_S[device_id] - requiredStrorage
                                        available_CPUCore_S[device_id] = available_CPUCore_S[device_id] - 1
                                        serset_id = serset_id + 1
                                        requiredcpu1 = requiredcpu1 - requiredcpu
                                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                        requiredRAM1 = requiredRAM1 - requiredRAM
                                        break
                                    else:
                                        topology_com_id1 = topo_mem[device_id]
                                        if (topology_com_id1 == topology_com_id0):
                                            service2DevicePlacementMatrix_S[serviceSet][device_id] = 1
                                            tempServiceAlloc_S[serviceSet] = device_id
                                            nodeBussy_cpu_speed_S[device_id] = nodeBussy_cpu_speed_S[
                                                                                 device_id] + requiredcpu
                                            nodeBussy_RAM_S[device_id] = nodeBussy_RAM_S[device_id] + requiredRAM
                                            nodeBussyResources_S[device_id] = nodeBussyResources_S[device_id] + requiredRAM
                                            nodeBussyStorage_S[device_id] = nodeBussyStorage_S[device_id] + requiredStrorage
                                            nodeBussyCore_S[device_id] = nodeBussyCore_S[device_id] + 1
                                            available_RAM_S[device_id] = available_RAM_S[device_id] - requiredRAM
                                            available_Storage_S[device_id] = available_Storage_S[
                                                                               device_id] - requiredStrorage
                                            available_CPUCore_S[device_id] = available_CPUCore_S[device_id] - 1
                                            serset_id = serset_id + 1
                                            requiredcpu1 = requiredcpu1 - requiredcpu
                                            requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                            requiredRAM1 = requiredRAM1 - requiredRAM
                                            break
                else:
                    similarity = sim_com_module(G, Fog_community, requiredcpu, requiredRAM, requiredStrorage, device_id,
                                                A, clientId)
                    community = []
                    sorted_comm = []

                    for j in range(len(Fog_community)):
                        community.append({'comm_id': j, 'sim_value': similarity[j]})
                    for sorted_com in sorted(community, key=operator.itemgetter("sim_value"), reverse=True):
                        sorted_comm.append(sorted_com)

                    for j in range(len(sorted_comm)):
                        comm_id = sorted_comm[j]['comm_id']
                        overlapp = True

                        if (overlapp):

                            device_id = map_com_SOTA(G, Fog_community[comm_id],topo_mem, SLA_info, requiredcpu, requiredRAM, requiredStrorage,
                                                clientId, available_Storage_S, available_RAM_S, available_CPUCore_S)

                            if (device_id != -1):
                                alloc_devices_S.append({'device_id': device_id, 'community_Id': comm_id})

                                if (serset_id == 0):
                                    topology_com_id0 = topo_mem[device_id]
                                    tempServiceAlloc_S[serviceSet] = device_id
                                    service2DevicePlacementMatrix_S[serviceSet][device_id] = 1
                                    nodeBussy_RAM_S[device_id] = nodeBussy_RAM_S[device_id] + requiredRAM
                                    nodeBussyResources_S[device_id] = nodeBussyResources_S[device_id] + requiredRAM
                                    nodeBussyStorage_S[device_id] = nodeBussyStorage_S[device_id] + requiredStrorage
                                    nodeBussyCore_S[device_id] = nodeBussyCore_S[device_id] + 1
                                    available_RAM_S[device_id] = available_RAM_S[device_id] - requiredRAM
                                    available_Storage_S[device_id] = available_Storage_S[device_id] - requiredStrorage
                                    available_CPUCore_S[device_id] = available_CPUCore_S[device_id] - 1
                                    serset_id = serset_id + 1
                                    requiredcpu1 = requiredcpu1 - requiredcpu
                                    requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                    requiredRAM1 = requiredRAM1 - requiredRAM
                                    break
                                else:
                                    topology_com_id1 = topo_mem[device_id]
                                    if (topology_com_id1 == topology_com_id0):
                                        tempServiceAlloc_S[serviceSet] = device_id
                                        service2DevicePlacementMatrix_S[serviceSet][device_id] = 1
                                        nodeBussy_cpu_speed_S[device_id] = nodeBussy_cpu_speed_S[device_id] + requiredcpu
                                        nodeBussy_RAM_S[device_id] = nodeBussy_RAM_S[device_id] + requiredRAM
                                        nodeBussyResources_S[device_id] = nodeBussyResources_S[device_id] + requiredRAM
                                        nodeBussyStorage_S[device_id] = nodeBussyStorage_S[device_id] + requiredStrorage
                                        nodeBussyCore_S[device_id] = nodeBussyCore_S[device_id] + 1
                                        available_RAM_S[device_id] = available_RAM_S[device_id] - requiredRAM
                                        available_Storage_S[device_id] = available_Storage_S[device_id] - requiredStrorage
                                        available_CPUCore_S[device_id] = available_CPUCore_S[device_id] - 1
                                        serset_id = serset_id + 1
                                        requiredcpu1 = requiredcpu1 - requiredcpu
                                        requiredStrorage1 = requiredStrorage1 - requiredStrorage
                                        requiredRAM1 = requiredRAM1 - requiredRAM
                                        break



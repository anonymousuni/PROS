#!/usr/bin/env python

import time
import random
import json
import re
import subprocess
import sys
import os
import numpy
from kubernetes import client, config, watch
from prometheus_api_client import PrometheusConnect

start_time = time.monotonic()

prom = PrometheusConnect()

## grab latency between two nodes
#print(prom.custom_query(query="sum(abs(delta(download_durations_s_sum{}[1m]))< 50)by(source_node_name,dest_node_name)"))

config.load_kube_config()
v1=client.CoreV1Api()

scheduler_name = "pros"

def nodes_available():
    ready_nodes = []
    for n in v1.list_node().items:
            for status in n.status.conditions:
                if status.status == "True" and status.type == "Ready":
                    ready_nodes.append(n.metadata.name)
    return ready_nodes

def choice(nodes):
    resources = nodes
    resources_str = "["+(" ".join(str(x) for x in resources)).replace(" ", ",") + "]"
    tasks_str = "["+(" ".join(str(x) for x in tasks)).replace(" ", ",") + "]"
    command = str.encode(os.popen("python3.9 PROS/Model-implementation/App_placement.py").read())
    output = command.decode()
    candidates_nodes = ((("["+(output).replace("\n",",")+"]")).strip("][").split(","))[0:len(tasks)]
    #print (candidates_nodes)
    candidates_nodes_indexes = list(map(int, candidates_nodes))
    #print (len(candidates_nodes_indexes))
    candidates_nodes_names =  [0 for i in range(len(tasks))]
    for i in range(len(candidates_nodes)):
    	candidates_nodes_names[i] = nodes[candidates_nodes_indexes[i]]
    return candidates_nodes_names

def scheduler(pod, node, namespace="default"):
    # print("start binding")
    try:
        target = client.V1ObjectReference()
        target.kind = "Node"
        target.apiVersion = "v1"
        target.api_version = 'v1'
        target.name = node
        #print("Target object: ", target)
        if target.name != '':
            meta = client.V1ObjectMeta()
            meta.name = pod.metadata.name
            body = client.V1Binding(target=target, metadata=meta)
            v1.create_namespaced_binding(namespace, body, _preload_content=False)
            print(meta.name, " scheduled on ", node)
        #else:
        #   print(pod.metadata.name, " not scheduled")
    except client.rest.ApiException as e:
        print(json.loads(e.body)['message'])
        print("------------------------------------------")
    return


class Test(object):
    def __init__(self, data):
	    self.__dict__ = json.loads(data)

def main():
    w = watch.Watch()
    command_dep_encod = str.encode(os.popen("kubectl apply -f ~/Documents/0encoding/00encoding-deployment.yaml").read())
    command_dep_fram  = str.encode(os.popen("kubectl apply -f ~/Documents/1framing/11framing-deployment.yaml").read())
    command_dep_train = str.encode(os.popen("kubectl apply -f ~/Documents/3training/33training-deployment.yaml").read())
    command_dep_flask = str.encode(os.popen("kubectl apply -f PROS/SKS/code/FlaskWebApp-on-K8s/deployment.yaml").read()) 
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
            try:
                print("------------------------------------------")
                print("scheduling pod ", event['object'].metadata.name)
                res = scheduler(event['object'], choice(nodes_available())[i])
            except client.rest.ApiException as e:
                print (json.loads(e.body)['message'])

if __name__ == '__main__':
    main()
elapsed_time = numpy.round(time.monotonic() - start_time , 5)
print ("=====================================================================")
print ("Algorithm execution time: {} second(s)".format(elapsed_time))
print ("=====================================================================")

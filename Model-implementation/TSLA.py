import numpy as np
from statistics import mean
from math import e

# list of data points

def std_dev(test_list):
    avg = sum(test_list) / len(test_list)
    my_variance = sum([((x - avg) ** 2) for x in test_list]) / len(test_list)
    standard_deviation = my_variance ** 0.5
    #print("Standard deviation :", standard_deviation)
    return standard_deviation

def mean_dev(test_list):
    avg = sum(test_list) / len(test_list)
    mean_deviation = sum(abs((x - avg)) for x in test_list) / len(test_list)
    #print("Mean deviation :", mean_deviation)
    return mean_deviation

test_list = [7, 2, 4, 3, 9, 12, 10, 2]
std_dev(test_list)
mean_dev(test_list)

def TSLA_cal(t,SP, NP, alpha0, Beta0):
    #print("SP:",SP)
    #print("NP:",NP)
    #print(alpha0)
    #print(Beta0)
    integrity=[]
    utility=Utility(SP,NP,t)
    reputation,alpha,Beta=Reputation(t,SP, NP, alpha0, Beta0)
    for i in range(len(reputation)):
        integrity.append(utility[i]*reputation[i])
    print("utility: ", utility)
    print("reputation: ",reputation)
    print("integrity: ", integrity)
    return integrity,reputation,utility,alpha,Beta

def Utility(SP, NP, t,feature_num=3):
    utility=[]
    AcceptPar = []
    SuccessPar = []
    SatiPar = []
    if t==0:
        for d in range(len(SP)):
            p=0.5
            u = 0.9 * (((e ** (5 * (p - 1))) - 1) / ((e ** (-5)) - 1)) + 0.1
            utility.append(u)

    if len(SP)==1:
        utility = [0.5 for i in range(0, len(SP[0]))]
    else:
    # creating list of attribute for each device in different time intervals to calculate the mean and standard deviation
        for t in range(len(SP)):
            for i in range(len(SP[t])):
                for j in range(len(SP[t][i])):
                    if t==0:
                        if j==0:
                            AcceptPar.append([SP[t][i][j]])
                        elif j==1:
                            SuccessPar.append([SP[t][i][j]])
                        elif j==2:
                            SatiPar.append([SP[t][i][j]])
                    else:
                        if j == 0:
                            AcceptPar[i].append(SP[t][i][j])
                        elif j == 1:
                            SuccessPar[i].append(SP[t][i][j])
                        elif j == 2:
                            SatiPar[i].append(SP[t][i][j])
        #print(AcceptPar)
        #print(SuccessPar)
        #print(SatiPar)
        P=[]
        for d in range(len(AcceptPar)):
            pq = []
            x=mean(AcceptPar[d])-(3*std_dev(AcceptPar[d]))
            y=mean(AcceptPar[d])+(3*std_dev(AcceptPar[d]))
            #print(AcceptPar[d][len(AcceptPar[d]) - 1])
            if AcceptPar[d][len(AcceptPar[d])-1] <= x:
                pq.append(1)
            elif AcceptPar[d][len(AcceptPar[d])-1] > y:
                pq.append(0)
            else:
                pq.append((y- AcceptPar[d][len(AcceptPar[d])-1])/(6*std_dev(AcceptPar[d])))

            x = mean(SuccessPar[d]) - (3 * std_dev(SuccessPar[d]))
            y = mean(SuccessPar[d]) + (3 * std_dev(SuccessPar[d]))
            #print(SuccessPar[d][len(SuccessPar[d]) - 1])
            if SuccessPar[d][len(SuccessPar[d]) - 1] <=x:
                pq.append(1)
            elif SuccessPar[d][len(SuccessPar[d]) - 1] > y:
                pq.append(0)
            else:
                pq.append((y - SuccessPar[d][len(SuccessPar[d]) - 1]) / (6 * std_dev(SuccessPar[d])))

            x = mean(SatiPar[d]) - (3 * std_dev(SatiPar[d]))
            y = mean(SatiPar[d]) + (3 * std_dev(SatiPar[d]))
            #print(SatiPar[d][len(SatiPar[d]) - 1])
            if SatiPar[d][len(SatiPar[d]) - 1] <= x:
                pq.append(1)
            elif SatiPar[d][len(SatiPar[d]) - 1] > y:
                pq.append(0)
            else:
                pq.append((y - SatiPar[d][len(SatiPar[d]) - 1]) / (6 * std_dev(SatiPar[d])))
            p=0.0
            for i in pq:
                p=p+(0.33*i)
            P.append(p)

            u= 0.9*(((e**(5*(p-1)))-1)/((e**(-5))-1)) + 0.1
            utility.append(u)
    #print("utility:  ", utility)
    return utility

def Reputation(t,SP, NP, alpha0, Beta0):
    reputation=[]
    viorate=[]
    alpha=[]
    Beta=[]
    if t==0:
        for d in range(len(NP[-1])):
            reputation.append(0.5)
    else:
        w= len(NP)-1/len(NP)
        for d in range(len(NP[-1])):
            sum_vio=0.0
            sumt=0.0
            for i in range(len(NP[-1][d])):
                sum_vio=sum_vio+NP[-1][d][i]
                sumt=sumt+NP[-1][d][i]+SP[-1][d][i]
                if sumt==0:
                    viorate.append(0.0)
                else:
                    viorate.append(sum_vio/sumt)
            alpha.append((w*alpha0[d])+viorate[d])
            Beta.append((w*Beta0[d])+(1-viorate[d]))
            reputation.append(Beta[d]/(alpha[d]+Beta[d]))
        print("Violation rate: ", viorate)
        print("alpha: ", alpha)
        print("Beta: ", Beta)
    return reputation,alpha,Beta
#SP=[[[5,4,3],[9,7,7]],[[6,4,4],[2,3,1]]]
#NP=[[[5,4,3],[9,7,7]],[[6,4,4],[2,3,1]]]

#alpha0 = [0 for i in range(0, 10)]
#Beta0=[0 for i in range(0, 10)]
#TSLA_cal(SP, NP, alpha0, Beta0)
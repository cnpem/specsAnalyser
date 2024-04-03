#!/bin/env python
import sys
import socket
import time
from optparse import OptionParser

socketObject = socket.socket()

def connect(host):
    print('Creating socket')
    try:
        socketObject.connect((host, 7010))
        socketObject.settimeout(5)
        print("Successful connection")

    except socket.error as e:
        print(str(e))
        sys.exit()

def sendReceive(string):

    data = ""
    string = string+"\n"
    bytes = string.encode()
    socketObject.send(bytes)
    while True:
        try:
            data = data + socketObject.recv(1024).decode()
            if "\n" in data:
                data = data.replace("\n","")
                break
            elif not data:
                break

        except socket.timeout as e:
            print(str(e))
            break
        except socket.error as e:
            print(str(e))
            break
    return data

def makeDb(db_filename):
    
    receive = sendReceive("?0000 GetAllAnalyzerParameterNames")
    print(receive)
    receive = receive.split("ParameterNames:")[1]
    receive = receive[1:-1]
    receive = receive.replace("\"", "")
    parameters = []
    parameters = receive.split(",")

    db_file = open(db_filename, "w")
    stdout = sys.stdout
    sys.stdout = db_file
    
    print('# Macros:')
    print('#% macro, P, Device Prefix')
    print('#% macro, R, Device Suffix')
    print('#% macro, PORT, Asyn Port name')
    print('#% macro, TIMEOUT, Timeout, default=1')
    print('#% macro, ADDR, Asyn Port address, default=0')
    print('')

    # for each node
    for parameter in parameters:

        recordname = parameter.replace("/","").replace(" ","").replace("[","").replace("]","")
        upperparameter = parameter.replace("/","").replace(" ","").replace("[","").replace("]","").upper()

        receive = sendReceive("?0000 GetAnalyzerParameterInfo ParameterName:\""+parameter+"\"")
        receive = receive.split("OK: ")[1]

        parameterinforaw = []
        parameterinfo = {}

        parameterinforaw = receive.split(" ")
        for i in parameterinforaw:
            if i.split(":")[0] == "Values":
                parameterinfo[i.split(":")[0]] = i.split(":")[1][1:-1].split(",")
            else:
                parameterinfo[i.split(":")[0]] = i.split(":")[1]

        ro = False
        
        if parameterinfo["ValueType"] in ["Integer", "integer"]:
            print('record(longin, "$(P)$(R)%s_RBV") {' % recordname)
            print('  field(DTYP, "asynInt32")')
            print('  field(INP,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(SCAN, "I/O Intr")')
            print('  field(DISA, "0")')
            print('}')
            print('')
            if ro:
                continue        
            print('record(longout, "$(P)$(R)%s") {' % recordname)
            print('  field(DTYP, "asynInt32")')
            print('  field(OUT,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(DISA, "0")')
            print('}')
            print('')
        
        if parameterinfo["ValueType"] in ["Bool", "bool"]:
            print('record(bi, "$(P)$(R)%s_RBV") {' % recordname)
            print('  field(DTYP, "asynInt32")')
            print('  field(INP,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(SCAN, "I/O Intr")')
            print('  field(DISA, "0")')
            print('}')
            print('')
            if ro:
                continue        
            print('record(bo, "$(P)$(R)%s") {' % recordname)
            print('  field(DTYP, "asynInt32")')
            print('  field(OUT,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(DISA, "0")')
            print('}')
            print('')

        elif parameterinfo["ValueType"] in ["Double", "double"]:
            print('record(ai, "$(P)$(R)%s_RBV") {' % recordname)
            print('  field(DTYP, "asynFloat64")')
            print('  field(INP,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(PREC, "3")'        )
            print('  field(SCAN, "I/O Intr")')
            print('  field(DISA, "0")')
            print('}')
            print('')
            if ro:
                continue    
            print('record(ao, "$(P)$(R)%s") {' % recordname)
            print('  field(DTYP, "asynFloat64")')
            print('  field(OUT,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(PREC, "3")')
            print('  field(DISA, "0")')
            print('}')
            print('')

        elif parameterinfo["ValueType"] in ["String", "string"]:
            print('record(stringin, "$(P)$(R)%s_RBV") {' % recordname)
            print('  field(DTYP, "asynOctetRead")')
            print('  field(INP,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(SCAN, "I/O Intr")')
            print('  field(DISA, "0")')
            print('}')
            print('')
            if ro:
                continue
            print('record(stringout, "$(P)$(R)%s") {' % recordname)
            print('  field(DTYP, "asynOctetWrite")')
            print('  field(OUT,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=1))%s")' % upperparameter)
            print('  field(DISA, "0")')
            print('}')
            print('')

        else:
            print("#Don't know what to do with parameter %s, value type %s" %parameter,parameterinfo["ValueType"])
            print('')

    db_file.close()     
    sys.stdout = stdout

# parse args
parser = OptionParser("""%prog <ip_server> <db_filename>
This script creates the database file of device parameters used in SpecsLab Prodigy Remote Control""")
options, args = parser.parse_args()

if len(args) != 2:
    parser.error("Incorrect number of arguments")
else:
    connect(args[0])
    status = sendReceive("?0000 Connect")
    print(status)
    if "OK" in status:
        makeDb(args[1])
        print("Db parameters created successfully")
        sendReceive("?0000 Disconnect")
    else:
        print("Connection Error")

socketObject.close()
print("Finish")
sys.exit()

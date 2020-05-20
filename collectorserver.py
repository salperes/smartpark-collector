import paho.mqtt.client as mqtt
import json
import mysql.connector
import socket
import time,datetime
import sys, signal, os.path
import collectorhelper
######################################################################################
def signal_handler(signal, frame):
    print("\nprogram exiting gracefully")
    logFile("stopping with CTRL+C")
    #mqttClient.loop_stop()
    #time.sleep(.1)
    mqttClient.disconnect()
    time.sleep(.1)
    sys.exit(0)

######################################################################################
def logFile(data):
    
    if len(data)>50:
        data = data[:50]
        
    if len(data)<=50:
        for i in range(len(data),50):
            data=data+" "
    logItem = data + " (@:" + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ")\n"
    if not os.path.isfile(logFileName):
        with open(logFileName,"w") as fileContainer:
            fileContainer.write(logItem)
    else:
        with open(logFileName,"a") as fileContainer:
            fileContainer.write(logItem)

######################################################################################
def connectMQTT():
    mqttClient.on_message = on_message
    mqttClient.on_connect = on_connect
    mqttClient.on_publish = on_publish
    mqttClient.on_subscribe = on_subscribe
    mqttClient.on_disconnect = on_disconnect
    mqttClient.username_pw_set(username="collector",password="Alp2013er!")
    mqttClient.connect("localhost",port=1883)
    subsTo = ("/mes/#")
    print(subsTo)
    mqttClient.subscribe(subsTo)
    
############
def on_message(client, userdata, message):
    _mesg = json.loads(message.payload)
    #print(_mesg)
    print("message topic=",message.topic)
    # print("message qos=",message.qos)
    # print("message retain flag=",message.retain)
    decodeIncomming(message.topic,_mesg)


def on_connect(mqttc, obj, flags, rc):
    print("Connected to %s:%s" % (mqttc._host, mqttc._port))

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mqttc, obj, level, string):
    print(string)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection. Attempting to reconnect.")
        mqttConnected = False
        try:
            time.sleep(10)
            mqttClient.reconnect()
        except socket.error:
            time.sleep(30)

######################################################################################
def printWPS(packageType,message):
    print("-------------------------------------------------------------")
    print(packageType)

    print("LoRa Msg. Time      :",      message["preamble"]["msgTime"])
    print("MQTT Msg. Time      :",      message["mqttTRtime"])    
    print("coordinator Serial  :",      message["coordSerial"])
    print("WPS Sequence Number :",      message["preamble"]["sequence"])
    print("WPS Serial BLE      :",      message["preamble"]["sensor_serial"])
    print("WPS Address         : ",     message["preamble"]["lora_network"], ".", message["preamble"]["lora_address"],sep="")
   
    print("WPS Mag Error       :",      message["preamble"]["magErr"])
    print("WPS BLE Error       :",      message["preamble"]["BLEErr"])
    print("WPS Lora TX Error   :",      message["preamble"]["LTXErr"])
    
    print("Last TX Retry Count :",      message["preamble"]["loraTXCount"])
    print("Vector Variance     :",      message["preamble"]["vectorVariance"])  
    print("WPS Vehicle Status  :",      message["preamble"]["vehicleStatus"])
    print("WPS Bar Status      :",      message["preamble"]["barStatus"])


    if packageType == "PKG_BOVL" or packageType == "PKG_PERI":
        print("WPS Temperature (C) :",  message["health"]["sensor_temp"])
        print("Battery Voltage     :",  message["health"]["battVoltage"],"V")
        print("Battery Level       :",  message["health"]["battLevel"],"%")
        print("WPS side RSSI       :",  message["health"]["sensRSSI"],"dBM")
        print("Coord. side RSSI    :",  message["health"]["coordRSSI"],"dBM")
 
    
    if packageType == "PKG_BOVL":
        print("WPS Serial MSBs     : ", message["staValues"]["serialMSB"])
        print("WPS SW Version      : ", message["staValues"]["sensSWversion"])
        print("WPS HW Version      : ", message["staValues"]["sensHWversion"])
        print("WPS magZ            : ", message["sensConfig"]["magZ"])
        print("WPS magXY           : ", message["sensConfig"]["magXY"])
        print("WPS readFRQ         : ", message["sensConfig"]["readFRQ"])
        print("WPS VarianceOrDiff  : ", message["sensConfig"]["VarianceOrDiff"])
        print("WPS vectorVarBase   : ", message["sensConfig"]["vectorVarBase"])
        print("WPS vectorVarLim    : ", message["sensConfig"]["vectorVarLim"])
        print("WPS checkRSSI       : ", message["sensConfig"]["checkRSSI"])
        print("WPS minRSSIdif      : ", message["sensConfig"]["minRSSIdif"])
        print("WPS maxRSSIdif      : ", message["sensConfig"]["maxRSSIdif"])
        print("WPS radioTXpower    : ", message["sensConfig"]["radioTXpower"])
        print("WPS bleTXpower      : ", message["sensConfig"]["bleTXpower"])
        print("WPS Vehic.Det.Cnt.  : ", message["sensConfig"]["vehicleDetectionCount"])
        print("WPS wpsSleepCount   : ", message["sensConfig"]["wpsSleepCount"])
        print("WPS loraChannel     : ", message["sensConfig"]["loraChannel"])
        print("WPS loraFRQ         : ", message["sensConfig"]["loraFRQ"])
        print("WPS diffMultiplier  : ", message["sensConfig"]["diffMultiplier"])
        print("WPS sensorGain      : ", message["sensConfig"]["sensorGain"])
        print("WPS bleWaitTimeout  : ", message["sensConfig"]["bleWaitTimeout"])
        print("WPS modemConfigNum. : ", message["sensConfig"]["modemConfigNumber"])
        print("WPS contMode        : ", message["sensConfig"]["contMode"])

######################################################################################
def updateWPSConfigTable(message):
    
    wpsSerial = message["preamble"]["sensor_serial"]
   
    sql = "SELECT * FROM sensor_config "
    sqlw = ("WHERE serialBLE='%s'" % wpsSerial)
    
    sql = sql + sqlw 
    print (sql)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    if len(myresult) == 0:
        print("not existing sensor serial, inserting new values")
    
        sql = "INSERT INTO sensor_config "
        sql = sql + "(ConfigTime, coordSerial, serialBLE, wpsAddress, wpsNetworkID, wpsSerialMSB, wpsSWVersion, "
        sql = sql + "wpsHWVersion, wpsmagZ, wpsmagXY, wpsreadFRQ, wpsVarianceOrDiff, wpsvectorVarBase, wpsVectorVarLim, wpsCheckRSSI, "
        sql = sql + "wpsMinRSSIdif, wpsMaxRSSIdif, wpsRadioTXpower, wpsBLETXpower, wpsVehicDetCnt, wpsSleepCount, wpsLoraChannel, wpsLoraFRQ, "
        sql = sql + "wpsdiffMultiplier, wpsSensorGain, wpsBLEWaitTimeout, wpsModemConfigNum, wpsContMode"
        sql = sql + ")  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    else:
        print("existing sensor serial, updating new values")
        sql = "UPDATE sensor_config set "
        sql = sql + "ConfigTime=%s, coordSerial=%s, serialBLE=%s, wpsAddress=%s, wpsNetworkID=%s, wpsSerialMSB=%s, wpsSWVersion=%s, "
        sql = sql + "wpsHWVersion=%s, wpsmagZ=%s, wpsmagXY=%s, wpsreadFRQ=%s, wpsVarianceOrDiff=%s, wpsvectorVarBase=%s, wpsVectorVarLim=%s, wpsCheckRSSI=%s, "
        sql = sql + "wpsMinRSSIdif=%s, wpsMaxRSSIdif=%s, wpsRadioTXpower=%s, wpsBLETXpower=%s, wpsVehicDetCnt=%s, wpsSleepCount=%s, wpsLoraChannel=%s, wpsLoraFRQ=%s, "
        sql = sql + "wpsdiffMultiplier=%s, wpsSensorGain=%s, wpsBLEWaitTimeout=%s, wpsModemConfigNum=%s, wpsContMode=%s "
        sql = sql + sqlw
            

    data =(
        message["mqttTRtime"],
        message["coordSerial"],
        message["preamble"]["sensor_serial"],
        message["preamble"]["lora_address"],
        message["preamble"]["lora_network"],         
        message["staValues"]["serialMSB"],
        message["staValues"]["sensSWversion"],
        message["staValues"]["sensHWversion"],
        message["sensConfig"]["magZ"],
        message["sensConfig"]["magXY"],
        message["sensConfig"]["readFRQ"],
        message["sensConfig"]["VarianceOrDiff"],
        message["sensConfig"]["vectorVarBase"],
        message["sensConfig"]["vectorVarLim"],
        message["sensConfig"]["checkRSSI"],
        message["sensConfig"]["minRSSIdif"],
        message["sensConfig"]["maxRSSIdif"],
        message["sensConfig"]["radioTXpower"],
        message["sensConfig"]["bleTXpower"],
        message["sensConfig"]["vehicleDetectionCount"],
        message["sensConfig"]["wpsSleepCount"],
        message["sensConfig"]["loraChannel"],
        message["sensConfig"]["loraFRQ"],
        message["sensConfig"]["diffMultiplier"],
        message["sensConfig"]["sensorGain"],
        message["sensConfig"]["bleWaitTimeout"],
        message["sensConfig"]["modemConfigNumber"],
        message["sensConfig"]["contMode"],
        )
    
    mycursor.execute(sql, data)
    mydb.commit()

######################################################################################
def addWPSLogTable(message, packageType):
    wpsSerial = message["preamble"]["sensor_serial"]
    print(wpsSerial)
    sql = "INSERT INTO sensor_log "
    sql = sql + "(serialBLE, wpsSequence, VehicleStatus, VectorVariance, mqttMsgTime, loraMsgTime, wpsBarStatus, "
    sql = sql + "wpsMagError, wpsBLEError, wpsLoraTXError, LastTXRetryCount, wpsTemperature, wpsBatteryVoltage, wpsBatteryLevel, " 
    sql = sql + "wpsSideRSSI, coordSideRSSI ,packageType"
    sql = sql + ") VALUES ('%s', %s, '%s', %s, '%s', '%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s')"
            
    
    data =(     
        message["preamble"]["sensor_serial"],
        message["preamble"]["sequence"],
        message["preamble"]["vehicleStatus"],
        message["preamble"]["vectorVariance"],
        message["mqttTRtime"],
        message["preamble"]["msgTime"],
        message["preamble"]["barStatus"],
        message["preamble"]["magErr"],
        message["preamble"]["BLEErr"],
        message["preamble"]["LTXErr"],
        message["preamble"]["loraTXCount"],
        message["health"]["sensor_temp"],
        message["health"]["battVoltage"],
        message["health"]["battLevel"],
        message["health"]["sensRSSI"],
        message["health"]["coordRSSI"],
        packageType
    )
    sql = (sql % data)
    mycursor.execute(sql)
    mydb.commit()

######################################################################################
def decodeIncomming(_topic, message):
    
    topic = _topic.split("/")
    coordSerial = topic[2] 
    packageType = topic[3]  
    

    message["mqttTRtime"] = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S") 
    message["coordSerial"] = coordSerial 

    addWPSLogTable(message, packageType)

    if packageType == "PKG_BOVL":
        updateWPSConfigTable(message)

    # printWPS(packageType,message)
  
########################################################################

mydb = mysql.connector.connect(
  host="localhost",
  user="smrtprkadmin",
  passwd="Alp2013er!",
  database="smartparking"
)

mycursor = mydb.cursor()

# mycursor.execute("CREATE TABLE customers (name VARCHAR(255), address VARCHAR(255))")


######################################################################################
##########################         S T A R T         #################################
######################################################################################

logFileName = (sys.argv[0]).split(".")[0] + ".log"
logFile("starting")

mqttClientName=socket.gethostname()

mqttClient = mqtt.Client(client_id=mqttClientName)
time.sleep(0.1)
connectMQTT()

wps = collectorhelper.WPSDATA()


while True:
    signal.signal(signal.SIGINT, signal_handler)
    mqttClient.loop_start()
    
    time.sleep(.2)
    mqttClient.loop_stop()
    
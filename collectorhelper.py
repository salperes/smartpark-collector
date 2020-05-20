BASE_FREQ433=433.15
BASE_FREQ865=865.20

###############################################################################
###############################################################################
class WPSDATA:
    def __init__(self, wpsaddress=0, wpsserial=None):
        self.flagid = 0   
        self.network_id = 0
        self.coordinatorSerial = 0 
        # RECV BYTE 00
        self.byte00 = 0                 # Byte 00
        self.magError=0                 # BIT 0 MAGNETOMETER ERROR STATUS
        self.BLEerror=0                 # BIT 1 BLEMODULE ERROR STATUS
        self.loraTXerror=0              # BIT 2 LORA ERROR STATUS
        self.compassType=0              # BIT 3 COMPASS TYPE
        self.barStatus=0                # BIT 6 OCCUPATION BAR STATUS (OPEN/CLOSE)
        self.vehicleStatus=0            # BIT 7 EMPTY / BUSY
        
        # RECV BYTES 01-08
        self.wpsaddress = wpsaddress    
        self.wpsserial = wpsserial      # Byte 01-04
        self.sequence = 0               # Byte 06-08
        self.byte08 = 0
        self.lastTXRetryCount=0
        self.vectorVariance=0

        # RECV BYTES 09-13 
        # HEALTH VALUES 
        self.temperature = 0            # Byte 09-10
        self.batteryvalue = 0           # Byte 11-12
        self.lastRSSI = 0               # Byte 13
        self.recvRSSI = 0               # RSSI Calculated from Coordinator side storage

        self.wpsVoltage = 0
        self.wpsbattlevel=0

        # RECV BYTES 14-21
        # CONFIGURATION PARAMETERS
        self.magparam = 0				# Byte 14 
        self.magZ=0
        self.magXY=0
        self.readFRQ=0
        self.VarianceOrDiff=0

        self.vecvarlimits = 0			# Byte 15
        self.vector_variance_base = 0   # MINIMUM TRESHOLD FOR DETERMINE LOT EMPTY 
        self.vector_variance_limit = 0  # MAXIMUM TRESHOLD FOR DETERMINE LOT BUSY

        self.rssdiflimits = 0			# Byte 16
        self.minRSSIdiff = 0            # MINIMUM TRESHOLD FOR DETERMINE LOT EMPTY.  EXPERIMENTAL  
        self.maxRSSIdiff = 0            # MAXIMUM TRESHOLD FOR DETERMINE LOT BUSY. EXPERIMENTAL 

        self.rfpowers = 0				# Byte 17
        self.radioTXpower = 0           # LORA TRANSMIT POWER 
        self.bleTXpower = 0             # BLE TRANSMIT POWER
        self.check_rssi = 0             # WHETHER CHECK RSSI OR NOT ... EXPERIMENTAL

        self.vdcslpcounts = 0			# Byte 18
        self.vehicleDetectionCount = 0
        self.wpsSleepCount = 0

        self.channel= 0	                # Byte 19

        self.dmBLEwSG = 0				# Byte 20 DIFF_MULTIPLIER & BLE_WAIT_TIMEOUT & SENSOR GAIN
        self.diffMultiplier = 0         # VECTOR ABSOLUTE DIFFERENCE MULTIPLIER, FOR REDUCING LORA PACKET SIZE
        self.sensorGain = 0             # MAGNETOMETER GAIN
        self.bleWaitTimeout = 0         # TIMEOUT FOR BLE MODULE BEFORE ENTER SLEEP STATE

        self.modemcfg_contmode = 0		# Byte 21 modem config number and contMode
        self.modemConfigNumber = 0      # LORA MODEM PARAMETER SELECTION 
        self.contMode = 0               # IF OCCUPATION BAR INSTALLED, SET TRUE, WPS NEVER SLEEPS

        self.serialMSBs=0
        self.hw_sw_ver=0
        self.swmin=0
        self.hwVersion=0
        self.swVersion=0
 
        
        # FLAG_USE_CRC 0b01000000        
        self.revc_useCRC = 0                 # Received package use CRC 
        # FLAG_USE_ENCRYPTION 0b10000000  
                                        # ONLY USE FOR FLAD IDs 10-30
        self.revc_useENC = 0

        self.lastSeen=0

        self.loraTRtime = 0
        self.mqttTRtime = 0

        self.wpsLoraFrq = 0
        
###############################################################################
    def decodePreamble(self, dataContainer):
     
        try:
            self.flagid = dataContainer.rxHeaderFlagsInitial & 0b00111111
            self.revc_useCRC=dataContainer.revc_useCRC
            self.revc_useENC=dataContainer.revc_useENC
        except:
            print("mqtt module")

        self.wpsaddress = dataContainer.wpsaddress
        self.network_id = dataContainer.networkid

        self.byte00 = dataContainer.data[0]
        self.magError     = (0b00000001 & self.byte00)                # MAGNETOMETER ERROR STATUS
        self.BLEerror     = (0b00000010 & self.byte00) >> 1           # BLEMODULE ERROR STATUS
        self.loraTXerror  = (0b00000100 & self.byte00) >> 2           # LORA ERROR STATUS
        self.compassType  = (0b00001000 & self.byte00) >> 3           # COMPASS TYPE
        self.barStatus    = (0b01000000 & self.byte00) >> 6           # OCCUPATION BAR STATUS (OPEN/CLOSE)
        self.vehicleStatus= (0b10000000 & self.byte00) >> 7           # EMPTY / BUSY

        self.wpsserial = dataContainer.data[4] << 24 | dataContainer.data[3] << 16 | dataContainer.data[2] << 8 | dataContainer.data[1]
        self.sequence = dataContainer.data[5] << 16 | dataContainer.data[6] << 8 | dataContainer.data[7]

        self.byte08 = dataContainer.data[8]

        self.lastTXRetryCount = self.byte08 & 0b00001111
        self.vectorVariance   = (self.byte08 & 0b11110000) >> 4

###############################################################################
    def decodeHealth(self, dataContainer):
        
        tempValue = dataContainer.data[10] * 256 + dataContainer.data[9] 
        
        if (self.compassType == 0 ):
            self.temperature = tempValue/128+25
        else:
            self.temperature = tempValue/8+25
        
        self.battValue =  dataContainer.data[12] * 256 + dataContainer.data[11] 


        self.wpsVoltage = round((self.battValue*3.3 * 2 / 1024),2)

        self.wpsbattlevel = calculateBattLevel(self.wpsVoltage)
       
        self.recvRSSI = round (dataContainer.recvRSSI)
        self.lastRSSI = round(dataContainer.data[13])*-1


###############################################################################
    def calculateBattLevel(self, voltage):
        ##################################################### 
        #   CALCULATION BASED ON 6V ALKALINE BATTERY PACK
        if (voltage >= 6):
            self.wpsbattlevel = 100

        if (voltage < 6) and (voltage >= 5.6):
            self.wpsbattlevel = 96 + (100 * 4 * (voltage - 5.6) / 40)
            if (self.wpsbattlevel > 100):
                self.wpsbattlevel = 100

        if (voltage < 5.6 and voltage >= 5.12):
            self.wpsbattlevel = 83 + (100 * 13 * (voltage - 5.12) / 48)
            if (self.wpsbattlevel > 96): 
                self.wpsbattlevel = 96
        
        if (voltage < 5.12 and voltage >= 4):
            self.wpsbattlevel = 17 + (100 * 66 * (voltage - 4) / 112)
            if (self.wpsbattlevel > 83): 
                self.wpsbattlevel = 83


        if (voltage < 4 and voltage >= 3.2):
            self.wpsbattlevel = 100 * 17 * (voltage - 3, 2) / 80
            if (self.wpsbattlevel > 17): 
                self.wpsbattlevel = 17
        
        if (voltage < 3.2): 
            self.wpsbattlevel = 0      

        return int(round(self.wpsbattlevel))


###############################################################################
    def decodeConfig(self, dataContainer):

        # decode magParameters
        self.magparam = dataContainer.data[14]
        self.magZ = self.magparam & 0b00000011
        self.magXY = (self.magparam & 0b00001100) >> 2
        self.readFRQ =	(self.magparam & 0x01110000) >> 4
        self.VarianceOrDiff = self.magparam >> 7
    
        # vector var limists
        self.vecvarlimits = dataContainer.data[15]
        self.vector_variance_base  = self.vecvarlimits & 0b00000111
        self.vector_variance_limit = self.vecvarlimits >> 3 
        

        
        # decode min-max RSSI diff
        self.rssdiflimits = dataContainer.data[16]			
        self.minRSSIdiff = self.rssdiflimits & 0b00000111
        self.maxRSSIdiff = self.rssdiflimits  >> 3

        # decode RF powers and check_rssi bit
        self.rfpowers = dataContainer.data[17]	
        self.radioTXpower = self.rfpowers & 0b00011111         
        self.bleTXpower =  (self.rfpowers & 0b01100000) >> 5        
        self.check_rssi =  self.rfpowers >> 7         

        # decode counts
        self.vdcslpcounts = dataContainer.data[18]
        self.vehicleDetectionCount = self.vdcslpcounts >> 6
        self.wpsSleepCount = self.vdcslpcounts & 0b00111111

        # get Channel
        self.channel= dataContainer.data[19]

        # decode Multipliers, magGain and ble timeout
        self.dmBLEwSG = dataContainer.data[20]
        self.diffMultiplier = self.dmBLEwSG & 0b00000011
        self.sensorGain = (self.dmBLEwSG & 0b00001100) >> 2
        self.bleWaitTimeout = self.dmBLEwSG >> 4

        # decode Modem Config number and enable Continious Mode
        self.modemcfg_contmode =  dataContainer.data[21]
        self.modemConfigNumber = self.modemcfg_contmode & 0b00001111     
        self.contMode = (self.modemcfg_contmode & 0b00010000) >> 4

############################################################################### 
    def decodeStatic(self, dataContainer,returnPackageType):
        
        # static val can be started from byte 09 or byte 22 depends on package type
        offset = 0
        if returnPackageType == "PKG_BOVL":
            offset=13

        self.serialMSBs= dataContainer.data[10+offset] << 8 | dataContainer.data[9+offset]
        
        self.hw_sw_ver = dataContainer.data[11+offset]
        self.swmin=dataContainer.data[12+offset] & 0b00111111
        
        self.hwVersion= (self.hw_sw_ver & 0b11110000) >> 4
        self.swVersion= str(self.hw_sw_ver & 0b00001111) + "." + str(self.swmin)

###############################################################################
    def printWPS(self, returnPackageType):

        print("WPS Address         :",self.wpsaddress)
        print("Sequence number     :",self.sequence)
        print("WPS Serial BLE      :",self.wpsserial)
        print("WPS Error Status    :", self.magError + self.BLEerror + self.loraTXerror)
        if self.contMode == 1:
            print("WPS Bar Status      :",self.barStatus)
        
        print("WPS Vehicle Status  :",self.vehicleStatus)

        print("Last TX Retry Count :", self.lastTXRetryCount)
        print("Vector Variance     :", self.vectorVariance)

        if returnPackageType == "PKG_BOVL" or returnPackageType == "PKG_PERI":
            print("WPS Temperature (C) :",self.temperature)
            print("Battery Voltage     :",self.wpsVoltage,"V")
            print("Battery Level       :",self.wpsbattlevel,"%")
            print("WPS side RSSI dBm   :",self.lastRSSI,"dBM")

        print("Coord. side RSSI dBm:",self.recvRSSI,"dBM")
        
        if returnPackageType == "PKG_BOVL":
            print("WPS Serial MSBs     : ",self.serialMSBs)
            print("WPS SW Version      : ",self.swVersion)
            print("WPS HW Version      : ",self.hwVersion)
            print("Network ID          : ",self.network_id)
            print("")

###############################################################################
    def createPackage(self, dataContainer,returnPackageType):

        self.decodePreamble(dataContainer)
        
        if returnPackageType == "PKG_BOVL":
            self.decodeConfig(dataContainer)
            self.decodeStatic(dataContainer,returnPackageType)
            self.decodeHealth(dataContainer)

        if returnPackageType == "PKG_PERI":
            self.decodeHealth(dataContainer)

        mqttPack={}

        mqttPack["sensor_serial"]=dataContainer.wpsserial
        mqttPack["msgTime"]=dataContainer.msgTime
        mqttPack["lora_address"] = dataContainer.wpsaddress
        mqttPack["lora_network"] = dataContainer.networkid
        mqttPack["sequence"] = self.sequence
        
        mqttPack["errorStatus"] = self.loraTXerror << 2 + self.BLEerror << 1 + self.magError 
        
        if self.contMode == 1:
            mqttPack["barStatus"] = self.barStatus
        
        if self.vehicleStatus:
            mqttPack["vehicleStatus"] = "busy"
        else:
            mqttPack["vehicleStatus"] = "empty"

        mqttPack["loraTXCount"] = self.lastTXRetryCount
        mqttPack["vectorVariance"] =  self.vectorVariance

        if returnPackageType == "PKG_BOVL" or returnPackageType == "PKG_PERI":
            mqttPack["sensor_temp"]=self.temperature
            mqttPack["battVoltage"]= self.wpsVoltage
            mqttPack["battLevel"]=self.wpsbattlevel
            mqttPack["sensRSSI"]=self.lastRSSI

        mqttPack["coordRSSI"]=self.recvRSSI
        
        if returnPackageType == "PKG_BOVL":
            mqttPack["serialMSB"]= hex(self.serialMSBs).upper()
            mqttPack["sensSWversion"] = self.swVersion
            mqttPack["sensHWversion"]=self.hwVersion

            mqttPack["magZ"] = self.magZ
            mqttPack["magXY"] =self.magXY
            mqttPack["readFRQ"] =self.readFRQ 
            mqttPack["VarianceOrDiff"] =self.VarianceOrDiff 

            mqttPack["vectorVarBase"] = self.vector_variance_base  
            mqttPack["vectorVarLim"] = self.vector_variance_limit

            mqttPack["checkRSSI"] = self.check_rssi
            mqttPack["minRSSIdif"] = self.minRSSIdiff  
            mqttPack["maxRSSIdif"] = self.maxRSSIdiff

            mqttPack["radioTXpower"] = self.radioTXpower
            mqttPack["bleTXpower"] = self.bleTXpower

            mqttPack["vehicleDetectionCount"] = self.vehicleDetectionCount 
            mqttPack["wpsSleepCount"] = self.wpsSleepCount

            mqttPack["loraChannel"] = self.channel
            if self.channel < 64:
                mqttPack["loraFRQ"] = round(float(BASE_FREQ433) + 0.2 * self.channel, 2)
            else:
               mqttPack["loraFRQ"] = round(float(BASE_FREQ865) + 0.3 * self.channel, 2)


            mqttPack["diffMultiplier"] = self.diffMultiplier 
            mqttPack["sensorGain"] = self.sensorGain 
            mqttPack["bleWaitTimeout"] = self.bleWaitTimeout 

            mqttPack["modemConfigNumber"] = self.modemConfigNumber      
            mqttPack["contMode"] = self.contMode

        return mqttPack   




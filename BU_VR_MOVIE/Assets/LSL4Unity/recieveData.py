from pylsl import StreamInlet, resolve_stream 
from pylsl import StreamInfo, StreamOutlet
import time as time
import sys
import biosppy
import numpy as np
import pyhrv.tools as tools
import numpy as np
import pyhrv.time_domain as td 
import datetime
import random as random
import array


print("looking for an ECG stream...")
streams = resolve_stream('type', 'signal')

inlet = StreamInlet(streams[0]) 
counter = 0
loop_time = 20
loop_time2 = 60*3
tEnd = time.time() + loop_time
sdnn=0.0
samples = []
bMaxSdnn=0
bLowSdnn=0
delta =0
window = delta/3 
baseTimeLow = time.time()
baseTimeHigh =time.time()

info = StreamInfo('Freq', 'Float', 4, 100, 'float32', 'myuid2424')
outlet = StreamOutlet(info)

# method for stress SDNN calculation 
def calcStress(data):
     data, rpeaks = biosppy.signals.ecg.ecg(data,show=False)[1:3] #extract R-peaks using BioSppy
     nni = tools.nn_intervals(rpeaks) # Compute NNI
     SDNN = td.sdnn(nni) #compute SDNN for current frame  
     lSdnn = SDNN['sdnn']
     #resultFile.write("timeframe:%s\r      SDNN:%s     StressLevel:%s    New Score:%s    Current Score:%s     Last tScore:%s\r\n" % (datetime.datetime.now(), sdnn, stress, newScore, currentScore, lastScore)) # save results into file
     return lSdnn

#def OpenFile():
#    global counter
#    filedata= open("./datarecoreded%d.txt" %counter , "w+")
#    print("opened file %s " % filedata.name)
#    counter+=1
#    return filedata


#currentFile= OpenFile()

#def saveToFile(odata):
    #with open(currentFile.name ,"a+") as target:
        #for line in odata:
            #target.write("%s" % str(line)) 
        #target.write("\r\n")   
    #print("got %s at time %s" % (sample[0], timestamp))

def saveSample():
    global samples
    samples,timestamps = inlet.pull_chunk(timeout=5, max_samples=30000)
   # print("got %s at time %s" % (samples[0], timestamps))
    samples = np.array(samples).ravel()
    m_timestamps = np.array(timestamps)
    m_timestamps *= 1000
    return samples,  m_timestamps

def calcHighBseline():
    global bMaxSdnn
    basedata, baseTimeHigh= saveSample()
    bMaxSdnn= calcStress(basedata)
    print("Base High SDNN %s" % (bMaxSdnn))
    
def calcLowBseline():
    global bLowSdnn
    basedata, baseTimeLow= saveSample()
    bLowSdnn= calcStress(basedata)
    print("Base Low SDNN %s" % (bLowSdnn))

def calcWindow():
    global delta, window
    delta = bMaxSdnn - bLowSdnn
    window = delta /3

calcHighBseline()
calcLowBseline()

while True:
    #global sdnn,bMaxSdnn, bLowSdnn

    data, time = saveSample()
    sdnn = calcStress(data)
    print("SDNN %s" % (sdnn))
    if(sdnn > bMaxSdnn):
        bMaxSdnn = sdnn
        calcWindow() # send reduced frequency number
        print("incresed base Max SDNN sending high freq ..." )
        x=[30,sdnn,0,5]
        outlet.push_sample(x)
    elif (sdnn >= bMaxSdnn - (window*2)):
        x=[30,sdnn,0,4]
        outlet.push_sample(x)
        print("now sending high freq ..." )
    elif (sdnn < bLowSdnn):
        bLowSdnn =sdnn  
        calcWindow()
        print("docreased base Low SDNN sending Low freq ..." )
        x=[6,sdnn,0,4]
        outlet.push_sample(x)
    elif (sdnn <= bLowSdnn - window):
        x=[6,sdnn,3,4]
        outlet.push_sample(x)
        print("now sending Low freq ..." )
    else:
        x=[5,sdnn,0,4]
        outlet.push_sample(x)
        print("now sending optimal freq ..." )
        


        
 
    




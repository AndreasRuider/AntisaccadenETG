# -*- coding: utf-8 -*-
"""
(c) 2021 University of Regensburg

Antisaccaden Eyetracking
"""

import csv
import re

import Logfile
import os
import scipy.signal
import math

#import numpy
#import re
#import csv

import matplotlib.pyplot as plt


# Setup Variables

InFolderName    = 'logs/antisaccade'
OutFolderName   = 'logs/antisaccade_result'

reactAngle = 3.0                # yaw considered a reaction
FilterWindow = 5                # Windowsize in sample points for filter
GeneratePlots = False           # True to generate plots (better not for lots of logfiles)


##### CODE #####

class Counter:
    def __init__(self):
        self.NumIncorrect = 0
        self.NumFixationError = 0

    def incorrect(self):
        self.NumIncorrect += 1

    def fixationError(self):
        self.NumFixationError += 1
        
    def result(self):
        print( "Found %d incorrect reactions and %d fixation errors." % (self.NumIncorrect,self.NumFixationError))
        
        

class Evaluator:
    def __init__(self,active=False,TimeStamp=0,File=0,Marker='',counter=0):
        self.counter = counter
        self.TimeStamp = TimeStamp
        self.Marker = Marker
        self.File = File
        self.findBlink = True
        self.foundBlink = 0
        self.findSacc = True
        self.foundSacc = 0
        self.findReaction = False
        self.findFixation = False
        self.Latency = 0
        self.index = 0
        self.P1 = []
        self.P2 = []
        self.A = []
        self.T = []
        self.t = 0
        self.evaluating = active
        self.Yaw = 0
        self.Pitch = 0
        self.Angle = 0
        self.Error = 0
        self.DoPlot = False
        if self.evaluating:
            print(Marker)

    def inactive(self):
        self.evaluating = False
        
    def fixation(self):
        self.findFixation = True
        
    def direction(self,pseudoRow,anti=False):
        self.findReaction = True
        print('Directuib %s' % pseudoRow[3])
        if pseudoRow[3]!=self.Marker:
            return False
        if anti:
            if pseudoRow[1]=="L":
                print( "Expect Right" )
                self.reactRight = True
            else:
                print( "Expect Left" )
                self.reactRight = False
        else:
            if pseudoRow[1]=="R":
                print( "Expect Right" )
                self.reactRight = True
            else:
                print( "Expect Left" )
                self.reactRight = False
        return True

    def evaluate(self,dt,v1,v2,angle,pitch,yaw,row):
        #print('Evaluate %f  %f' % (dt,self.window))
        if self.t < 1:
            if self.findBlink and (row['Left Validity']!='31' or row['Right Validity']!='31'):
                self.foundBlink = self.t
                self.findBlink = False
                print('Blink at %f' % self.t)
            if self.findSacc and v2>30:
                if self.findFixation:
                    self.DoPlot = True
                self.foundSacc = self.t
                self.findSacc = False
                print('Saccade at %f' % self.t)
            if self.findFixation:
                if abs(angle) > reactAngle:
                    self.Yaw = yaw
                    self.Pitch = pitch
                    self.Angle = angle
                    print("Reaction incorrect. angle=%f° pitch=%f° pitch=%f°" % (angle,pitch,yaw))
                    self.counter.fixationError()
                    self.findFixation = False                                
                    print( "Reacted in %d ms" % (self.t*1000))
                    self.Error = 1
                    self.Latency = self.t;
            if self.findReaction:
                if abs(yaw) > reactAngle:
                    self.Yaw = yaw
                    self.Pitch = pitch
                    self.Angle = angle
                    if (self.reactRight and yaw<0) or ((not self.reactRight) and yaw>0):
                        print("Reaction correct %f°" % yaw)
                        self.Error = 0
                    else:
                        print("%s: Reaction incorrect. %f°" % (self.Marker,yaw))
                        self.Error = 1
                        self.counter.incorrect()
                    self.Latency = self.t;
                    print( "Reacted in %d ms" % (self.t*1000))
                    self.findReaction = False
            if GeneratePlots:
                self.P1.append(v1)
                self.P2.append(v2)
                self.A.append(angle)
                self.T.append(self.t)
        else:
            if self.evaluating:
                self.LogResult()
                if self.DoPlot and GeneratePlots:
                    self.plot()
                self.evaluating = False
                return False
        self.t += dt
        return True
                
    def plot(self):
        figure, axis = plt.subplots(2, 1)
        axis[0].plot(self.T,self.P1,'r')
        axis[0].plot(self.T,self.P2,'g')
        axis[0].set_ylabel('v [°/s]')
        axis[0].set_title('Velocities')
        axis[0].grid(True)
        axis[1].plot(self.T,self.A,'b')
        axis[1].set_title('Angle')
        axis[1].set_ylabel('angle [°]')
        axis[1].set_xlabel('time [s]')
        axis[1].grid(True)
        plt.suptitle('Fixation task marker [%s]' % self.Marker)
        figure.tight_layout()
        plt.show()

    def LogResult(self):
        self.File.write( "%d;%s;%f;%f;%f;%f;%f;%f;%d\n" % (self.TimeStamp*1000, self.Marker, self.Angle, self.Pitch, self.Yaw, self.Latency, self.foundSacc, self.foundBlink, self.Error))

def EvalData(Path, FileName, Segments):

    c = Counter()
    t = 0                       # elapsed time
    
    markerLast = ""

    AntiList3D = []
    AntiIndex3D = 0
        
    E = Evaluator()
    
    with open('logs/3D_Antisaccade_pseudorandom.csv', 'r') as file:
        reader3DAnti = csv.reader(file, delimiter = ',')
        next(reader3DAnti) # skip header
        
        for row in reader3DAnti:
            AntiList3D.append( row)
    
    
    with open('logs/2D_Prosaccade_pseudorandom.csv', 'r') as file2:
        reader2DPro = csv.reader(file2, delimiter = ',')
        next(reader2DPro) # skip header


        with open('logs/2D_Antisaccade_pseudorandom.csv', 'r') as file3:
            reader2DAnti = csv.reader(file3, delimiter = ',')
            next(reader2DAnti) # skip header

            with open(Path + '/' + FileName, 'w') as result:
                result.write("Timestamp;Marker;Angle;Pitch;Yaw;Latency_3degree;Latency_sacc;Latency_blink;Error\n")
                
                # Iterate rows    
                for seg in Segments:

                    Error = False                    
                    try:
                        seg[4] = scipy.signal.savgol_filter(seg[3], FilterWindow, 2, axis=-1, mode='interp', cval=0.0)
                    except:
                        result.write( "-1;%s;-1;-1;-1;-1;-1;-1;-1\n" % (''))
                        print( 'Filter Error')
                        print(seg[0])
                        print(seg[3])
                        Error = True
                        Nan=[]
                        for n in seg[3]:
                           if math.isnan(n):
                               Nan.append(1)
                           else:
                               Nan.append(0)
                        figure, axis = plt.subplots(2, 1)
                        axis[0].plot(seg[0],seg[3],'r')
                        axis[0].set_ylabel('v [°/s]')
                        axis[0].set_title('Velocities')
                        axis[0].grid(True)
                        axis[1].plot(seg[0],Nan,'b+')
                        axis[1].set_title('NAN')
                        axis[1].set_ylabel('isnan [0/1]')
                        axis[1].set_xlabel('time [s]')
                        axis[1].grid(True)
                        plt.suptitle('Filter Error')
                        figure.tight_layout()
                        plt.show()
                        
                    for idx in range(0,len(seg[0])):
                        row = seg[1][idx]
                        dt = seg[2][idx]
                        t = seg[0][idx]
                            
                        marker = row['Marker']                    # Marker
                    
                        # Found a marker
                        if marker != "" and marker !=markerLast:
                            markerLast = marker
                            # If we where looking for a reaction, seems there was not
                            
                            E = Evaluator(True,t,result,marker,c)
                            match = re.match(".\\d\\d(.)\\d", marker)
                            if match:
                                while not E.direction(next(reader2DPro)):
                                    pass
                            else:
                                match = re.match("2.\\d\\d(.)\\d", marker)
                                if match:
                                    while not E.direction(next(reader2DAnti),True):
                                        pass
                                else:
                                    match = re.match("3.\\d\\d(.)\\d", marker)
                                    if match:
                                        while not E.direction(AntiList3D[AntiIndex3D],True):
                                            pass
                                        AntiIndex3D = (AntiIndex3D + 1 ) % 48                            
                                    else:
                                        match = re.match("z\\d\\d.", marker)
                                        if match:                                
                                            E.fixation()
                                        else:
                                            E.inactive()
    
                        if not Error:    
                            E.evaluate(dt,seg[3][idx],seg[4][idx],float(row['Angle']),float(row['Pitch']),float(row['Yaw']),row)
    c.result()                
                                            


def SegmentFile( Path, FileName):


    AllData = [[],[],[],[],[],[]]
    
    Segments = []
    Segment = []

    InSegment = False
    SegmentAdd = 0
    TimeStamp = 0
    LastTimeStamp = 0
    SegLen = 0
    markerLast = 0
    LastVector = 0
    lastv = 0
    t = 0
    Init = True
    for row in Logfile.File(Path + '/' + FileName,';', Logfile.EyeRow):

        if Init:
            match = re.match('.*-(\\d*)\.(\\d*).(\\d*):(\d*)', row['UETime'])
            if match:
                h = int(match.group(1))
                m = int(match.group(2))
                s = int(match.group(3))
                ms = int(match.group(4))
                LastTimeStamp = s+60*(m+60*h)+(ms/1000)
                Init = False
        else:            
            marker = row['Marker']                    # Marker
    
            match = re.match('.*-(\\d*)\.(\\d*).(\\d*):(\d*)', row['UETime'])
            if match:
                h = int(match.group(1))
                m = int(match.group(2))
                s = int(match.group(3))
                ms = int(match.group(4))
#                print( '%d %d %d %d %f' % (h,m,second,ms,s+60*(minute+60*hour)+(ms/1000)))
                TimeStamp = s+60*(m+60*h)+(ms/1000)
                dt = TimeStamp - LastTimeStamp
                LastTimeStamp = TimeStamp
                t += dt
        
            # Found a marker
            if marker != "" and marker !=markerLast:
                Segment = []
                for col in AllData:               
                    Segment.append( col[-(FilterWindow):] )
                InSegment = True
                markerLast = marker
                SegLen = 0
                lastv = 0
                
            AllData[0].append( t )
            AllData[1].append( row)
            AllData[2].append( dt )
            vel = Logfile.AngleVector(LastVector,row.Direction())/dt
            try:
                if math.isnan(vel):
                    AllData[3].append(lastv)
                else:
                    AllData[3].append(vel)
                    lastv = vel
            except:
                AllData[3].append(vel)
    
            AllData[5].append( Logfile.AngleVector(LastVector,row.Direction()))
            
            if InSegment or SegmentAdd>0:
                Segment[0].append( t )
                Segment[1].append( row)
                Segment[2].append( dt )
                if InSegment:
                    Segment[3].append( Logfile.AngleVector(LastVector,row.Direction())/dt)
                else:
                    Segment[3].append( AllData[3][-1])
    
                Segment[5].append( Logfile.AngleVector(LastVector,row.Direction()))
                if SegLen<1:
                    SegLen += dt
                else:
                    if InSegment:
                        SegmentAdd = FilterWindow + 1
                    InSegment = False
                if not InSegment:
                    SegmentAdd -= 1
                    if SegmentAdd==0:
                        Segments.append( Segment  )
                        
            LastVector = row.Direction()           
                
    return Segments

    
#    maxi = 0
#    maxi2 = 0
#    Plot = []
#    for r in range(0,len(Time)):
#        #print( '%f   %f   %f   %f  %f' % (Time[r],Data[r],Data2[r],DeltaT[r],DiffAngle[r] ))
#        if maxi<Data1[r]:
#            maxi=Data1[r]
#        maxi2 = max(Data2[r],maxi2)
#        Plot.append(Data1[r])
#        if Data1[r]>500:
#            print( Data1[r])
    
#    print(maxi)
#    print(maxi2)
    
#    # disabling the offset on y axis
#    ax = plt.gca()
#    ax.ticklabel_format(useOffset=False)

    
#    plt.plot(Data1,'r+')
#    #plt.plot(Time,Data2)
#    plt.show()

## Loop through folder            
for file in os.listdir(InFolderName):
#    try:
#        EvalFile(FolderName,file,of)
#    except:
#        pass
#     EvalData(OutFolderName,file,EvalFile(InFolderName,file))
    try:
        EvalData(OutFolderName,file,SegmentFile(InFolderName,file))
    except:
        pass
            
            
#of.close()


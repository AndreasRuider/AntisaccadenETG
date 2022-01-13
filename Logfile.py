# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 12:14:21 2021

@author: rua21789
"""

import csv
import numpy

from scipy.spatial.transform import Rotation

#

## Calculate the angle between two vectors
##
def AngleVector(v1,v2):
    return numpy.rad2deg(numpy.arccos(numpy.dot(v1,v2)/numpy.linalg.norm(v1)/numpy.linalg.norm(v2)))


## Calculate the Distance between v1 and v2 (v2 adjusted to same length as v1)
##
def DistVector(v1,v2):
    return numpy.linalg.norm(numpy.subtract(v1,numpy.multiply(numpy.divide(v2,numpy.linalg.norm(v2)),numpy.linalg.norm(v1))))


## Class for row in eye tracking logfile
class EyeRow:
    def __init__(self, row_raw, head):
        self.row = {}
        for index,item in enumerate(row_raw):
            if index < len(head):
                self.row[head[index]] = item

    ## Calculate the Vector to a target.
    ##
    def LookAtTarget(self,target):
    
        eyeOriginLeft = numpy.multiply([float(self.row['Left Origin Z']),float(self.row['Left Origin X']),float(self.row['Left Origin Y'])],100)
        eyeOriginRight = numpy.multiply([float(self.row['Right Origin Z']),float(self.row['Right Origin X']),float(self.row['Right Origin Y'])],100)
        origin = numpy.divide(numpy.add(eyeOriginLeft,eyeOriginRight),2000)

        center = [float(self.row[target + ' X']),float(self.row[target + ' Y']),float(self.row[target + ' Z'])]
        if center[0]==150 and center[1]==0 and center[2]==0:
            return numpy.subtract(center,origin)
        else:
            camPos = [float(self.row['Camera X']),float(self.row['Camera Y']),float(self.row['Camera Z'])]
            camQuat = [float(self.row['Camera Rot X']),float(self.row['Camera Rot Y']),float(self.row['Camera Rot Z']),float(self.row['Camera Rot W'])]
            r = Rotation.from_quat(camQuat)
            return numpy.subtract(r.apply(numpy.subtract(center,camPos),True),origin)

    ## Get the eye beam direction
    def Direction(self):
        eyeDirectionLeft = numpy.multiply([float(self.row['Left Gaze Z']),-float(self.row['Left Gaze X']),float(self.row['Left Gaze Y'])],100)
        eyeDirectionRight = numpy.multiply([float(self.row['Right Gaze Z']),-float(self.row['Right Gaze X']),float(self.row['Right Gaze Y'])],100)
        return numpy.divide(numpy.add(eyeDirectionLeft,eyeDirectionRight),2)
    
    def Origin(self):
        eyeOriginLeft = numpy.multiply([float(self.row['Left Origin Z']),float(self.row['Left Origin X']),float(self.row['Left Origin Y'])],100)
        eyeOriginRight = numpy.multiply([float(self.row['Right Origin Z']),float(self.row['Right Origin X']),float(self.row['Right Origin Y'])],100)
        return numpy.divide(numpy.add(eyeOriginLeft,eyeOriginRight),2000)

    ## Get the angle from logfile
    def Angle(self):
        return self.row['Angle']
    
    def __getitem__(self,item):
        return self.row[item]
    
    def print(self):
        print(self.row)

## Class for row in eye tracking logfile
class EyeRowCS:
    def __init__(self, row_raw, head):
        self.row = {}
        for index,item in enumerate(row_raw):
            if index < len(head):
                self.row[head[index]] = item

    ## Calculate the Vector to a target.
    ##
    def LookAtTarget(self,target):
    
#        eyeOriginLeft = numpy.multiply([float(self.row['Left Origin Z']),float(self.row['Left Origin X']),float(self.row['Left Origin Y'])],100)
#        eyeOriginRight = numpy.multiply([float(self.row['Right Origin Z']),float(self.row['Right Origin X']),float(self.row['Right Origin Y'])],100)
#        origin = numpy.divide(numpy.add(eyeOriginLeft,eyeOriginRight),2000)

        center = [float(self.row[target + ' X']),float(self.row[target + ' Y']),float(self.row[target + ' Z'])]
        if center[0]==150 and center[1]==0 and center[2]==0:
            return numpy.subtract(center,origin)
        else:
            camPos = [float(self.row['Camera X']),float(self.row['Camera Y']),float(self.row['Camera Z'])]
            camQuat = [float(self.row['Camera Rot X']),float(self.row['Camera Rot Y']),float(self.row['Camera Rot Z']),float(self.row['Camera Rot W'])]
            r = Rotation.from_quat(camQuat)
            return numpy.subtract(r.apply(numpy.subtract(center,camPos),True),origin)

    ## Get the eye beam direction
    def Direction(self):
        eyeDirectionLeft = numpy.multiply([float(self.row['gazeOut_rz']),-float(self.row['gazeOut_rx']),float(self.row['gazeOut_ry'])],100)
        eyeDirectionRight = numpy.multiply([float(self.row['gazeOut_lz']),-float(self.row['gazeOut_lx']),float(self.row['gazeOut_ly'])],100)
        return numpy.divide(numpy.add(eyeDirectionLeft,eyeDirectionRight),2)
    
    def Origin(self):
        eyeOriginLeft = numpy.multiply([float(self.row['Left Origin Z']),float(self.row['Left Origin X']),float(self.row['Left Origin Y'])],100)
        eyeOriginRight = numpy.multiply([float(self.row['Right Origin Z']),float(self.row['Right Origin X']),float(self.row['Right Origin Y'])],100)
        return numpy.divide(numpy.add(eyeOriginLeft,eyeOriginRight),2000)

    ## Get the angle from logfile
    def Angle(self):
        return self.row['Angle']
    
    def __getitem__(self,item):
        return self.row[item]
    
    def print(self):
        print(self.row)


## Class for evaluating Logfiles
class File:
    def __iter__(self):
        return self
        
    def __init__(self, fileName, d, C,skip=1):
        f = open(fileName, 'r')
        self.reader = csv.reader(f, delimiter = d)
        self.head = []
        self.rowC = C

        while skip>0:
            next(self.reader)
            skip -= 1
        row = next(self.reader)    
        for item in row:
            self.head.append( item)
        self.head[0] = 'UETime'
    
    def __next__(self):
        self.row = next(self.reader)
        return self.rowC(self.row,self.head)
        
    def get(self,C):
        return C(self.row,self.head)



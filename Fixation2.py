# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 12:14:21 2021

@author: rua21789
"""

import Logfile
import os
import re
import csv

# Setup Variables
FixationAngle = 3
ErrorAngle = 3
Interval = 1
MarkerDistance = 3
FolderName = 'logs/test2'
OutFileName = 'Gaze10.csv'


class AntiList3D:
    def __init__(self):
        self.List = []
        self.index = 0
        with open('logs/3D_AttentionFixation_pseudorandom_new.csv', 'r') as file:
            reader3DAnti = csv.reader(file, delimiter = ',')
            next(reader3DAnti) # skip header
            
            for row in reader3DAnti:
                self.List.append( row)
                
    def __next__(self):
        idx = self.index
        if self.index+1 == len(self.List):
            self.index = 0
        else:
            self.index = self.index+1
        return self.List[idx]


if os.path.exists(OutFileName):
    of = open(OutFileName, 'a')
else:
    Head = 'ID';
    of = open(OutFileName, 'w')
    for i in range(1,3):
        Head += '\tNonFixation_k%d' % i
        List = AntiList3D()
        for j in range(1,25):
            item = next(List)
            Head += '\t%s_Duration_k%d\t%s_Aft_Error_k%d' % (item[3],i,item[3],i)
    of.write(Head+'\n')


def EvalFile( Path, FileName, result):
    VP = FileName.split('_')[2].split('.')[0]
    print(VP)
    result.write(VP)
    TString = ''
    dt = 0
    TimeStamp = 0
    LastTimeStamp = 0
    FixTimeStamp = 0
#    LastMarkerTimeStamp = -1
    NonFixationTime = 0
    TargetFixationTime = 0
    AftErrorTime = 0
    
    checkFixation = False
    checkTarget = False
    
    Convert = { 'B':'Bottom','T':'Top','L':'Left','R':'Right',}
    List3D = AntiList3D()
    
    TrialNum = 0
    
    maxAngle = 0
    minAngle = 9999
    maxDistance = 0
    
    Target = ''
    marker = ''
    
    ListItem = next(List3D)
    searchMarker = ListItem[3]
    for row in Logfile.File(Path + '/' + FileName,';', Logfile.EyeRow):
    
        # Timestamp in Zeit umrechnen
        #[2020.12.18-11.53.59:841][309]
        match = re.match('.*-(\\d*)\.(\\d*).(\\d*):(\d*)', row['UETime'])
        if match:
            h = int(match.group(1))
            m = int(match.group(2))
            s = int(match.group(3))
            ms = int(match.group(4))
#            print( '%d %d %d %d %f' % (h,m,second,ms,s+60*(minute+60*hour)+(ms/1000)))
            TimeStamp = s+60*(m+60*h)+(ms/1000)
            dt = TimeStamp - LastTimeStamp
            LastTimeStamp = TimeStamp
            

        if row['Marker'] == searchMarker:
            marker = searchMarker
            #print(searchMarker)
            # Blicktarget vector
            Target = Convert[ListItem[1]]
            checkFixation = True
            checkTarget = True
            TrialNum += 1
            ListItem = next(List3D)
            searchMarker = ListItem[3]
            FixTimeStamp = TimeStamp

#                if LastMarkerTimeStamp>0:
#                    print(LastMarkerTimeStamp-TimeStamp)
#                LastMarkerTimeStamp=TimeStamp

        if Target!='':
            realTarget = row.LookAtTarget(Target)
            realCenter = row.LookAtTarget('Center')
            direction = row.Direction()
        
        if checkFixation:
            maxAngle = max(maxAngle,float(row.Angle()))
            if Logfile.AngleVector(realCenter,direction)>FixationAngle:
                NonFixationTime += dt
#                if float(row.Angle())>3:
#                    print('%s / %f / %f' % (row.Angle(),Logfile.AngleVector(realCenter,direction),Logfile.AngleVector(realTarget,direction)))
                    #row.print()
                maxDistance = max(maxDistance,Logfile.DistVector(realCenter,direction))
            
            

        if TimeStamp-FixTimeStamp<Interval:
            minAngle = min(minAngle,Logfile.AngleVector(realTarget,direction))              
            if Logfile.AngleVector(realTarget,direction)<FixationAngle:
                print("Fixation on Target: %f %s %s %s %s" % (TimeStamp,row['UETime'],Target,row['Pitch'],row['Yaw']))
                TargetFixationTime+=dt   
            if (Target=='Left' and float(row['Yaw'])>ErrorAngle) or (Target=='Right' and float(row['Yaw'])<-ErrorAngle) or (Target=='Bottom' and float(row['Pitch'])>ErrorAngle) or (Target=='Top' and float(row['Pitch'])<-ErrorAngle):
                print("Error on Target: %f %s %s %s %s" % (TimeStamp,row['Angle'],row['Yaw'],row['Pitch'],row['UETime']))
                AftErrorTime += dt
                
        else:
            if checkTarget:
                TString += '\t%f\t%f' % (TargetFixationTime,AftErrorTime)
                TargetFixationTime = 0
                AftErrorTime = 0
                checkTarget = False
            if (TrialNum==24 or TrialNum==48) and TimeStamp-FixTimeStamp>MarkerDistance and checkFixation:
                print( 'Hit MarkerDistance after last marker of block.\n'
                      'MaxAngle from center was: %f\n'
                      'MinAngle from targets was: %f' % (maxAngle,minAngle))
                print( 'NonFixationTime = %f\n' % NonFixationTime)
                checkFixation=False
                result.write( '\t%f%s' %(NonFixationTime,TString))
                NonFixationTime = 0
                minAngle = 9999
                maxAngle = 0
                TString = ''
    of.write('\n')


## Loop through folder            
for file in os.listdir(FolderName):
    try:
        EvalFile(FolderName,file,of)
    except:
        pass
            
of.close()

"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
TV Channels module
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

import os
import platform

# Video carrier frequencies for PAL B/G TV standard
frequencyDict = {
"C02" : 48.25,
"C03" : 55.25,
"C04" : 62.25,
"S02" : 112.25,
"S03" : 119.25,
"S04" : 126.25,
"S05" : 133.25,
"S06" : 140.25,
"S07" : 147.25,
"S08" : 154.25,
"S09" : 161.25,
"S10" : 168.25,
"C05" : 175.25,
"C06" : 182.25,
"C07" : 189.25,
"C08" : 196.25,
"C09" : 203.25,
"C10" : 210.25,
"C11" : 217.25,
"C12" : 224.25,
"S11" : 231.25,
"S12" : 238.25,
"S13" : 245.25,
"S14" : 252.25,
"S15" : 259.25,
"S16" : 266.25,
"S17" : 273.25,
"S18" : 280.25,
"S19" : 287.25,
"S20" : 294.25,
"S21" : 303.25,
"S22" : 311.25,
"S23" : 319.25,
"S24" : 327.25,
"S25" : 335.25,
"S26" : 343.25,
"S27" : 351.25,
"S28" : 359.25,
"S29" : 367.25,
"S30" : 375.25,
"S31" : 383.25,
"S32" : 391.25,
"S33" : 399.25,
"S34" : 407.25,
"S35" : 415.25,
"S36" : 423.25,
"S37" : 431.25,
"S38" : 439.25,
"S39" : 447.25,
"S40" : 455.25,
"S41" : 463.25,
"C21" : 471.25,
"C22" : 479.25,
"C23" : 487.25,
"C24" : 495.25,
"C25" : 503.25,
"C26" : 511.25,
"C27" : 519.25,
"C28" : 527.25,
"C29" : 535.25,
"C30" : 543.25,
"C31" : 551.25,
"C32" : 559.25,
"C33" : 567.25,
"C34" : 575.25,
"C35" : 583.25,
"C36" : 591.25,
"C37" : 599.25,
"C38" : 607.25,
"C39" : 615.25,
"C40" : 623.25,
"C41" : 631.25,
"C42" : 639.25,
"C43" : 647.25,
"C44" : 655.25,
"C45" : 663.25,
"C46" : 671.25,
"C47" : 679.25,
"C48" : 687.25,
"C49" : 695.25,
"C50" : 703.25,
"C51" : 711.25,
"C52" : 719.25,
"C53" : 727.25,
"C54" : 735.25,
"C55" : 743.25,
"C56" : 751.25,
"C57" : 759.25,
"C58" : 767.25,
"C59" : 775.25,
"C60" : 783.25,
"C61" : 791.25,
"C62" : 799.25,
"C63" : 807.25,
"C64" : 815.25,
"C65" : 823.25,
"C66" : 831.25,
"C67" : 839.25,
"C68" : 847.25,
"C69" : 855.25
}

#-----------------------
# Channel playlist
#----------------------- 

import xml.etree.ElementTree as ET

class TvChannel():
    def __init__(self):
        self.frequencyName = None
        self.frequencyMHz = None
        self.name  = None
    def print(self):
        print("TV channel: {fn} | {f:.2f} MHz | {n}".format(fn=self.frequencyName, f=self.frequencyMHz, n=self.name))

class TvChannels():
    def __init__(self):
        self.fileChannelList="channels.xml"
        self.channel = 0
        self.nChannel = 0
        self.channels = []
        
    def read(self):
        isFile = os.path.isfile(self.fileChannelList)
        if isFile:
            tree=ET.parse(self.fileChannelList)
            root=tree.getroot()
            self.channel=int(root[0].text)
            self.channels = []
            for s in root.findall('tvChannel'):
                self.channels.append(TvChannel())  
                self.nChannel=len(self.channels)
                self.channels[self.nChannel-1].frequencyName=s[0].text
                self.channels[self.nChannel-1].frequencyMHz=float(s[1].text)
                self.channels[self.nChannel-1].name=s[2].text
        else:
            newChannel=TvChannel()
            newChannel.frequencyName="C32"
            newChannel.frequencyMHz=559.25
            newChannel.name="Unknown Channel"  
            self.channels=[]
            self.channels.append(newChannel)
            self.nChannel=1
            self.channel=0
            
    def write(self):        
        root = ET.Element("channelList")
        Playing=ET.SubElement(root,"playing").text="{}".format(self.channel)
        for i in range (self.nChannel):
            Channel=ET.SubElement(root,"tvChannel")
            ET.SubElement(Channel,"frequencyName").text="{fName}".format(fName=self.channels[i].frequencyName)
            ET.SubElement(Channel,"frequencyMHz").text="{freq:.2f}".format(freq=self.channels[i].frequencyMHz)
            ET.SubElement(Channel,"name").text=self.channels[i].name
        tree = ET.ElementTree(root)
        tree.write(self.fileChannelList,encoding="utf-8", xml_declaration=True)

        from shutil import which
        if which('xml') :
            cmd="xml format {file} > {file}.1".format(file=self.fileChannelList)
            print(cmd)
            os.system(cmd)
            cmd="mv {file}.1 {file} ".format(file=self.fileChannelList)
            print(cmd)
            os.system(cmd)
            
    def add_channel(self,tvChannel):        
        channelToAdd="{fName} : {freq:6.2f} MHz : {name}".format(fName=tvChannel.frequencyName,freq=tvChannel.frequencyMHz,name=tvChannel.name)
        print (channelToAdd)
        newTvChannel=TvChannel()
        newTvChannel.frequencyName=tvChannel.frequencyName
        newTvChannel.frequencyMHz=tvChannel.frequencyMHz
        newTvChannel.name=tvChannel.name
        iFreq=0
        for i in range(len(self.channels)):
            if newTvChannel.frequencyMHz >= self.channels[i].frequencyMHz :
                iFreq=i+1
        if iFreq==self.nChannel:
            self.channels.append(newTvChannel)
            
        else:
            self.channels.insert(iFreq,newTvChannel)

        self.nChannel=self.nChannel+1
        self.channel=iFreq
        self.print()

    def remove_channel(self,channel):
        if self.nChannel > 1 :
            del self.channels[channel]
            if channel == self.nChannel-1:
                self.channel = self.channel-1
            self.nChannel=len(self.channels)
        self.print()
            
    def update_channel(self,channel,tvChannel):
        self.channels[channel].frequencyName=tvChannel.frequencyName
        self.channels[channel].frequencyMHz=tvChannel.frequencyMHz
        self.channels[channel].name=tvChannel.name
        self.print()
    
    def print(self):
        print("Tv channels:")
        print(' # of Channel: {}'.format(self.nChannel))
        for i in range (self.nChannel):
            print(" {i:2d} > {fn} : {f:.2f} MHz : {n}".format(i=i, fn=self.channels[i].frequencyName, f=self.channels[i].frequencyMHz, n=self.channels[i].name))
        print(" Selected channel:",self.channel)

"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
Audio control module
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

from pulsectl import Pulse, PulseVolumeInfo

class AudioControl():
    def __init__(self, audioSourceName):
        self.sourceName=audioSourceName
        self.audioSource=None
        self.pulse=Pulse()
        self.n_channels=1
        self.volume=0
        self.get_source(self.sourceName)
        if self.audioSource :
            self.get_volume()
        print("Audio source:",self.sourceName)
    def get_source(self,sourceName): 
        try:
            self.audioSource=self.pulse.get_source_by_name(sourceName)
        except:
            self.audioSource=None
    def get_volume(self):
        volume = self.audioSource.volume
        self.volume=volume.values
        self.n_channels = len(volume.values)
    def set_volume(self,volume):
        set_volume = PulseVolumeInfo(volume, self.n_channels)  
        if self.audioSource :
            self.pulse.source_volume_set(self.audioSource.index,set_volume)
    def mute(self):
        self.pulse.source_mute(self.audioSource.index,mute=True)
    def unmute(self):
        self.pulse.source_mute(self.audioSource.index,mute=False)
    def print_volume(self):
        self.get_volume()
        print("Audio volume:",self.volume)

class AudioSourceList(object):
    def __init__(self):
        self.pulse=Pulse()
        self.audioSources=self.pulse.source_list()
        self.nameList = [self.audioSources[i].name for i in range(len(self.audioSources))]
        self.descriptionList = [self.audioSources[i].description for i in range(len(self.audioSources))]
        self.selected=-1
        self.indexSelected=-1
    def select_by_name(self,name):
        self.selected=-1
        self.indexSelected=-1
        for i in range(len(self.audioSources)) :
            if self.nameList[i]== name :
                self.selected=i
                self.indexSelected=self.audioSources[i].index
                break
    def select(self,index):
        self.selected=index
        self.indexSelected=self.audioSources[index].index
    def print(self):
        for i in range(len(self.audioSources)) :
            if i == self.selected :
                print("* {d} | {n} | {i}".format(d=self.descriptionList[i], n=self.nameList[i],i=self.audioSources[i].index))
            else :
                print("  {d} | {n} | {i}".format(d=self.descriptionList[i], n=self.nameList[i],i=self.audioSources[i].index))
                

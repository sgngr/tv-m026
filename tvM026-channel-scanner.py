#!/usr/bin/env python
"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
Channel Scanner
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

#===============================================================================

from m026Device import *
m026 = M026Device()
m026.find()
if m026.usbDev == None :
    print ("AVerTV USB2.0 not found!") 
    exit()
print ("AVerTV USB2.0 found!") 

m026.open() 
m026.gpio_led(True)
print("----------------------------------------------------------------")

#===============================================================================

from m026Settings import *

tvM026Settings=Settings()
fileSettings=tvM026Settings.fileSettings

isFile = os.path.isfile(fileSettings)
if isFile:
    tvM026Settings.read(fileSettings)
else:
    tvM026Settings.write(fileSettings) 

tvM026Settings.print()
print("----------------------------------------------------------------")

frameTv=Frame(Position(tvM026Settings.m026TvCaptureStartX,tvM026Settings.m026TvCaptureStartY),Position(tvM026Settings.m026TvCaptureEndX,tvM026Settings.m026TvCaptureEndY))
m026.vdVideoStandardTv = tvM026Settings.m026TvVideoStandard
m026.vdCaptureFrameTv=frameTv

m026.video_decoder_set_video_standard(m026.vdVideoStandardTv)

m026.video_decoder_get_video_standard()
m026.video_decoder_status_video_standard()

def video_size_class(videoStandard):
    videoSizeClass="576"
    if videoStandard==VIDEO_STANDARD_NTSC_M_J :
        videoSizeClass="480"
    if videoStandard==VIDEO_STANDARD_PAL_B_G_H_I_N :
        videoSizeClass="576"      
    if videoStandard==VIDEO_STANDARD_PAL_M :
        videoSizeClass="480"             
    if videoStandard==VIDEO_STANDARD_PAL_Nc :
        videoSizeClass="576"
    if videoStandard==VIDEO_STANDARD_NTSC :
        videoSizeClass="480"  
    if videoStandard==VIDEO_STANDARD_SECAM :
        videoSizeClass="576"
    print("Video size class:",videoSizeClass)
    return videoSizeClass

videoSizeClass=video_size_class(m026.vdVideoStandardTv)

#===============================================================================

from tvChannels import *

tvChannels = TvChannels()
tvChannel = TvChannel()

tvChannels.read()
# tvChannels.print()

newTvChannels=TvChannels()

for i in range(tvChannels.nChannel) :
    newTvChannels.add_channel(tvChannels.channels[i])

newTvChannels.print()
newTvChannels.channel=0

print("----------------------------------------------------------------")
    
#===============================================================================

from m026AudioControl import *

if tvM026Settings.audioSource == None :
    audioControl=AudioControl('Unknown')
else :
    audioControl=AudioControl(tvM026Settings.audioSource)

if audioControl.audioSource == None :
    print("Audio source isn't set!")
if audioControl.audioSource :
    print("Audio source is set.")
    
audioSources=AudioSourceList()  

if audioControl.audioSource :
    audioSources.select_by_name(audioControl.sourceName)
    
print("----------------------------------------------------------------")

#===============================================================================

from m026Stream import *

streamDevice=StreamDevice(tvM026Settings.v4l2Device)
streamer=Streamer(tvM026Settings.streamer,streamDevice.v4l2Device)

#===============================================================================

m026.set_audio_source(AUDIO_SOURCE_TV_TUNER)

if newTvChannels.nChannel > 0 :
    tvChannel=newTvChannels.channels[0]
    frequencyMHz=tvChannel.frequencyMHz
else :
    frequencyMHz=frequencyDict[list(frequencyDict)[0]]
m026.set_tv_tuner(frequencyMHz)

m026.set_video_source(VIDEO_SOURCE_TV)

streamer.terminate()
if videoSizeClass=="576" :
    m026.set_video_capture(0,0,720,576)
else :
    m026.set_video_capture(0,0,720,480)
streamer.start(m026.videoCaptureSize.width,m026.videoCaptureSize.height)    

#===============================================================================

from m026Vlc import *

vlcApp = VlcApp(None,None)
if audioControl.audioSource :
    audioSourceName=audioControl.sourceName
    audioMedia='pulse://'+audioSourceName
    vlcApp.set_audio_media(audioMedia)

playerVolume=tvM026Settings.audioPlayerVolume
print("Player volume:",playerVolume)
vlcApp.audioPlayer.audio_set_volume(playerVolume)  
vlcApp.audioPlayer.play()

videoMedia='v4l2://'+tvM026Settings.v4l2Device
vlcApp.set_video_media(videoMedia)

vlcApp.videoPlayer.video_set_aspect_ratio('16:9')
vlcApp.videoPlayer.video_set_scale(1.0)

#===============================================================================

from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont

#=============================================================================== 

global channel
channel=0

class DialogChannelListSave(object):
    def __init__(self, parent,fileChannelList):
        self.yesNo = 'No'
        self.root=Toplevel(parent)
        self.root.bind('<Key>', self.key)  
          
        p1 = PhotoImage(file='icons/tvM026.png')
        self.root.iconphoto(False,p1)  
        self.root.title("Save channel list")    
   
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        
        self.helv10b = tkFont.Font(family='Helvetica',size=10, weight='bold')
        
        self.frameChannelListSave=ttk.Frame(self.root)
        self.frameChannelListSave['padding']=(10,10,10,8)
        self.frameChannelListSave['relief'] = 'sunken'
        self.frameChannelListSave['width'] = 302
        self.frameChannelListSave.grid(padx=5, pady=5,sticky=tk.W+tk.N+tk.E+tk.S)
        
        self.frameChannelListSave.columnconfigure(0, minsize=141)
        self.frameChannelListSave.columnconfigure(1, minsize=141)
        
        msg="The file '{}' will be overwritten!" 
        msg=msg.format(fileChannelList)
        self.labelQuestion1 = ttk.Label(self.frameChannelListSave, text=msg)
        self.labelQuestion1['padding']=(5,5,5,0)
        self.labelQuestion1['font']=self.helv10b
        self.labelQuestion1.grid(row=0,columnspan=2)

        msg="Are you sure?"
        self.labelQuestion1 = ttk.Label(self.frameChannelListSave, text=msg)
        self.labelQuestion1['padding']=(5,0,5,5)
        self.labelQuestion1['font']=self.helv10b
        self.labelQuestion1.grid(row=1,columnspan=2)
    
        self.buttonYes = ttk.Button(self.frameChannelListSave, text="Yes", command=self.Yes)
        self.buttonYes.grid(row=2,column=0, padx=10, pady=5, sticky=tk.E)
        
        self.buttonNo = ttk.Button(self.frameChannelListSave, text="No", command=self.No)
        self.buttonNo.grid(row=2,column=1, padx=10, sticky=tk.W)
        self.buttonNo.focus()

        self.root.wait_visibility()
        self.root.grab_set()
        self.root.transient(parent)

    def key(self,event):
        k = event.keysym
        print("Key: {k}".format(k=k))
        if k == 'Escape':
            self.root.grab_release()
            self.root.destroy()  

    def Yes(self):
        self.yesNo = "Yes"
        self.root.grab_release()
        self.root.destroy()

    def No(self):
        self.yesNo = "No"
        self.root.grab_release()
        self.root.destroy()


class DialogChannelRemove(object):
    def __init__(self, parent,tvChannels):
        self.yesNo = 'No'
        self.root=Toplevel(parent)
        self.root.bind('<Key>', self.key)  
        p1 = PhotoImage(file='icons/tvM026.png')
        self.root.iconphoto(False,p1)  
        self.root.title("Remove channel")    
        self.root.geometry('312x119')   
            
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        self.helv10b = tkFont.Font(family='Helvetica',size=10, weight='bold')
        
        self.frameChannelRemove=ttk.Frame(self.root)
        self.frameChannelRemove['padding']=(10,10,10,8)
        self.frameChannelRemove['relief'] = 'sunken'
        self.frameChannelRemove['width'] = 302
        self.frameChannelRemove.grid(padx=5, pady=5,sticky=tk.W+tk.N+tk.E+tk.S)
        
        self.frameChannelRemove.columnconfigure(0, minsize=141)
        self.frameChannelRemove.columnconfigure(1, minsize=141)
        
        msg="Are you sure to remove the channel"
        self.labelQuestion1 = ttk.Label(self.frameChannelRemove, text=msg)
        self.labelQuestion1['padding']=(5,5,5,0)
        self.labelQuestion1['font']=self.helv10b
        self.labelQuestion1.grid(row=0,columnspan=2)
        
        msg="{fName} : {freq:6.2f} MHz : {name}" 
        msg=msg.format(fName=tvChannels.channels[tvChannels.channel].frequencyName,freq=tvChannels.channels[tvChannels.channel].frequencyMHz,name=tvChannels.channels[tvChannels.channel].name)
        
        self.labelQuestion2 = ttk.Label(self.frameChannelRemove, text=msg)
        self.labelQuestion2['padding']=(5,0,5,5)
        self.labelQuestion2['font']=self.helv10b
        self.labelQuestion2.grid(row=1,columnspan=2)                
               
        self.buttonYes = ttk.Button(self.frameChannelRemove, text="Yes", command=self.Yes)
        self.buttonYes.focus()
        self.buttonYes.grid(row=2,column=0, padx=10, pady=5, sticky=tk.E)
        
        self.buttonNo = ttk.Button(self.frameChannelRemove, text="No", command=self.No)
        self.buttonNo.grid(row=2,column=1, padx=10, sticky=tk.W)

        self.root.wait_visibility()
        self.root.grab_set()
        self.root.transient(parent)
        self.parent = parent

    def key(self,event):
        k = event.keysym
        print("Key: {k}".format(k=k))
        if k == 'Escape':
            self.root.grab_release()
            self.root.destroy()  

    def Yes(self):
        self.yesNo = "Yes"
        self.root.grab_release()
        self.root.destroy()

    def No(self):
        self.yesNo = "No"
        self.root.grab_release()
        self.root.destroy()

class TvM026ChannelScanner(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.grid()
        
        self.master.bind('<Key>', self.handle_key)
        self.master.protocol("WM_DELETE_WINDOW", self.delete)
        self.master.title('tvM026 channel scanner')
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
    
        self.helv10 = tkFont.Font(family='Helvetica',size=10, weight='normal')
        self.helv10b = tkFont.Font(family='Helvetica',size=10, weight='bold')
        
        self.style.configure('TCheckbutton', indicatorsize='13')
        self.style.configure('TCheckbutton', indicatormargin='0 0 2 4')
        self.style.map("TCheckbutton",
            foreground=[('pressed', 'red'), ('active', 'blue')],
            background=[('pressed', '!disabled', ''), ('active', '#dcdad5')]
        )

        self.style.configure('TRadiobutton', indicatorsize='12')
        self.style.configure('TRadiobutton', indicatormargin='0 0 2 4')
        self.style.map("TRadiobutton",
            background=[ ('active', '#dcdad5')]
        )

        self.imgChannelPrev=PhotoImage(file='icons/media-skip-backward.png')
        self.imgChannelNext=PhotoImage(file='icons/media-skip-forward.png')
        self.imgChannelRemove=PhotoImage(file='icons/list-remove.png')
        self.imgChecked=PhotoImage(file='icons/checkmark.png')
        self.imgSave=PhotoImage(file='icons/save.png')

        self.videoSizeClass="576"
                
        self.indexVideoStandard=int(m026.vdVideoStandard/2)
        self.videoStandardList=["Autoswitch", "NTSC (M,J)", "PAL (B,G,H,I,N)", "PAL (M)", "PAL (Nc)", "NTSC (4.43)", "SECAM  (B, D, G, K, K1, L)"]
        
        self.CreateWidgets()
        
        if newTvChannels.nChannel == 0 : 
            self.disable_channel_actions()
        self.gui_update_channel_list()
        self.gui_update_channel_name()
        
        self.set_video_size_class(m026.vdVideoStandard)
        if self.videoSizeClass=="576" :
            self.labelVideoSize["text"]="720x576"
            m026.set_video_capture(0,0,720,576)
        else :
            self.labelVideoSize["text"]="720x480"
            m026.set_video_capture(0,0,720,480)
        
        m026.get_video_capture()
        
        self.master.wait_visibility()
        
        if self.videoSizeClass=="576" :
            self.canvasVideo['height']=576       
            self.canvasVideo['width']=576*16/9-4
        else :
            self.canvasVideo['height']=480+8       
            self.canvasVideo['width']=(480+8)*16/9-4
        vlcApp.videoPlayer.video_set_scale(1.0)
   
    def CreateWidgets(self):
        
        self.frameVideo = ttk.Frame(self)
        self.frameVideo['relief'] = 'raised'  
        self.frameVideo.grid(padx=2,pady=2)

        self.canvasVideo = tk.Canvas(self.frameVideo, width=m026.videoCaptureSize.height*16/9, height=m026.videoCaptureSize.height,bg='black')  
        self.canvasVideo.grid(row=0,column=0,padx=(2,2),pady=(2,2),sticky=tk.EW)
        h = self.canvasVideo.winfo_id()
        vlcApp.videoPlayer.play()
        vlcApp.videoPlayer.set_xwindow(h)

        self.frameControl = ttk.Frame(self)
        self.frameControl['relief'] = 'raised'
        self.frameControl['padding']=(4,4,4,4)
        self.frameControl.grid(row=0,column=1,sticky=tk.NS)

        self.frameVideoStandard = ttk.Frame(self.frameControl)
        self.frameVideoStandard['relief'] = 'groove'
        self.frameVideoStandard['padding']=(2,2,2,4)
        self.frameVideoStandard.grid(row=0,sticky=tk.N+tk.E+tk.S+tk.W)
        self.frameVideoStandard.columnconfigure(0, weight=100)

        labelVideoStandard=ttk.Label(self.frameVideoStandard)       
        labelVideoStandard['text']="Video Standard"  
        labelVideoStandard['font']=self.helv10b
        labelVideoStandard['justify']="center"
        labelVideoStandard['padding']=(42,0,42,0)
        labelVideoStandard['background']='#1e94f1'
        labelVideoStandard['foreground']='white'
        labelVideoStandard.grid(row=0,column=0, columnspan=2, padx=(2,2),pady=(2,2)) 

        self.videoStandardVar=IntVar()
        self.videoStandardVar.set(m026.vdVideoStandard)
        self.comboboxVideoStandards = ttk.Combobox(self.frameVideoStandard)
        self.comboboxVideoStandards.grid(row=1,column=0, columnspan=2, padx=(10,10),sticky=tk.EW)
        self.comboboxVideoStandards['state'] = 'readonly'
        self.comboboxVideoStandards['justify'] = 'center'
        self.comboboxVideoStandards['font'] = self.helv10
        self.comboboxVideoStandards.bind('<<ComboboxSelected>>', self.video_standard_selected)
        self.comboboxVideoStandards['values']=self.videoStandardList
        if self.indexVideoStandard >= 0 :
            self.comboboxVideoStandards.current(newindex=self.indexVideoStandard)
        else:
            self.comboboxVideoStandards.current(newindex=None)

        self.frameVideoStandard.columnconfigure(0, weight=50)
        self.frameVideoStandard.columnconfigure(1, weight=50)

        labelVideoStandardInfo1=ttk.Label(self.frameVideoStandard, text = "Video size:")
        labelVideoStandardInfo1.grid(row=2,column=0,padx=0,pady=4,sticky=tk.E)
        self.labelVideoSize=ttk.Label(self.frameVideoStandard, text = "?")
        self.labelVideoSize.grid(row=2,column=1, padx=0,pady=4,sticky=tk.W)

        self.frameScan = ttk.Frame(self.frameControl)
        self.frameScan['relief'] = 'groove'  
        self.frameScan['padding']=(2,2,2,2)
        self.frameScan.grid(row=1,padx=0,pady=(4,2),sticky=tk.N+tk.E+tk.S+tk.W)
        self.frameScan.columnconfigure(0, weight=100)

        labelChannel=ttk.Label(self.frameScan)       
        labelChannel['text']="Channel Scan"  
        labelChannel['font']=self.helv10b
        labelChannel['justify']="center"
        labelChannel['padding']=(46,0,46,0)
        labelChannel['background']='#1e94f1'
        labelChannel['foreground']='white'
        labelChannel.grid(row=0,column=0, columnspan=2, padx=(2,2),pady=(2,2))

        self.frameScan.columnconfigure(0, weight=50)
        self.frameScan.columnconfigure(1, weight=50)

        labelScanInfo1=ttk.Label(self.frameScan, text = "Channel:")
        labelScanInfo1.grid(row=1,column=0, padx=0,pady=4,sticky=tk.E)
        self.labelChannelName=ttk.Label(self.frameScan, text = "?")
        self.labelChannelName.grid(row=1,column=1,padx=2,pady=4,sticky=tk.W)

        labelScanInfo2=ttk.Label(self.frameScan, text = "Frequency:")
        labelScanInfo2.grid(row=2,column=0, padx=0,pady=4,sticky=tk.E)
        self.labelChannelFrequency=ttk.Label(self.frameScan, text = "? MHz")
        self.labelChannelFrequency.grid(row=2,column=1,padx=2,pady=4,sticky=tk.W)
        
        labelScanInfo3=ttk.Label(self.frameScan, text = "Line count:")
        labelScanInfo3.grid(row=3,column=0, padx=0,pady=4,sticky=tk.E)
        self.labelLineCount=ttk.Label(self.frameScan, text = "0")
        self.labelLineCount.grid(row=3,column=1,padx=2,pady=4,sticky=tk.W)

        labelScanInfo4=ttk.Label(self.frameScan, text = "H. Sync. locked:")
        labelScanInfo4.grid(row=4,column=0, padx=0,pady=4,sticky=tk.E)
        self.labelHSync=ttk.Label(self.frameScan, text = "No")
        self.labelHSync.grid(row=4,column=1,padx=2,pady=4,sticky=tk.W)

        labelScanInfo4=ttk.Label(self.frameScan, text = "V. Sync. locked:")
        labelScanInfo4.grid(row=5,column=0, padx=0,pady=4,sticky=tk.E)
        self.labelVSync=ttk.Label(self.frameScan, text = "No")
        self.labelVSync.grid(row=5,column=1,padx=2,pady=4,sticky=tk.W)

        self.frameScanControl = ttk.Frame(self.frameScan)
        self.frameScanControl.grid(row=6,column=0,columnspan =2, sticky=tk.EW)

        self.merge = BooleanVar()
        r1 = ttk.Radiobutton(self.frameScanControl, text='Merge', value=True, variable=self.merge,takefocus=False)
        r2 = ttk.Radiobutton(self.frameScanControl, text='New list', value=False, variable=self.merge,takefocus=False)
        r1['padding']=(0,5,0,0)
        r2['padding']=(0,5,0,0)
        r1.grid(row=0,column=0,padx=(5,0))
        r2.grid(row=0,column=1,padx=(5,0))
        self.merge.set(True)
        
        self.frameScanControl.columnconfigure(0, weight=1)
        self.frameScanControl.columnconfigure(1, weight=1)
        self.frameScanControl.columnconfigure(2, weight=100)

        self.imgScan=PhotoImage(file='icons/scan.png')
        self.labelScan=ttk.Label(self.frameScanControl)
        self.labelScan['image']=self.imgScan
        self.labelScan['text']="Scan"
        self.labelScan['padding']=(0,5,5,2)
        self.labelScan.bind("<Button-1>", self.scan_start)
        self.labelScan.grid(row=0,column=3,sticky=tk.SE)

        self.frameChannel = ttk.Frame(self.frameControl)
        self.frameChannel['relief'] = 'groove'  # flat, groove, raised, ridge, solid, or sunken
        self.frameChannel['padding']=(2,2,2,2)
        self.frameChannel.grid(row=2,padx=0,pady=(2,2),sticky=tk.EW)
        self.frameChannel.columnconfigure(0, weight=100)

        labelList=ttk.Label(self.frameChannel)       
        labelList['text']="Channel List"  
        labelList['font']=self.helv10b
        labelList['justify']="center"
        labelList['padding']=(50,0,50,0)
        labelList['background']='#1e94f1'
        labelList['foreground']='white'
        labelList.grid(row=0,column=0, columnspan=2, padx=(2,2),pady=(2,2))

        self.comboboxChannel = ttk.Combobox(self.frameChannel)
        self.comboboxChannel.grid(column=0, row=1, columnspan=2, padx=(10,10), pady=(2,2),sticky=tk.EW)
        self.comboboxChannel['state'] = 'readonly'
        self.comboboxChannel['justify'] = 'center'
        self.comboboxChannel['font'] = self.helv10
        self.comboboxChannel.bind('<<ComboboxSelected>>', self.channel_changed)

        self.channelPrevLabel=ttk.Label(self.frameChannel)
        self.channelPrevLabel['image']=self.imgChannelPrev
        self.channelPrevLabel.bind("<Button-1>", self.channel_prev)
        self.channelPrevLabel.grid(row=2,column=0,padx=(6,0),sticky=tk.W)
        self.channelPrevLabel['padding']=(2,0,0,0)

        self.channelNextLabel=ttk.Label(self.frameChannel)
        self.channelNextLabel['image']=self.imgChannelNext
        self.channelNextLabel.bind("<Button-1>", self.channel_next)
        self.channelNextLabel.grid(row=2,column=1,padx=(0,6), sticky=tk.E)
        self.channelNextLabel['padding']=(0,0,2,0)
        
        self.entryChannelName = ttk.Entry(self.frameChannel)
        self.entryChannelName['width']=16
        self.entryChannelName['font']=self.helv10
        self.entryChannelName['justify']='center'
        self.entryChannelName.grid(row=3,columnspan=2,padx=(10,10), pady=2,sticky=tk.EW)

        self.frameChannelAction = ttk.Frame(self.frameChannel)
        self.frameChannelAction.grid(row=4,column=0,columnspan =2, sticky=tk.EW)
        
        self.labelChannelRemove=ttk.Label(self.frameChannelAction)
        self.labelChannelRemove['image']=self.imgChannelRemove
        self.labelChannelRemove.bind("<Button-1>", self.channel_remove)
        self.labelChannelRemove.grid(row=0,column=1)
        self.labelChannelRemove['padding']=(5,0,5,0)

        self.labelChannelUpdate=ttk.Label(self.frameChannelAction)
        self.labelChannelUpdate['image']=self.imgChecked
        self.labelChannelUpdate.bind("<Button-1>", self.channel_update)
        self.labelChannelUpdate.grid(row=0,column=2)
        self.labelChannelUpdate['padding']=(5,0,5,0)  
        
        self.labelSave=ttk.Label(self.frameChannelAction)
        self.labelSave['image']=self.imgSave
        self.labelSave['padding']=(0,5,5,3)
        self.labelSave.bind("<Button-1>", self.save_channel_list)
        self.labelSave.grid(row=0,column=3,sticky=tk.E)
        
        self.frameChannelAction.columnconfigure(0, weight=100)
        self.frameChannelAction.columnconfigure(1, weight=1)
        self.frameChannelAction.columnconfigure(2, weight=1)
        self.frameChannelAction.columnconfigure(3, weight=1)
  
        self.dummyText=StringVar()
        self.dummyEntry=ttk.Entry(self,textvariable=self.dummyText)
        self.dummyText.set('Hello')
        self.dummyEntry.grid(row=3,column=0)
        self.dummyEntry.grid_forget()
        
        self.frameControl.rowconfigure(3, weight=100)

        self.imgShutdown=PhotoImage(file='icons/system-shutdown.png')
        self.labelQuit=ttk.Label(self.frameControl)
        self.labelQuit['image']=self.imgShutdown
        self.labelQuit['text']="Quit"
        self.labelQuit['padding']=(0,5,5,0)
        self.labelQuit.bind("<Button-1>", self.quit)
        self.labelQuit.grid(row=3,column=0,sticky=tk.SE)

    def enable_channel_actions(self):
        self.comboboxChannel.bind('<<ComboboxSelected>>', self.channel_changed)
        self.channelPrevLabel.bind("<Button-1>", self.channel_prev)
        self.channelNextLabel.bind("<Button-1>", self.channel_next)
        self.labelChannelRemove.bind("<Button-1>", self.channel_remove)
        self.labelChannelUpdate.bind("<Button-1>", self.channel_update)
        self.labelSave.bind("<Button-1>", self.save_channel_list)
        
    def disable_channel_actions(self):
        self.comboboxChannel.set("")
        self.comboboxChannel.bind('<<ComboboxSelected>>', self.dummy_callback)
        self.channelPrevLabel.bind("<Button-1>", self.dummy_callback)
        self.channelNextLabel.bind("<Button-1>", self.dummy_callback)
        self.labelChannelRemove.bind("<Button-1>", self.dummy_callback)
        self.labelChannelUpdate.bind("<Button-1>", self.dummy_callback)
        self.labelSave.bind("<Button-1>", self.dummy_callback)
    
    def channel_remove(self, event):
        print("Channel remove!")
        d = DialogChannelRemove(self,newTvChannels)
        print("'Channel Remove' dialog is opened, waiting to respond")
        self.wait_window(d.root)
        print('End of wait_window, back in MainWindow code')
        print('got data: {yn}'.format(yn=d.yesNo)) 
        if d.yesNo == 'Yes':
            if newTvChannels.nChannel > 1 :
                newTvChannels.remove_channel(newTvChannels.channel)
            tvChannel=newTvChannels.channels[newTvChannels.channel]
            self.gui_update_channel_list()
            self.gui_update_channel_name()
            self.set_tv_channel(tvChannel)
            m026.video_decoder_get_vertical_line_count()
                    
    def channel_update(self,event):
        newTvChannels.channel=self.comboboxChannel.current() 
        print("Channel update:", newTvChannels.channel)
        tvChannel=newTvChannels.channels[newTvChannels.channel]
        tvChannel.name=self.entryChannelName.get()
        newTvChannels.update_channel(newTvChannels.channel,tvChannel)
        self.gui_update_channel_list()
        self.gui_update_channel_name()
        newTvChannels.print()

    def save_channel_list (self,event) :
        print("Channel remove!")
        d = DialogChannelListSave(self,'channels.xml')
        print("'Channel Remove' dialog is opened, waiting to respond")
        self.wait_window(d.root)
        print('End of wait_window, back in MainWindow code')
        print('got data: {yn}'.format(yn=d.yesNo)) 
        if d.yesNo == 'Yes':
            newTvChannels.write()

    def update_channel_infos(self,freqName,freqMHz):
        self.labelChannelName['text']=freqName
        self.labelChannelFrequency['text']="{f:6.2f} MHz".format(f=freqMHz)
        if m026.vdHorizontalSyncLocked == 1 :
            self.labelHSync['text']="Yes"
        else :
            self.labelHSync['text']="No"
        if m026.vdVerticalSyncLocked == 1 :
            self.labelVSync['text']="Yes"
        else :
            self.labelVSync['text']="No"    
        self.labelLineCount['text']=m026.vdVerticalLineCount
        self.update()

    def gui_update_channel_list(self):
        self.valuesChannellist = ["" for i in range(len(newTvChannels.channels))] 
        for i in range(len(newTvChannels.channels)):
            item="{fName} : {freq:6.2f} MHz : {name}" 
            self.valuesChannellist[i]=item.format(fName=newTvChannels.channels[i].frequencyName,freq=newTvChannels.channels[i].frequencyMHz,name=newTvChannels.channels[i].name)
        self.comboboxChannel['values']=self.valuesChannellist
        if len(self.valuesChannellist) :
            self.comboboxChannel.set(self.valuesChannellist[newTvChannels.channel])
        else :
            self.comboboxChannel.set("")
     
    def gui_update_channel_name(self):
        self.entryChannelName.delete(0, END)
        self.entryChannelName.insert(0,newTvChannels.channels[newTvChannels.channel].name)
        
        
    def set_video_size_class(self,videoStandard):
        if videoStandard==VIDEO_STANDARD_NTSC_M_J :
            self.videoSizeClass="480"
        if videoStandard==VIDEO_STANDARD_PAL_B_G_H_I_N :
            self.videoSizeClass="576"      
        if videoStandard==VIDEO_STANDARD_PAL_M :
            self.videoSizeClass="480"             
        if videoStandard==VIDEO_STANDARD_PAL_Nc :
            self.videoSizeClass="576"
        if videoStandard==VIDEO_STANDARD_NTSC :
            self.videoSizeClass="480"  
        if videoStandard==VIDEO_STANDARD_SECAM :
            self.videoSizeClass="576"
        print("Video size class:",self.videoSizeClass)

    def handle_key(self,event):
        
        if event:
            k=event.keysym
            print('> ',k)
    
        if k in ('q', 'Q', 'Escape'):
            self.quit(event=None)
            
        if k == 'Up' :
            self.volume_up()

        if k == 'Down' :
            self.volume_down()

        if k == 'Left' :
            self.channel_prev(event=None)
        
        if k == 'Right' :
            self.channel_next(event=None)
            
        if k in ('r', 'R') : 
            m026.video_decoder_get_vertical_line_count()
            tvChannel=newTvChannels.channels[newTvChannels.channel]
            self.update_channel_infos(tvChannel.frequencyName,tvChannel.frequencyMHz)
        
        if k == 's':
            m026.video_decoder_set_video_standard(VIDEO_STANDARD_00)
            self.video_standard_selected(self,event=None)
            self.scan_start(event=None)

        if k == 'v':
            vlcVideoSize =  vlcApp.videoPlayer.video_get_size() 
            print("VLC Video size:",vlcVideoSize)
            
    def dummy_callback(self,event):
        pass
    
    def defocus(self):
        self.focus()
        self.dummyEntry.focus()
        self.dummyEntry.select_range(0,'end')

    def video_standard_selected(self,event):
        self.defocus()
        self.indexVideoStandard=self.comboboxVideoStandards.current()
        print("Selected video standard:",self.videoStandardList[self.indexVideoStandard])
        videoStandard=int(self.indexVideoStandard*2)
        
        m026.vdVideoStandard=videoStandard
        m026.video_decoder_set_video_standard(m026.vdVideoStandard)
        time.sleep(1)
        m026.video_decoder_status_video_standard()
        m026.get_video_capture()
        print("Size",m026.videoCaptureSize)
        
        if videoStandard == VIDEO_STANDARD_00 :
            videoStandard=m026.vdVideoStandard
    
        self.set_video_size_class(videoStandard)
        
        if self.videoSizeClass=="576" :
            self.labelVideoSize["text"]="720x576"
        else :
            self.labelVideoSize["text"]="720x480"
            
        if self.videoSizeClass=="576" :
            self.canvasVideo['height']=576       
            self.canvasVideo['width']=576*16/9-4
        else :
            self.canvasVideo['height']=480+8       
            self.canvasVideo['width']=(480+8)*16/9-4
    
        streamer.terminate()
        time.sleep(1)
        vlcApp.videoPlayer.stop()
        if self.videoSizeClass=="576" :
            print("576 Size")
            m026.set_video_capture(0,0,720,576)
            streamer.start(720,576) 
        else :
            print("480 Size")
            m026.set_video_capture(0,0,720,480)
            streamer.start(720,480)
        time.sleep(1)
        m026.get_video_capture()
        vlcApp.videoPlayer.play()

        self.dummyEntry.focus_set()
        self.dummyEntry.select_range(0,'end')
           
    def scan_start(self,event):
        global newTvChannels
        if not self.merge.get() :
            newTvChannels=TvChannels()
        self.entryChannelName.delete(0, END)
        self.gui_update_channel_list()
        self.disable_channel_actions()
        self.comboboxChannel.set("")
        self.scan(0)
    
    def scan(self,first):
        global tvChannel
        m026.video_decoder_get_vertical_line_count()
        frequencyNames=list(frequencyDict)
        
        freqName=frequencyNames[first]
        frequencyMHz=frequencyDict[freqName]
        self.update_channel_infos(freqName,frequencyMHz)
        
        i=first
        for i  in range (first, len(frequencyNames)) :
            freqName=frequencyNames[i]
            frequencyMHz=frequencyDict[freqName]
            m026.set_tv_tuner(frequencyMHz)
            m026.video_decoder_get_vertical_line_count()
            print("Vertical line count:",m026.vdVerticalLineCount)
            
            self.update_channel_infos(freqName,frequencyMHz)
            
            if m026.vdVideoDetected :
                print("Video detected: {c} | {f}".format(c=freqName,f=frequencyMHz))
                tvChannel=TvChannel()
                tvChannel.frequencyName=freqName
                tvChannel.frequencyMHz=frequencyMHz
                                
                tvChannel.name="?"

                if self.merge.get() :
                    inList=False
                    for ch in range(newTvChannels.nChannel) :
                        if newTvChannels.channels[ch].frequencyName == freqName :
                            inList=True
                            break
                    if not inList :
                        newTvChannels.add_channel(tvChannel)
                
                else :
                    newTvChannels.add_channel(tvChannel)
                    
                self.gui_update_channel_list()
                self.channel_changed(event=None)
                
            i=i+1
         
        newTvChannels.print()
        
        newTvChannels.channel=0
        tvChannel=newTvChannels.channels[newTvChannels.channel] 
        tvChannel.print()
        self.set_tv_channel(tvChannel)
        self.update_channel_infos(tvChannel.frequencyName,tvChannel.frequencyMHz)
        self.gui_update_channel_list()
        self.enable_channel_actions()
        
    def set_tv_channel(self,tvChannel):
        vlcApp.videoPlayer.pause()
        m026.vdi_stop_capture()
        m026.set_tv_tuner(tvChannel.frequencyMHz)
        self.update_channel_infos(tvChannel.frequencyName,tvChannel.frequencyMHz)
        m026.vdi_start_capture()
        vlcApp.videoPlayer.play()
        
    def channel_changed(self,event):
        print("Channel changed!") 
        print("Current station {}".format(self.comboboxChannel.current()))
        newTvChannels.channel=self.comboboxChannel.current()
        
        self.comboboxChannel.set(newTvChannels.channel)
        
        newTvChannel=newTvChannels.channels[newTvChannels.channel]
        
        self.frequencyName=newTvChannel.frequencyName
        self.frequencyMHz=newTvChannel.frequencyMHz
        
        self.entryChannelName.delete(0, END)
        self.entryChannelName.insert(0,newTvChannels.channels[newTvChannels.channel].name)
        
        print(self.frequencyName, self.frequencyMHz)
        
        m026.set_tv_tuner(self.frequencyMHz)
        m026.video_decoder_get_vertical_line_count()
        
        self.gui_update_channel_list()
        self.update_channel_infos(newTvChannel.frequencyName,newTvChannel.frequencyMHz)        
        self.defocus()

    def channel_next(self,event):
        if newTvChannels.nChannel > 0 :
            newTvChannels.channel+=1
            if newTvChannels.channel > newTvChannels.nChannel-1 : 
                newTvChannels.channel=0
            tvChannel=newTvChannels.channels[newTvChannels.channel] 
            tvChannel.print()
            self.set_tv_channel(tvChannel)
            m026.video_decoder_get_vertical_line_count()
            self.update_channel_infos(tvChannel.frequencyName,tvChannel.frequencyMHz)
            self.gui_update_channel_list()
            self.gui_update_channel_name()
    
    def channel_prev(self,event):
        if newTvChannels.nChannel > 0 :
            newTvChannels.channel-=1
            if newTvChannels.channel < 0 :
                newTvChannels.channel=newTvChannels.nChannel-1
            tvChannel=newTvChannels.channels[newTvChannels.channel]
            tvChannel.print()
            self.set_tv_channel(tvChannel)
            m026.video_decoder_get_vertical_line_count()
            self.update_channel_infos(tvChannel.frequencyName,tvChannel.frequencyMHz)
            self.gui_update_channel_list()
            self.gui_update_channel_name()
            
    def volume_up(self):
        playerVolume=vlcApp.audioPlayer.audio_get_volume()
        playerVolume+=5
        if playerVolume > 150 :
            playerVolume = 150
        print("Player volume:",playerVolume)
        vlcApp.audioPlayer.audio_set_volume(playerVolume)

    def volume_down(self):  
        playerVolume=vlcApp.audioPlayer.audio_get_volume()
        playerVolume-=5
        if playerVolume < 0 :
            playerVolume = 0
        print("Player volume:",playerVolume)
        vlcApp.audioPlayer.audio_set_volume(playerVolume) 
       
    def delete(self):
        self.quit(self)
            
    def quit(self,event):
        m026.set_audio_source(AUDIO_SOURCE_NONE)
        streamer.terminate()  
        m026.gpio_led(False)
        m026.close()
        quit() 

#===============================================================================

channelScaner = TvM026ChannelScanner()
channelScaner.master.wait_visibility()
channelScaner.master.resizable(False,False)
channelScaner.mainloop()

#===============================================================================






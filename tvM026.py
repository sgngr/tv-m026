#!/usr/bin/env python
"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
Main module
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

import sys
import usb1 as usb

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


m026.audioSource=tvM026Settings.m026AudioSource
m026.videoSource=tvM026Settings.m026VideoSource

frameComposite=Frame(Position(tvM026Settings.m026CompositeCaptureStartX,tvM026Settings.m026CompositeCaptureStartY),Position(tvM026Settings.m026CompositeCaptureEndX,tvM026Settings.m026CompositeCaptureEndY))

frameTv=Frame(Position(tvM026Settings.m026TvCaptureStartX,tvM026Settings.m026TvCaptureStartY),Position(tvM026Settings.m026TvCaptureEndX,tvM026Settings.m026TvCaptureEndY))

frameSVideo=Frame(Position(tvM026Settings.m026SVideoCaptureStartX,tvM026Settings.m026SVideoCaptureStartY),Position(tvM026Settings.m026SVideoCaptureEndX,tvM026Settings.m026SVideoCaptureEndY))

m026.vdVideoStandardComposite = tvM026Settings.m026CompositeVideoStandard
m026.vdVideoStandardTv = tvM026Settings.m026TvVideoStandard
m026.vdVideoStandardSVideo = tvM026Settings.m026SVideoVideoStandard
    
m026.vdCaptureFrameComposite=frameComposite
m026.vdCaptureFrameTv=frameTv
m026.vdCaptureFrameSVideo=frameSVideo

#===============================================================================
from tvChannels import *

tvChannels = TvChannels()
tvChannel = TvChannel()

tvChannels.read()
tvChannels.print()

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
# print(audioSources.nameList)
# print(audioSources.descriptionList)

if audioControl.audioSource :
    audioSources.select_by_name(audioControl.sourceName)
    
# audioSources.print()

print("----------------------------------------------------------------")

#===============================================================================

from m026Stream import *

streamDevice=StreamDevice(tvM026Settings.v4l2Device)
streamer=Streamer(tvM026Settings.streamer,streamDevice.v4l2Device)

tv = False
composite = False
svideo= False

if tvM026Settings.m026VideoSource == VIDEO_SOURCE_TV :
    tv = True
    
if tvM026Settings.m026VideoSource == VIDEO_SOURCE_COMPOSITE :
    composite = True
    
if tvM026Settings.m026VideoSource == VIDEO_SOURCE_S_VIDEO :
    svideo = True
    
if composite == True or svideo == True:
    m026.set_audio_source(AUDIO_SOURCE_AUX)
if tv == True:
    m026.set_audio_source(AUDIO_SOURCE_TV_TUNER)

if composite == True:    
    m026.set_video_source(VIDEO_SOURCE_COMPOSITE)

if svideo == True:    
    m026.set_video_source(VIDEO_SOURCE_S_VIDEO)

if tv == True:
    tvChannel=tvChannels.channels[tvChannels.channel]
    m026.set_tv_tuner_frequency(tvChannel.frequencyMHz)
    m026.set_video_source(VIDEO_SOURCE_TV)

m026.video_decoder_status_video_standard()

streamer.terminate()
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

aspectRatio="{w}:{h}".format(w=16,h=9)
vlcApp.videoPlayer.video_set_aspect_ratio(aspectRatio)

widthCropped=m026.videoCaptureSize.width-tvM026Settings.vlcCropLeft-tvM026Settings.vlcCropRight
heightCropped=m026.videoCaptureSize.height-tvM026Settings.vlcCropTop-tvM026Settings.vlcCropBottom
cropGeometry="{w}x{h}+{l}+{t}".format(w=widthCropped,h=heightCropped,l=tvM026Settings.vlcCropLeft,t=tvM026Settings.vlcCropTop)

vScale=tvM026Settings.guiVideoHeight/heightCropped

vlcApp.videoPlayer.video_set_crop_geometry(cropGeometry)

print("Video scale: {s:.3f}".format(s=vlcApp.videoPlayer.video_get_scale()))
print("Video aspect ratio: {r}".format(r=vlcApp.videoPlayer.video_get_aspect_ratio()))
print("Crop geometry:",vlcApp.videoPlayer.video_get_crop_geometry())

#===============================================================================

from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont

#===============================================================================

from m026GUI import *

# - GUI settings -----------------------

global paused
paused=False

#===============================================================================

class TvM026(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.grid(padx=1,pady=1)
        
        self.master.bind('<Key>', self.handle_key)
        self.master.protocol("WM_DELETE_WINDOW", self.delete)
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self.displayColor = '#1e94f1'
        self.master.title('AVerMedia tvM026')
                
        self.master.height=tvM026Settings.guiVideoHeight
        self.videoCanvasWindowID=None
        self.videoCanvasHeight=tvM026Settings.guiVideoHeight
        self.videoCanvasWidth=int(tvM026Settings.guiVideoHeight*tvM026Settings.guiVideoAspectRatio)-1*(tvM026Settings.vlcCropLeft+tvM026Settings.vlcCropRight)
                
        print('GUI video size:',self.videoCanvasWidth,'x',self.videoCanvasHeight)
        
        self.master.attributes('-topmost',1)
        p1 = PhotoImage(file='icons/tvM026.png')
        self.master.iconphoto(False,p1)
        
        self.tvChannel=tvChannels.channels[tvChannels.channel]
        
        self.CreateWidgets()
        self.master.wait_visibility()
        vlcApp.videoPlayer.video_set_scale(vScale)
        
        
        
    def handle_key(self, event):
        k = event.keysym
        print("Key: {k}".format(k=k))
        if k == 'q' or k == 'Q':
            self.quit(self)

    def CreateWidgets(self):
        
        self.frameApp = ttk.Frame(self)
        self.frameApp['relief'] = 'raised'  
        self.frameApp['padding']=(5,5,5,5)
        self.frameApp.grid()
        
        self.videoCanvas = tk.Canvas(self.frameApp,width=self.videoCanvasWidth,height=self.videoCanvasHeight,bg='black')
        self.videoCanvas.grid(row=0,column=0,sticky=tk.EW)
        self.videoCanvasWindowID = self.videoCanvas.winfo_id()
        vlcApp.videoPlayer.set_xwindow(self.videoCanvasWindowID)
        
        #-----------------------------------------------------------------------------------------     
        
        self.frameControl = ttk.Frame(self.frameApp)
        self.frameControl['relief'] = 'raised'
        self.frameControl['padding']=(0,0,10,0)
        self.frameControl.grid(row=2,sticky=tk.EW)
        
        s = ttk.Style()
        s.configure('My.TFrame', background=self.displayColor)
        s.configure('My.TLabel', background=self.displayColor,foreground="white")
        
        #===============================================================================

        self.frameDisplay = ttk.Frame(self.frameControl)
        self.frameDisplay['padding']=(0,2,0,2)
        self.frameDisplay['relief'] = 'raised'
        self.frameDisplay['style'] = 'My.TFrame'
        self.frameDisplay.grid(row=0,column=0,sticky=tk.EW)
        self.frameDisplay.columnconfigure(0, minsize=400)
        
        helv12b = tkFont.Font(family='Helvetica',size=12, weight='bold')
        self.frameDisplay.labelChannel=ttk.Label(self.frameDisplay,text=tvChannels.channels[tvChannels.channel].name)
        self.frameDisplay.labelChannel['font']=helv12b
        self.frameDisplay.labelChannel['style']='My.TLabel'
        self.frameDisplay.labelChannel.grid(row=0, column=0)

        # -----------------------

        self.frameTVchannel = ttk.Frame(self.frameControl)
        self.frameTVchannel['padding']=(8,1,4,0)
        self.frameTVchannel.grid(row=0,column=1,sticky=tk.EW,padx=5,ipady=2)
        
        self.imgChannelPrev=PhotoImage(file='icons/media-skip-backward.png')
        self.frameTVchannel.channelPrevLabel=ttk.Label(self.frameTVchannel)
        self.frameTVchannel.channelPrevLabel['image']=self.imgChannelPrev
        self.frameTVchannel.channelPrevLabel['padding']=(5,5,5,0)
        self.frameTVchannel.channelPrevLabel.bind("<Button-1>", self.channel_prev)        
        self.frameTVchannel.channelPrevLabel.grid(row=0,column=1)
       
        self.imgChannelNext=PhotoImage(file='icons/media-skip-forward.png')
        self.frameTVchannel.channelNextLabel=ttk.Label(self.frameTVchannel)
        self.frameTVchannel.channelNextLabel['image']=self.imgChannelNext
        self.frameTVchannel.channelNextLabel['padding']=(5,5,5,0)
        self.frameTVchannel.channelNextLabel.bind("<Button-1>", self.channel_next)
        self.frameTVchannel.channelNextLabel.grid(row=0,column=2,sticky=tk.E)
        
        self.imgGoBottom=PhotoImage(file='icons/go-bottom.png')
        self.imgGoTop=PhotoImage(file='icons/go-top.png')
        
        self.frameTVchannel.controlUpDownLabel=ttk.Label(self.frameTVchannel)
        self.frameTVchannel.controlUpDownLabel['image']=self.imgGoBottom
        self.frameTVchannel.controlUpDownLabel['padding']=(5,5,5,0)
        self.frameTVchannel.controlUpDownLabel.bind("<Button-1>", self.channelSettings)
        self.frameTVchannel.controlUpDownLabel.grid(row=0,column=6)
        
        self.frameControl.columnconfigure(3, weight=100)
        
        #-----------------------
    
        self.frameAudio = ttk.Frame(self.frameControl)
        self.frameAudio['padding']=(0,2,0,2)
        self.frameAudio.grid(row=0,column=4,sticky=tk.E)

        self.imgVolDown=PhotoImage(file='icons/go-down.png')
        self.frameAudio.volDownLabel=ttk.Label(self.frameAudio)
        self.frameAudio.volDownLabel['image']=self.imgVolDown
        self.frameAudio.volDownLabel['padding']=(5,0,5,0)
        self.frameAudio.volDownLabel.bind("<Button-1>", self.volume_down)
        self.frameAudio.volDownLabel.grid(row=0,column=3)

        self.imgVolUp=PhotoImage(file='icons/go-up.png')
        self.frameAudio.volUpLabel=ttk.Label(self.frameAudio)
        self.frameAudio.volUpLabel['image']=self.imgVolUp
        self.frameAudio.volUpLabel['padding']=(5,0,5,0)
        self.frameAudio.volUpLabel.bind("<Button-1>", self.volume_up)
        self.frameAudio.volUpLabel.grid(row=0,column=4)
        
        #-----------------------
        
        self.imgPause=PhotoImage(file='icons/media-playback-pause.png')
        self.imgStart=PhotoImage(file='icons/media-playback-start.png')
        
        self.labelPlayPause=ttk.Label(self.frameControl)
        self.labelPlayPause['image']=self.imgPause
        self.labelPlayPause['padding']=(5,0,5,0)
        self.labelPlayPause.bind("<Button-1>", self.playPause)
        self.labelPlayPause.grid(row=0,column=6)
        
        self.frameControl.columnconfigure(7, minsize=10)
        
        self.imgSettings=PhotoImage(file='icons/applications-system.png')       
        self.labelSettings=ttk.Label(self.frameControl)       
        self.labelSettings['image']=self.imgSettings       
        self.labelSettings['padding']=(5,0,5,0)       
        self.labelSettings.bind("<Button-1>", self.dialogSettings)       
        self.labelSettings.grid(row=0,column=8) 
        
        self.imgSource=PhotoImage(file='icons/media-source.png')       
        self.labelSource=ttk.Label(self.frameControl)       
        self.labelSource['image']=self.imgSource     
        self.labelSource['padding']=(5,0,5,0)       
        self.labelSource.bind("<Button-1>", self.source_changed)       
        self.labelSource.grid(row=0,column=9)       
       
        self.imgShutdown=PhotoImage(file='icons/system-shutdown.png')
        self.labelQuit=ttk.Label(self.frameControl)
        self.labelQuit['image']=self.imgShutdown
        self.labelQuit['text']="Çık"
        self.labelQuit['padding']=(0,0,0,0)
        self.labelQuit.bind("<Button-1>", self.quit)
        self.labelQuit.grid(row=0,column=10,sticky=tk.E)

    def display_frameTVchannel(self):
        self.frameTVchannel.grid(row=0,column=1,sticky=tk.EW,padx=5,ipady=2)

    def set_tv_channel (self,tvChannel):
        vlcApp.videoPlayer.pause()
        m026.vdi_stop_capture()
        m026.set_tv_tuner_frequency(tvChannel.frequencyMHz)
        m026.vdi_start_capture()
        vlcApp.videoPlayer.play()
        self.update_display()
                
    def channel_next(self,event):
        tvChannels.channel+=1
        if tvChannels.channel > tvChannels.nChannel-1 : 
            tvChannels.channel=0
        tvChannel=tvChannels.channels[tvChannels.channel]  
        self.set_tv_channel(tvChannel)
    
    def channel_prev(self,event):  
        tvChannels.channel-=1
        if tvChannels.channel < 0 :
            tvChannels.channel=tvChannels.nChannel-1
        tvChannel=tvChannels.channels[tvChannels.channel]
        self.set_tv_channel(tvChannel)
        
    def source_changed(self, event):
        vlcApp.videoPlayer.stop()
        streamer.terminate()
        time.sleep(1)

        if m026.videoSource == VIDEO_SOURCE_TV:
            # Composite
            m026.videoSource = VIDEO_SOURCE_COMPOSITE
            m026.set_video_source(VIDEO_SOURCE_COMPOSITE)            
            self.frameTVchannel.grid_remove()
        elif m026.videoSource == VIDEO_SOURCE_COMPOSITE:
            # S-Video
            m026.videoSource = VIDEO_SOURCE_S_VIDEO
            m026.set_video_source(VIDEO_SOURCE_S_VIDEO)
            self.frameTVchannel.grid_remove()
        elif m026.videoSource == VIDEO_SOURCE_S_VIDEO:
            # Tv
            m026.videoSource = VIDEO_SOURCE_TV
            m026.tvTunerFrequency=tvChannels.channels[tvChannels.channel].frequencyMHz
            m026.set_video_source(VIDEO_SOURCE_TV)
            self.display_frameTVchannel()
   
        m026.vdi_get_capture_frame()
    
        streamDevice.frame_width=m026.videoCaptureSize.width
        streamDevice.frame_height=m026.videoCaptureSize.height
        streamDevice.pixel_format=PixelFormat.YUYV
        
        streamDevice.set()
        if streamDevice.is_set == False :
            print("Stream device can't set!")
        
        q=0
        while streamDevice.is_set == False and q < 5 :
            time.sleep(1)
            streamDevice.set()
            if streamDevice.is_set == False :
                print("Stream device can't set!")
            q+=1
            
        print("Stream device is set, streamer will start!")
        streamer.start(m026.videoCaptureSize.width,m026.videoCaptureSize.height)
        
        videoMedia='v4l2://'+tvM026Settings.v4l2Device
        vlcApp.set_video_media(videoMedia)
        vlcApp.videoPlayer.set_xwindow(self.videoCanvasWindowID)
        time.sleep(1)
        
        # player scale and crop
        widthCropped=m026.videoCaptureSize.width-tvM026Settings.vlcCropLeft-tvM026Settings.vlcCropRight
        heightCropped=m026.videoCaptureSize.height-tvM026Settings.vlcCropTop-tvM026Settings.vlcCropBottom
        cropGeometry="{w}x{h}+{l}+{t}".format(w=widthCropped,h=heightCropped,l=tvM026Settings.vlcCropLeft,t=tvM026Settings.vlcCropTop)
        print("Crop Geometry:",cropGeometry)
        vScale=tvM026Settings.guiVideoHeight/heightCropped
        vlcApp.videoPlayer.video_set_scale(vScale)
        vlcApp.videoPlayer.video_set_crop_geometry(cropGeometry)
        vlcApp.videoPlayer.play()
        
        tvM026Settings.m026VideoSource=m026.videoSource    

        self.update_display()

    def playPause(self,event):
        global paused
        if paused:
            self.labelPlayPause['image']=tvM026.imgPause
            m026.vdi_start_capture()
            audioControl.unmute()
            paused=False
        else:
            self.labelPlayPause['image']=tvM026.imgStart
            m026.vdi_stop_capture()
            audioControl.mute()
            paused=True        

    def channelSettings(self,event):
        d = ChannelSettings(self.master, self, tvChannels, m026, frequencyDict)
        print("'Channel Settings' dialog is opened, waiting to respond")
        self.master.wait_window(d.root)
        print('End of wait_window, back in MainWindow code')
        

    def dialogSettings(self,event):
        fileSettings=tvM026Settings.fileSettings
        tvM026Settings.read(fileSettings)
        
        if tvM026Settings.audioSource == None :
            audioControl.get_source('Unknown')
        else :
            audioControl.get_source(tvM026Settings.audioSource)
        
        if audioControl.audioSource:
            audioMedia='pulse://'+audioControl.sourceName
            vlcApp.set_audio_media(audioMedia)
            vlcApp.audioPlayer.play()
        
        d = AppSettings(self.master,self,tvM026Settings,streamDevice,streamer,m026,audioSources,audioControl,vlcApp)

        d.drawVideoFrame576()
        d.drawVideoFrame480()
        print("Video size class: ", d.videoSizeClass) 
        if d.videoSizeClass == "576" :
            d.frameCaptureStart480.grid_forget()
        else :
            d.frameCaptureStart576.grid_forget() 

        print("'Settings' dialog is opened, waiting to respond")
        self.master.wait_window(d.root)
        
        self.update_display()
        tvM026Settings.write(fileSettings)
        
    def update_display(self):
        print("Updating display:")
        print("  Video source:",list_video_sources[m026.videoSource])
        m026.video_decoder_get_video_standard()
        m026.video_decoder_status_video_standard()
        print("  Video standard",list_video_standards[m026.vdVideoStandard])
        
        txtVideoStandard="PAL"
        if m026.vdVideoStandard == VIDEO_STANDARD_NTSC_M_J or m026.vdVideoStandard ==  VIDEO_STANDARD_NTSC :
            txtVideoStandard="NTSC"
        if m026.vdVideoStandard == VIDEO_STANDARD_SECAM :
            txtVideoStandard="SECAM"
        
        if m026.videoSource == VIDEO_SOURCE_COMPOSITE :
            displayText="CVBS:"
            displayText+=txtVideoStandard
            self.frameDisplay.labelChannel['text']=displayText
            
        if m026.videoSource == VIDEO_SOURCE_S_VIDEO :
            displayText="S-Video:"
            displayText+=txtVideoStandard    
            self.frameDisplay.labelChannel['text']=displayText
            
        if m026.videoSource == VIDEO_SOURCE_TV :    
            self.frameDisplay.labelChannel['text']="{fName} : {freq:.2f} MHz : {name}".format(fName=tvChannels.channels[tvChannels.channel].frequencyName,freq=tvChannels.channels[tvChannels.channel].frequencyMHz,name=tvChannels.channels[tvChannels.channel].name)
        
        print("Display updated:", self.frameDisplay.labelChannel['text'])
       
    def volume_up(self,event):
        playerVolume=vlcApp.audioPlayer.audio_get_volume()
        playerVolume+=5
        if playerVolume > 150 :
            playerVolume = 150
        print("Player volume:",playerVolume)
        vlcApp.audioPlayer.audio_set_volume(playerVolume)

    def volume_down(self,event):  
        playerVolume=vlcApp.audioPlayer.audio_get_volume()
        playerVolume-=5
        if playerVolume < 0 :
            playerVolume = 0
        print("Player volume:",playerVolume)
        vlcApp.audioPlayer.audio_set_volume(playerVolume)    
        
    def delete(self):
        self.quit(self)
        
    def quit(self,event):
        tvChannels.write()
        
        tvM026Settings.audioPlayerVolume=vlcApp.audioPlayer.audio_get_volume()
        tvM026Settings.m026AudioSource=m026.audioSource
        tvM026Settings.m026VideoSource=m026.videoSource

        tvM026Settings.m026CompositeVideoStandard=m026.vdVideoStandardComposite
        tvM026Settings.m026TvVideoStandard=m026.vdVideoStandardTv
        tvM026Settings.m026SVideoVideoStandard=m026.vdVideoStandardSVideo

        tvM026Settings.m026TvCaptureStartX=m026.vdCaptureFrameTv.start.x
        tvM026Settings.m026TvCaptureStartY=m026.vdCaptureFrameTv.start.y
        tvM026Settings.m026TvCaptureEndX=m026.vdCaptureFrameTv.end.x
        tvM026Settings.m026TvCaptureEndY=m026.vdCaptureFrameTv.end.y
        
        tvM026Settings.m026SVideoCaptureStartX=m026.vdCaptureFrameSVideo.start.x
        tvM026Settings.m026SVideoCaptureStartY=m026.vdCaptureFrameSVideo.start.y
        tvM026Settings.m026SVideoCaptureEndX=m026.vdCaptureFrameSVideo.end.x
        tvM026Settings.m026SVideoCaptureEndY=m026.vdCaptureFrameSVideo.end.y
        
        tvM026Settings.m026CompositeCaptureStartX=m026.vdCaptureFrameComposite.start.x
        tvM026Settings.m026CompositeCaptureStartY=m026.vdCaptureFrameComposite.start.y
        tvM026Settings.m026CompositeCaptureEndX=m026.vdCaptureFrameComposite.end.x
        tvM026Settings.m026CompositeCaptureEndY=m026.vdCaptureFrameComposite.end.y
        
        tvM026Settings.print()                  
        
        tvM026Settings.write(fileSettings)
        m026.set_audio_source(AUDIO_SOURCE_NONE)
        streamer.terminate()  
        m026.gpio_led(False)
        m026.close()
        quit()   
        
#===============================================================================

tvM026 = TvM026()
if m026.videoSource != VIDEO_SOURCE_TV :
    tvM026.frameTVchannel.grid_remove()
tvM026.update_display()
vlcApp.videoPlayer.play()
tvM026.master.wait_visibility()
tvM026.master.resizable(False,False)
tvM026.mainloop()

#===============================================================================







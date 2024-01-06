"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
Application settings module
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

import os
import platform
import xml.etree.ElementTree as ET
        
class Settings():
    def __init__(self):
        self.fileSettings="tvM026-settings.xml"    
        self.guiVideoHeight=640
        self.guiVideoAspectRatio=16/9
        self.vlcCropLeft=10
        self.vlcCropTop=8
        self.vlcCropRight=0
        self.vlcCropBottom=0
        self.v4l2Device='/dev/video0'
        self.streamer='./m026-streamer'
        self.audioSource=None
        self.audioSourceVolume=0.25
        self.audioPlayerVolume=50
        self.m026AudioSource=0
        self.m026VideoSource=0
        self.m026TvVideoStandard=0
        self.m026TvCaptureStartX=0
        self.m026TvCaptureStartY=0
        self.m026TvCaptureEndX=1280
        self.m026TvCaptureEndY=240
        self.m026CompositeVideoStandard=0
        self.m026CompositeCaptureStartX=0
        self.m026CompositeCaptureStartY=0
        self.m026CompositeCaptureEndX=1280
        self.m026CompositeCaptureEndY=240
        self.m026SVideoVideoStandard=0
        self.m026SVideoCaptureStartX=0
        self.m026SVideoCaptureStartY=0
        self.m026SVideoCaptureEndX=1280
        self.m026SVideoCaptureEndY=240

        if os.path.exists(self.fileSettings):
            self.read(self.fileSettings)
        
    def read (self,file):
        tree=ET.parse(file)
        root=tree.getroot()
        self.v4l2Device=root.find('v4l2_device').text  
        self.audioSource=root.find('audio_source').text
        if self.audioSource=='None' :
            self.audioSource=None
        self.audioSourceVolume=float(root.find('audio_source_volume').text) 
        self.audioPlayerVolume=int(root.find('audio_player_volume').text)
        self.m026AudioSource=int(root.find('m026_audio_source').text)
        self.m026VideoSource=int(root.find('m026_video_source').text) 
 
        self.m026TvVideoStandard=int(root.find('m026_tv_video_standard').text)
        self.m026TvCaptureStartX=int(root.find('m026_tv_capture_start_x').text)
        self.m026TvCaptureStartY=int(root.find('m026_tv_capture_start_y').text)
        self.m026TvCaptureEndX=int(root.find('m026_tv_capture_end_x').text)
        self.m026TvCaptureEndY=int(root.find('m026_tv_capture_end_y').text)
        
        self.m026SVideoVideoStandard=int(root.find('m026_svideo_video_standard').text)
        self.m026SVideoCaptureStartX=int(root.find('m026_svideo_capture_start_x').text)
        self.m026SVideoCaptureStartY=int(root.find('m026_svideo_capture_start_y').text)
        self.m026SVideoCaptureEndX=int(root.find('m026_svideo_capture_end_x').text)
        self.m026SVideoCaptureEndY=int(root.find('m026_svideo_capture_end_y').text)

        self.m026CompositeVideoStandard=int(root.find('m026_composite_video_standard').text)
        self.m026CompositeCaptureStartX=int(root.find('m026_composite_capture_start_x').text)
        self.m026CompositeCaptureStartY=int(root.find('m026_composite_capture_start_y').text)
        self.m026CompositeCaptureEndX=int(root.find('m026_composite_capture_end_x').text)
        self.m026CompositeCaptureEndY=int(root.find('m026_composite_capture_end_y').text)
        
    def write(self,file):
        root = ET.Element("settings")
        r=ET.SubElement(root,"v4l2_device").text="{}".format(self.v4l2Device)
        r=ET.SubElement(root,"audio_source").text="{}".format(self.audioSource)
        r=ET.SubElement(root,"audio_source_volume").text="{v:.2f}".format(v=self.audioSourceVolume)
        r=ET.SubElement(root,"audio_player_volume").text="{v}".format(v=self.audioPlayerVolume)
        r=ET.SubElement(root,"m026_audio_source").text="{}".format(self.m026AudioSource)
        r=ET.SubElement(root,"m026_video_source").text="{}".format(self.m026VideoSource)
        
        r=ET.SubElement(root,"m026_tv_video_standard").text="{}".format(self.m026TvVideoStandard)
        r=ET.SubElement(root,"m026_tv_capture_start_x").text="{}".format(self.m026TvCaptureStartX)
        r=ET.SubElement(root,"m026_tv_capture_start_y").text="{}".format(self.m026TvCaptureStartY)        
        r=ET.SubElement(root,"m026_tv_capture_end_x").text="{}".format(self.m026TvCaptureEndX)
        r=ET.SubElement(root,"m026_tv_capture_end_y").text="{}".format(self.m026TvCaptureEndY)
        
        r=ET.SubElement(root,"m026_composite_video_standard").text="{}".format(self.m026CompositeVideoStandard)
        r=ET.SubElement(root,"m026_composite_capture_start_x").text="{}".format(self.m026CompositeCaptureStartX)
        r=ET.SubElement(root,"m026_composite_capture_start_y").text="{}".format(self.m026CompositeCaptureStartY)        
        r=ET.SubElement(root,"m026_composite_capture_end_x").text="{}".format(self.m026CompositeCaptureEndX)
        r=ET.SubElement(root,"m026_composite_capture_end_y").text="{}".format(self.m026CompositeCaptureEndY)

        r=ET.SubElement(root,"m026_svideo_video_standard").text="{}".format(self.m026SVideoVideoStandard)
        r=ET.SubElement(root,"m026_svideo_capture_start_x").text="{}".format(self.m026SVideoCaptureStartX)
        r=ET.SubElement(root,"m026_svideo_capture_start_y").text="{}".format(self.m026SVideoCaptureStartY)        
        r=ET.SubElement(root,"m026_svideo_capture_end_x").text="{}".format(self.m026SVideoCaptureEndX)
        r=ET.SubElement(root,"m026_svideo_capture_end_y").text="{}".format(self.m026SVideoCaptureEndY)
        
        tree = ET.ElementTree(root)
        tree.write(file,encoding="utf-8", xml_declaration=True)
        from shutil import which
        if which('xml') :
            cmd="xml format {file} > {file}.1".format(file=self.fileSettings)
            print(cmd)
            os.system(cmd)
            cmd="mv {file}.1 {file} ".format(file=self.fileSettings)
            print(cmd)
            os.system(cmd)

    def print(self):
        print("Application Settings:")
        print(" v4l2 loopback device:",self.v4l2Device)
        print(" Audio player source:",self.audioSource)
        print(" Audio source volume:","{v:.2f}".format(v=self.audioSourceVolume))
        print(" Audio player volume:","{v}".format(v=self.audioPlayerVolume))
        print(" Audio source:",self.m026AudioSource)
        print(" Video source:",self.m026VideoSource)
        print(" TV Video standard:",self.m026TvVideoStandard)
        print(" TV capture start X:",self.m026TvCaptureStartX)
        print(" TV capture start Y:",self.m026TvCaptureStartY)
        print(" TV capture end X:",self.m026TvCaptureEndX)
        print(" TV capture end Y:",self.m026TvCaptureEndY)
        print(" S-Video Video standard:",self.m026SVideoVideoStandard)
        print(" S-Video capture start X:",self.m026SVideoCaptureStartX)
        print(" S-Video capture start Y:",self.m026SVideoCaptureStartY)
        print(" S-Video capture end X:",self.m026SVideoCaptureEndX)
        print(" S-Video capture end Y:",self.m026SVideoCaptureEndY)
        print(" Composite Video standard:",self.m026CompositeVideoStandard)
        print(" Composite capture start X:",self.m026CompositeCaptureStartX)
        print(" Composite capture start Y:",self.m026CompositeCaptureStartY)
        print(" Composite capture end X:",self.m026CompositeCaptureEndX)
        print(" Composite capture end Y:",self.m026CompositeCaptureEndY)

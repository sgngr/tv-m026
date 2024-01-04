"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
v4l2 streamer module
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

from v4l2py.device import Device, BufferType, PixelFormat

class StreamDevice(object):
    def __init__(self,v4l2Device):
        self.v4l2Device=v4l2Device
        self.info=None
        self.frame_width=0
        self.frame_height=0
        self.pixel_format=PixelFormat.GREY
        self.is_set=False
        self.is_got=False
        self.get()
        
    def get(self):
        deviceID=''.join(filter(str.isdigit,self.v4l2Device))
        v4l2Device = Device.from_id(deviceID)
        try:
            v4l2Device.open()
            self.info=v4l2Device.info
            streamDataFormat=v4l2Device.get_format(BufferType.VIDEO_OUTPUT) 
            self.frame_width=streamDataFormat.width
            self.frame_height=streamDataFormat.height
            self.pixel_format=streamDataFormat.pixel_format
            v4l2Device.close()
            self.is_got=True
        except:
            self.is_got=False
            self.is_set=False
      
    def set(self):
        deviceID=''.join(filter(str.isdigit,self.v4l2Device))
        v4l2Device = Device.from_id(deviceID)
        try:
            v4l2Device.open()
            v4l2Device.set_format(BufferType.VIDEO_OUTPUT, pixel_format=self.pixel_format, width=self.frame_width, height=self.frame_height)    
            v4l2Device.close()
            self.is_set=True
        except:
            self.is_set=False


import os
import signal
from subprocess import check_output

class Streamer(object):
    def __init__(self,streamer,streamDevice):
        self.streamer=streamer
        self.streamDevice=streamDevice
    def get_pid(self):
        try:
            pid=int(check_output(["pidof",self.streamer]))
        except:
            pid=None
        return pid
    
    def terminate(self):
        pid=self.get_pid()
        if pid:
            os.kill(pid,signal.SIGTERM)    

    def start(self,width,height):
        cmd="{s} -d {d} -w {w} -h {h} &".format(s=self.streamer,d=self.streamDevice, w=width, h=height)
        os.system(cmd) 
        print("Command executed:",cmd)

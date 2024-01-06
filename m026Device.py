"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
Hardware control module
================================================
Version:    0.1
Author:     Sinan Güngör
"""

import os
import time
import usb1 as usb

#===============================================================================

class DC1100():
    # GCTRL GPIO Control 
    GCTRL=0x000

    # Remote Wakeup Control
    RMCTL=0x00C

    # Decoder Control Register
    DCTRL=0x100

    # Capture Frame Start Position 
    CFSPO=0x110
    CFSPO_STX_L=0x110
    CFSPO_STX_H=0x111
    CFSPO_STY_L=0x112
    CFSPO_STY_H=0x113

    # Capture Frame End Position
    CFEPO=0x114
    CFEPO_ENX_L=0x114
    CFEPO_ENX_H=0x115
    CFEPO_ENY_L=0x116
    CFEPO_ENY_H=0x117 

    #Serial Interface Control Register
    SICTL=0x200

    # Serial Bus Write
    SBUSW=0x204
    
    # Serial Bus Read
    SBUSR=0x208

dc1100=DC1100()

#===============================================================================

import ctypes
enum = ctypes.c_uint

video_standards = enum 
(VIDEO_STANDARD_00,VIDEO_STANDARD_01, VIDEO_STANDARD_NTSC_M_J, VIDEO_STANDARD_03, VIDEO_STANDARD_PAL_B_G_H_I_N, VIDEO_STANDARD_05, VIDEO_STANDARD_PAL_M, VIDEO_STANDARD_07, VIDEO_STANDARD_PAL_Nc, VIDEO_STANDARD_09, VIDEO_STANDARD_NTSC, VIDEO_STANDARD_11, VIDEO_STANDARD_SECAM) = range(13)

audio_sources = enum
(AUDIO_SOURCE_NONE,AUDIO_SOURCE_AUX,AUDIO_SOURCE_TV_TUNER) = range(3)

video_sources = enum
(VIDEO_SOURCE_TV,VIDEO_SOURCE_COMPOSITE,VIDEO_SOURCE_S_VIDEO) = range(3)

list_video_standards=["Autoswitch", "Reserved", "NTSC (M,J)", "Reserved", "PAL (B,G,H,I,N)", "Reserved", "PAL (M)","Reserved", "PAL (Nc)","Reserved", "NTSC (4.43)","Reserved", "SECAM  (B, D, G, K, K1, L)"]
list_audio_sources=["None","Aux","Tv Tuner"]
list_video_sources=["Tv","Composite","S-Video"]

#===============================================================================

class Utils():
    def set_bit(self,value, bit):
        return value | (1<<bit)
    
    def clear_bit(self,value, bit):
        return value & ~(1<<bit)

    def get_bit(self,value,bit):
        return ((value >> bit) & 1)  
    
    def byte2bits(self,x):
        return "{:04b}".format(x>>4)+" "+"{:04b}".format(x&0x0F)
    
    def word2bits(self,x):
        return "{:04b}".format(x>>12)+" "+"{:04b}".format((x>>8)&0x0F)+" "+"{:04b}".format((x>>4)&0x0F)+" "+"{:04b}".format(x&0x0F)
    
utils = Utils()

#===============================================================================

class Position(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __str__(self):
        return '(' + str(self.get_x()) + ',' + str(self.get_y()) + ')'
    def get_x(self):
        return self.x
    def get_y(self):
        return self.y

class Frame(object):
    def __init__(self,start,end):
        self.start = start
        self.end = end
    def __str__(self):
        return str(self.get_start()) + '-' + str(self.get_end())
    def get_start(self):
        return self.start
    def get_end(self):
        return self.end

class Size(object):
    def __init__(self,w,h):
        self.width = w
        self.height = h
    def __str__(self):
        return str(self.get_width()) + 'x' + str(self.get_height()) 
    def get_width(self):
        return self.width
    def get_height(self):
        return self.height

#===============================================================================

class M026Device():
    """This class provides functions to control the hardware of AVerMedia AVerTV USB2.0 (07ca:0026).
    The main controller of the device - Crescentec/Syntek CT-DC1100 video controller - is an ancestor 
    of Syntek STK11xx series video imaging controllers and has similar registers with this series of 
    controllers. Main controller functions are grouped as:
      - GPIO functions: gpio_....()
      - Video decoder interface functions: vdi_....()
      - Serial bus interface functions: sbi_....()
      - Timing generator functions: tg_....()
    Functions for other hardware controlled via serial bus interface are:
      - Video decoder (Texas Instruments TVP5150AM1) functions: video_decoder_....()
      - Tuner functions (LG TALN-M205T): tv_tuner_....()
    """

    def __init__(self):
        self.VENDOR_ID=0x07ca
        self.PRODUCT_ID=0x0026
        self.usbDev = None
        self.usbDevh = None
        self.usbOpened = False
        
        self.colorBrightness0 = 0.5
        self.colorBrightness = 0.5
        self.colorContrast0 = 0.5
        self.colorContrast = 0.5
        self.colorHue0 = 0.0
        self.colorHue = 0.0
        self.colorSaturation0 = 0.5
        self.colorSaturation = 0.5
 
        self.audioSource = 0
        self.videoSource = 0

        self.videoCaptureStart=Position(0,0)
        self.videoCaptureEnd=Position(640,480)
        self.videoCaptureSize=Size(640,480)

        self.vdVideoStandard=0x04
        self.vdVideoStandardAuto=0x00
        self.vdVideoStandardComposite=0
        self.vdVideoStandardSVideo=0
        self.vdVideoStandardTv=0
        self.vdCaptureFrameComposite=Frame(Position(0,0),Position(1280,240))
        self.vdCaptureFrameSVideo=Frame(Position(0,0),Position(1280,240))
        self.vdCaptureFrameTv=Frame(Position(0,0),Position(1280,240))
        self.vdVideoSizeClass="576"
        self.vdVerticalLineCount=625
        self.vdVerticalSyncLocked=0
        self.vdHorizontalSyncLocked=0
        self.vdVideoDetected=False

        self.tvTunerFrequency=500.25
    
    def find(self):
        """Find the device."""
        usbContext=usb.USBContext()
        for dev in usbContext.getDeviceList():
            if dev.getVendorID() == self.VENDOR_ID and dev.getProductID() == self.PRODUCT_ID :
                break
            else:
                dev=None
        self.usbDev=dev
        
    def open(self):
        """Open the device."""
        self.usbDevh=self.usbDev.open()
    
    def reset(self):
        """Reset the device."""
        if self.usbDevh :
            self.usbDevh.resetDevice()
            
    def close(self):
        """Close the device."""
        self.usbDevh.close()
    
    def ctrl_tx(self,index,value):
        """Do a USB control write."""
        r = self.usbDevh.controlWrite(0x40,1,value,index,[])

    def ctrl_rx(self,index):
        """Do a USB control read."""
        r = self.usbDevh.controlRead(0xc0,0,0x0000,index,1)
        return r[0]
 
    def print_register(self,reg):
        """Print value of a USB control register"""
        val=self.ctrl_rx(reg)
        print("0x{v:03x} | {b}".format(v=val,b=utils.byte2bits(val)))
 
    def set_register_bit(self,reg,bit):
        """Set a USB control register bit."""
        val=self.ctrl_rx(reg)
        val=utils.set_bit(val,bit)
        self.ctrl_tx(reg,val)

    def clear_register_bit(self,reg,bit):
        """Clear a USB control register bit."""
        val=self.ctrl_rx(reg)
        val=utils.clear_bit(val,bit)
        self.ctrl_tx(reg,val)

    def sbi_clock_divider(self,cd):
        """Set serial bus clock devider."""
        self.ctrl_tx(dc1100.SICTL+2,cd) 
    
    def sbi_select_device(self,sda):
        """Select a serial bus device."""
        self.ctrl_tx(dc1100.SICTL+3,sda)

    def sbi_read(self,ra):
        """Do register read from a serial bus device."""
        self.ctrl_tx(dc1100.SBUSR,ra)
        self.ctrl_tx(dc1100.SICTL,0x0020)   # Read now
        rf=self.sbi_read_finish(1000)
        rd=self.ctrl_rx(dc1100.SBUSR+1)
        return rd   
   
    def sbi_write(self,wa,wd):
        """Write register of a serial bus device."""
        self.ctrl_tx(dc1100.SBUSW,wa)
        self.ctrl_tx(dc1100.SBUSW+1,wd)
        self.ctrl_tx(dc1100.SICTL,0x0005) # Retry Write on Failed ACK + Access Immediately
        wf=self.sbi_write_finish(1000)

    def sbi_write_finish(self, max_try):
        """Wait until write operation completed."""
        c = self.ctrl_rx(dc1100.SICTL+1) 
        q=1
        while c != 0x04 :
            c = self.ctrl_rx(dc1100.SICTL+1)
            q+=1
            if q == max_try :
                print('sbi_write_finish: Serial bus interface can not write!')
                return False
        return True
    
    def sbi_read_finish(self, max_try):
        """Wait until read operation completed."""
        c = self.ctrl_rx(dc1100.SICTL+1) 
        q=1
        while c != 0x01 :
            c = self.ctrl_rx(dc1100.SICTL+1)
            q+=1
            if q == max_try :
                print('sbi_read_finish: Serial bus interface can not read!')
                return False
        return True
        
    def gpio_led(self,on):
        """Turn the LED on the device on or off."""
        if on :
            self.clear_register_bit(dc1100.GCTRL,6) # GCTRL:GV
        else:
            self.set_register_bit(dc1100.GCTRL,6) # GCTRL
            
            
    def tg_set_timings(self):
        """Set timing generator."""
        self.ctrl_tx(0x0300,0x0012)
        self.ctrl_tx(0x0350,0x002d)
        self.ctrl_tx(0x0351,0x0001)
        self.ctrl_tx(0x0352,0x0000)
        self.ctrl_tx(0x0353,0x0000)
        self.ctrl_tx(0x0300,0x0080)    
    
    def vdi_start_capture(self):
        """Start video capture."""
        self.ctrl_tx(dc1100.DCTRL,0xb3)
    
    def vdi_stop_capture(self):
        self.ctrl_tx(dc1100.DCTRL,0x33)
        """Stop video capture."""
        
    def vdi_set_capture_frame(self,frame):
        """Set capture frame."""
        x0=frame.start.x
        y0=frame.start.y
        x1=frame.end.x
        y1=frame.end.y
        
        xL=x0&0x00FF
        xH=(x0&0xFF00)>>8
        self.ctrl_tx(dc1100.CFSPO_STX_L,xL)
        self.ctrl_tx(dc1100.CFSPO_STX_H,xH)

        yL=y0&0x00FF
        yH=(y0&0xFF00)>>8
        self.ctrl_tx(dc1100.CFSPO_STY_L,yL)
        self.ctrl_tx(dc1100.CFSPO_STY_H,yH)

        xL=x1&0x00FF
        xH=(x1&0xFF00)>>8
        self.ctrl_tx(dc1100.CFEPO_ENX_L,xL)
        self.ctrl_tx(dc1100.CFEPO_ENX_H,xH)

        if y1 > 287:
            y1=287
        yL=y1&0x00FF
        yH=(y1&0xFF00)>>8
        self.ctrl_tx(dc1100.CFEPO_ENY_L,yL)
        self.ctrl_tx(dc1100.CFEPO_ENY_H,yH)      
        
        # print("vdi_set_capture_frame: ({},{}) - ({},{})".format(x0,y0,x1,y1))
        
        if self.videoSource == VIDEO_SOURCE_TV :
            self.vdCaptureFrameTv=Frame(Position(x0,y0),Position(x1,y1))
        if self.videoSource == VIDEO_SOURCE_COMPOSITE :
            self.vdCaptureFrameComposite=Frame(Position(x0,y0),Position(x1,y1))
        if self.videoSource == VIDEO_SOURCE_S_VIDEO :
            self.vdCaptureFrameSVideo=Frame(Position(x0,y0),Position(x1,y1))
        
        self.videoCaptureSize.width=int((x1-x0)//2)
        self.videoCaptureSize.height=int((y1-y0)*2)
        
    def vdi_get_capture_frame(self):
        """Get capture frame, store it for current video source and set video size."""
        xL=self.ctrl_rx(dc1100.CFSPO_STX_L)
        xH=self.ctrl_rx(dc1100.CFSPO_STX_H)
        x0=256*xH + xL
        xL=self.ctrl_rx(dc1100.CFEPO_ENX_L)
        xH=self.ctrl_rx(dc1100.CFEPO_ENX_H)
        x1=256*xH + xL
        yL=self.ctrl_rx(dc1100.CFSPO_STY_L)
        yH=self.ctrl_rx(dc1100.CFSPO_STY_H)
        y0=256*yH + yL
        yL=self.ctrl_rx(dc1100.CFEPO_ENY_L)
        yH=self.ctrl_rx(dc1100.CFEPO_ENY_H)
        y1=256*yH + yL
        
        self.vd_capture_frame=Frame(Position(x0,y0),Position(x1,y1))
        
        if self.videoSource == VIDEO_SOURCE_TV :
            self.vdCaptureFrameTv=Frame(Position(x0,y0),Position(x1,y1))
        if self.videoSource == VIDEO_SOURCE_COMPOSITE :
            self.vdCaptureFrameComposite=Frame(Position(x0,y0),Position(x1,y1))
        if self.videoSource == VIDEO_SOURCE_S_VIDEO :
            self.vdCaptureFrameSVideo=Frame(Position(x0,y0),Position(x1,y1))
            
        self.videoCaptureSize.width=int((x1-x0)//2)
        self.videoCaptureSize.height=int((y1-y0)*2)
     
    def print_video_capture(self):
        """Print video capture geometry."""
        self.get_video_capture()
        x0=self.videoCaptureStart.x
        y0=self.videoCaptureStart.y
        x1=self.videoCaptureEnd.x
        y1=self.videoCaptureEnd.y
        w=self.videoCaptureSize.width
        h=self.videoCaptureSize.height
        print ("({x0},{y0}) - ({x1},{y1}) : {w}x{h}".format(x0=x0,y0=y0,x1=x1,y1=y1,w=w,h=h)) 
     
    def get_video_capture (self):
        """Get start position, end position and size of video capture frame.""" 
        self.vdi_get_capture_frame()
        x0=self.vd_capture_frame.start.x
        y0=self.vd_capture_frame.start.y
        x1=self.vd_capture_frame.end.x
        y1=self.vd_capture_frame.end.y
        X0=x0//2
        X1=x1//2
        Y0=y0*2
        Y1=y1*2
        W=X1-X0
        H=Y1-Y0
        self.videoCaptureStart=Position(X0,Y0)
        self.videoCaptureEnd=Position(X1,Y1)
        self.videoCaptureSize=Size(W,H)
        
    def set_video_capture(self,X,Y,W,H):
        """Set video capture frame WxH+X+Y""" 
        if X < 0 :
            X = 0
        if Y < 0:
            Y = 0
        if W > 720 :
            W = 720
        if H > 576 :
            H = 576
            
        x0 = X*2
        y0 = Y//2
        x1=(X+W)*2
        y1=(Y+H)//2

        self.vdi_set_capture_frame(Frame(Position(x0,y0),Position(x1,y1)))
        
    def video_decoder_status_video_standard(self):
        """Get Status #5 of the video decoder chip TVP5150AM1.
           Get video standard of the video decoder.
           Save video standard of the video decoder for current video source.
        """
        self.sbi_select_device(0xba)
        s5=self.video_decoder_status(5)
        b7=utils.get_bit(s5,7)
        b3=utils.get_bit(s5,3)
        b2=utils.get_bit(s5,2)
        b1=utils.get_bit(s5,1)
        b0=utils.get_bit(s5,0)
        
        vStd= b0 | b1 << 1 | b2 << 2 | b3 << 3
        autoSwitched=b7

        print("video_decoder_status_video_standard: Status #5 : {v:04d} | 0x{v:02x} | {b}".format(v=s5,b=utils.byte2bits(s5)))
        print("video_decoder_status_video_standard: Status #5 - Video standard : {v:04d} | 0x{v:02x} | {b}".format(v=vStd,b=utils.byte2bits(vStd)))
        
        self.vdVideoStandard=0
        
        if vStd==1 :
            if autoSwitched :
                self.vdVideoStandardAuto=VIDEO_STANDARD_NTSC_M_J
            else:
                self.vdVideoStandard=VIDEO_STANDARD_NTSC_M_J
        if vStd==3 :
            if autoSwitched :
                self.vdVideoStandardAuto=VIDEO_STANDARD_PAL_B_G_H_I_N
            else:
                self.vdVideoStandard=VIDEO_STANDARD_PAL_B_G_H_I_N
        if vStd==5 :
            if autoSwitched :
                self.vdVideoStandardAuto=VIDEO_STANDARD_PAL_M
            else:
                self.vdVideoStandard=VIDEO_STANDARD_PAL_M
        if vStd==7 :
            if autoSwitched :
                self.vdVideoStandardAuto=VIDEO_STANDARD_PAL_Nc
            else:
                self.vdVideoStandard=VIDEO_STANDARD_PAL_Nc
        if vStd==9 :
            if autoSwitched :
                self.vdVideoStandardAuto=VIDEO_STANDARD_NTSC
            else:
                self.vdVideoStandard=VIDEO_STANDARD_NTSC
        if vStd==11 :
            if autoSwitched :
                self.vdVideoStandardAuto=VIDEO_STANDARD_SECAM
            else:
                self.vdVideoStandard=VIDEO_STANDARD_SECAM
        if autoSwitched :
                self.vdVideoStandard=self.vdVideoStandardAuto
            
        if self.videoSource == VIDEO_SOURCE_TV :
            self.vdVideoStandardTv=self.vdVideoStandard
        if self.videoSource == VIDEO_SOURCE_COMPOSITE :
            self.vdVideoStandardComposite=self.vdVideoStandard
        if self.videoSource == VIDEO_SOURCE_S_VIDEO :
            self.vdVideoStandardSVideo=self.vdVideoStandard

        if autoSwitched :
            print("video_decoder_status_video_standard: Video standard: ",list_video_standards[self.vdVideoStandard]," (auto switched)")
        else :
            print("video_decoder_status_video_standard: Video standard: ",list_video_standards[self.vdVideoStandard])

    def video_decoder_get_video_standard(self):
        """Get video standard of the video decoder chip TVP5150AM1."""
        # Video Standard Register: 0x28
        # Video standard
        # 0000 = Autoswitch mode (default)
        # 0001 = Reserved
        # 0010 = (M, J) NTSC ITU-R BT.601
        # 0011 = Reserved
        # 0100 = (B, G, H, I, N) PAL ITU-R BT.601
        # 0101 = Reserved
        # 0110 = (M) PAL ITU-R BT.601
        # 0111 = Reserved
        # 1000 = (Combination-N) PAL ITU-R BT.601
        # 1001 = Reserved
        # 1010 = NTSC 4.43 ITU-R BT.601
        # 1011 = Reserved
        # 1100 = SECAM ITU-R BT.601
        # With the autoswitch code running, the application can force the device to operate in a particular video
        # standard mode by writing the appropriate value into this register.
        
        self.sbi_select_device(0xba)
        self.vdVideoStandard=self.sbi_read(0x28)
            
    def video_decoder_set_video_standard(self,vs):
        """Select video standard of the video decoder chip TVP5150AM1."""
        self.sbi_select_device(0xba)
        self.sbi_write(0x28,vs)
    
    def video_decoder_get_vertical_line_count(self):
        """Return vertical line count of the video decoder chip TVP5150AM1."""
        self.sbi_select_device(0xba)
        vlc_h=self.sbi_read(0x84)
        vlc_l=self.sbi_read(0x85)
        vlc=256*vlc_h+vlc_l
        self.vdVerticalLineCount=vlc

    
    def video_decoder_status(self,n):
        """Return the nth status byte of the video decoder chip TVP5150AM1."""
        self.sbi_select_device(0xba)
        s=False
        if n == 1:
            s=self.sbi_read(0x88)
        if n == 2:
            s=self.sbi_read(0x89)
        if n == 3:
            s=self.sbi_read(0x8a)
        if n == 4:
            s=self.sbi_read(0x8b)
        if n == 5:
            s=self.sbi_read(0x8c)
        return s
    
    def video_decoder_set_brightness(self,brightness):
        """Set video brightness."""
        if brightness < 0.0 :
            brightness=0.0
        if brightness > 1.0 :
            brightness=1.0
        b=int(brightness*255)
        self.sbi_select_device(0xba)
        self.sbi_write(0x0009,b)

    def video_decoder_set_contrast(self,contrast):
        """Set video contrast."""
        if contrast < 0.0 :
            contrast=0.0
        if contrast > 1.0 :
            contrast=1.0
        c=int(contrast*255)
        self.sbi_select_device(0xba)
        self.sbi_write(0x000c,c)
        
    def video_decoder_set_hue(self,hue):
        """Set video hue."""
        if hue > 0.4985 :
            hue = 127/255
        if hue < -0.4985:
            hue = -128/255 
        h=int(hue*255)
        if h < 0 :
            h=255+h           
        self.sbi_select_device(0xba)
        self.sbi_write(0x000b,h)

    def video_decoder_set_saturation(self,saturation):
        """Set video saturation."""
        if saturation < 0.0 :
            saturation=0.0
        if saturation > 1.0 :
            saturation=1.0
        s=int(saturation*255)
        self.sbi_select_device(0xba)
        self.sbi_write(0x000a,s)
        
    def set_audio_source(self,audio_source):
        """Select audio source."""
        if audio_source == AUDIO_SOURCE_NONE:
            self.audioSource=AUDIO_SOURCE_NONE
            c = self.ctrl_rx(dc1100.GCTRL+2)
            self.ctrl_tx(dc1100.GCTRL+2,0x00e8)
            c = self.ctrl_rx(dc1100.GCTRL+3)
            self.ctrl_tx(dc1100.GCTRL+3,0x0001)
            c = self.ctrl_rx(dc1100.GCTRL)
            self.ctrl_tx(dc1100.GCTRL,0x001a)
            c = self.ctrl_rx(dc1100.GCTRL+1)
            self.ctrl_tx(dc1100.GCTRL+2,0x0002)
        if audio_source == AUDIO_SOURCE_AUX :
            self.audioSource=AUDIO_SOURCE_AUX
            c = self.ctrl_rx(dc1100.GCTRL+2)
            self.ctrl_tx(dc1100.GCTRL+2,0x00e8)
            c = self.ctrl_rx(dc1100.GCTRL+3)
            self.ctrl_tx(dc1100.GCTRL+3,0x0001)
            c = self.ctrl_rx(dc1100.GCTRL)
            self.ctrl_tx(dc1100.GCTRL,0x009a)
            c = self.ctrl_rx(dc1100.GCTRL+1)
            self.ctrl_tx(dc1100.GCTRL+1,0x0002)
        if audio_source == AUDIO_SOURCE_TV_TUNER :
            self.audioSource=AUDIO_SOURCE_TV_TUNER
            c = self.ctrl_rx(dc1100.GCTRL+2)
            self.ctrl_tx(dc1100.GCTRL+2,0x00e8)
            c = self.ctrl_rx(dc1100.GCTRL+3)
            self.ctrl_tx(dc1100.GCTRL+3,0x0001)
            c = self.ctrl_rx(dc1100.GCTRL)
            self.ctrl_tx(dc1100.GCTRL,0x001a)
            c = self.ctrl_rx(dc1100.GCTRL+1)
            self.ctrl_tx(dc1100.GCTRL+1,0x0003)
        
    def set_video_source(self,video_source):
        """Select video source."""
        if video_source == VIDEO_SOURCE_TV :
            print("Setting video source: TV")
            self.videoSource=VIDEO_SOURCE_TV   
            print("  Tuner frequency: {f:.2f} MHz".format(f=self.tvTunerFrequency))
            print("  Video standard:",list_video_standards[self.vdVideoStandardTv])
            print("  Capture frame:",self.vdCaptureFrameTv)
             
            vdVideoStandard=self.vdVideoStandardTv
      
            self.ctrl_tx(dc1100.GCTRL,0x0028) # GCTRL:GV
            self.ctrl_tx(dc1100.GCTRL+2,0x0068) # GCTRL:GDIR
            self.ctrl_tx(dc1100.RMCTL+1,0x0000) # RMCTL:RWP Remote Wakeup Polarity (GPIO[9:8])
            self.ctrl_tx(dc1100.RMCTL+3,0x0002) # RMCTL:RWC Remote Wakeup Control (GPIO[9:8])

            self.tg_set_timings()

            self.ctrl_tx(0x0018,0x0010) # PLLSO 
            self.ctrl_tx(0x0019,0x0000) # PLLSO 

            self.sbi_clock_divider(0x1e) # SICTL:CD
        
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0082)
            self.sbi_write(0x000f,0x000a) # Configuration Shared Pins Register
            self.sbi_write(0x0030,0x0001) # 656 Revision Select Register 1 = Adheres to ITU-R BT.656.3 timing
            self.sbi_write(0x0003,0x006f) # Miscellaneous Controls Register
            self.set_audio_source(AUDIO_SOURCE_NONE)
            
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0003)
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.sbi_write(0x0000,0x0002) # Video Input Source Selection #1 Register: 0x02 -  Composite AIP1B
            self.sbi_write(0x0003,0x006f) # Miscellaneous Controls Register

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0003)
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.sbi_write(0x0000,0x0001) # Video Input Source Selection #1 Register: 0x01 - S-Video AIP1A (luminance), AIP1B (chrominance)
            self.sbi_write(0x0003,0x002f) # Miscellaneous Controls Register

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0003)
            
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.sbi_write(0x0000,0x0000) # Video Input Source Selection #1 Register: 0x00 - -  Composite AIP1A (default)
            self.sbi_write(0x0003,0x006f) # Miscellaneous Controls Register

            self.video_decoder_set_video_standard(self.vdVideoStandardTv)

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.sbi_write(0x0030,0x0000)   # 656 Revision Select Register: 0000 = Adheres to ITU-R BT.656.4 and BT.656.5 timing (default)
                                            # 656 Revision Select Register: 0001 = Adheres to ITU-R BT.656.3 timing

            self.vdi_set_capture_frame(self.vdCaptureFrameTv)

            #   === Set audio source  
            self.set_audio_source(AUDIO_SOURCE_TV_TUNER)

            #   === Tuner frequency  setting    
            self.set_tv_tuner(self.tvTunerFrequency)
        
            self.get_video_capture()
            self.vdi_start_capture() 

        if video_source == VIDEO_SOURCE_COMPOSITE :
            print("Setting video source: Composite")
            self.videoSource = VIDEO_SOURCE_COMPOSITE
          
            print("  Video standard:",list_video_standards[self.vdVideoStandardComposite])
            print("  Capture frame:",self.vdCaptureFrameComposite)
          
            self.ctrl_tx(dc1100.GCTRL,0x0028) # GCTRL:GV
            self.ctrl_tx(dc1100.GCTRL+2,0x0068) # GCTRL:GDIR
            self.ctrl_tx(0x000d,0x0000) # RMCTL:RWP Remote Wakeup Polarity (GPIO[9:8])
            self.ctrl_tx(0x000f,0x0002) # RMCTL:RWC Remote Wakeup Control (GPIO[9:8])

            self.tg_set_timings()
                
            self.ctrl_tx(0x0018,0x0010) # ?
            self.ctrl_tx(0x0019,0x0000) # ?
                
            self.sbi_clock_divider(0x1e)    # SICTL:CD

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0082)
            self.sbi_write(0x000f,0x000a) # Configuration Shared Pins Register
            self.sbi_write(0x0030,0x0001) # 656 Revision Select Register 1 = Adheres to ITU-R BT.656.3 timing
            self.sbi_write(0x0003,0x006f) # Miscellaneous Controls Register

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0003)
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.sbi_write(0x0000,0x0002) # Video Input Source Selection #1 Register: 0x02 -  Composite AIP1B
            self.sbi_write(0x0003,0x006f) # Miscellaneous Controls Register

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.video_decoder_set_video_standard(self.vdVideoStandardComposite)

            self.sbi_write(0x0030,0x0000)

            self.vdi_set_capture_frame(self.vdCaptureFrameComposite)
            self.get_video_capture()
            
            #   === Set audio source 
            self.set_audio_source(AUDIO_SOURCE_AUX)
 
            self.get_video_capture()
            self.vdi_start_capture()

        if video_source == VIDEO_SOURCE_S_VIDEO :
            print("Setting video source: S-Video")
            print("  Video standard:",list_video_standards[self.vdVideoStandardSVideo])
            print("  Capture frame:",self.vdCaptureFrameSVideo)
            
            self.videoSource = VIDEO_SOURCE_S_VIDEO

            self.vdi_set_capture_frame(self.vdCaptureFrameSVideo)


            self.ctrl_tx(dc1100.GCTRL,0x0028) # GCTRL:GV
            self.ctrl_tx(dc1100.GCTRL+2,0x0068) # GCTRL:GDIR
            self.ctrl_tx(0x000d,0x0000) # RMCTL:RWP Remote Wakeup Polarity (GPIO[9:8])
            self.ctrl_tx(0x000f,0x0002) # RMCTL:RWC Remote Wakeup Control (GPIO[9:8])

            self.tg_set_timings()
                
            self.ctrl_tx(0x0018,0x0010) # ?
            self.ctrl_tx(0x0019,0x0000) # ?
                
            self.sbi_clock_divider(0x1e)    # SICTL:CD

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0082)
            self.sbi_write(0x000f,0x000a) # Configuration Shared Pins Register
            self.sbi_write(0x0030,0x0001) # 656 Revision Select Register 1 = Adheres to ITU-R BT.656.3 timing
            self.sbi_write(0x0003,0x006f) # Miscellaneous Controls Register

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            c = self.sbi_read(0x0003)
            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.sbi_write(0x0000,0x0001) # Video Input Source Selection #1 Register: 0x01 -  Composite AIP1B
            self.sbi_write(0x0003,0x000d) # Miscellaneous Controls Register

            self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
            self.video_decoder_set_video_standard(self.vdVideoStandardComposite)

            self.sbi_write(0x0030,0x0000)

            self.vdi_set_capture_frame(self.vdCaptureFrameComposite)
            self.get_video_capture()


            #   === Set audio source 
            self.set_audio_source(AUDIO_SOURCE_AUX) 
            
            self.get_video_capture()
            self.vdi_start_capture()
           
    def tv_tuner_select_band(self,frequencyMHz):
        """Return band select byte.
        M026 device has a LG Innotek TALN - M205T tuner which can receive 40 - 900 MHz signal.
        Bands and band select bytes are:
        Band                 BB
        -------------------  ----
          [40.0, ..., 45.0]  0x00
         (45.0, ..., 142.0]  0x01
        (142.0, ..., 147.0]  0x00
        (147.0, ..., 425.0]  0x02
        (425.0, ..., 431.0]  0x00
        (431.0, ..., 900.0]  0x08
        """
        bb=0x00
        if frequencyMHz>45.0 and frequencyMHz <= 142.0 :
            bb=0x01
        if frequencyMHz>147.0 and frequencyMHz <= 425.0 :
            bb=0x02
        if frequencyMHz>431.0 and frequencyMHz <= 900.0 :
            bb=0x08
        return bb
    
    def tv_tuner_set_frequency(self,frequencyMHz):
        """Set TV tuner frequency."""
        VFRQ=int(16*frequencyMHz)+618
        DB2=VFRQ&0x00FF
        DB1=(VFRQ>>8)&0x00FF
        # print("VFRQ_H,VFRQ_L: 0x{h:02x} 0x{l:02x}".format(h=DB1,l=DB2))
        CB=0x8e
        BB=self.tv_tuner_select_band(frequencyMHz)
        self.sbi_select_device(0x42) # Slave address
        self.sbi_select_device(0xc2) # Subaddress
        self.sbi_write(DB1,DB2)
        self.sbi_write(CB,BB)
        
    def set_tv_tuner(self,frequencyMHz): 
        """Set TV tuner."""
        self.tv_tuner_set_frequency(frequencyMHz)
        time.sleep(0.5)
        self.sbi_select_device(0x00ba) # TVP5150AM1 Chip
        status1=self.video_decoder_status(1)
        print("Video decoder status 1: 0x{s:02x} {b}".format(s=status1,b=utils.byte2bits(status1)))

        self.vdVerticalSyncLocked=utils.get_bit(status1,2)
        self.vdHorizontalSyncLocked=utils.get_bit(status1,1)
        
        if self.vdVerticalSyncLocked and self.vdHorizontalSyncLocked :
            self.vdVideoDetected=True
        else :
            self.vdVideoDetected=False
    
        self.sbi_select_device(0x0042)
        self.sbi_select_device(0x0086)
        self.sbi_write(0x0000,0x00d6)
        self.sbi_write(0x0001,0x0070)
        self.sbi_write(0x0002,0x0049)
        
        self.tvTunerFrequency=frequencyMHz
        return True

 

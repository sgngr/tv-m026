# tvM026
**A TV app for the AVerMedia AVerTV USB2.0**

---

tvM026 is a Linux app for the AVerMedia AVerTV USB2.0 (USB Id: 07ca:0026). The main controller of the device - Crescentec/Syntek CT-DC1100 video controller - is an ancestor of Syntek STK11xx series video imaging controllers and has similar registers with this series of controllers. 
The Python class `M026Device` provides a set of functions to control hardware.


## Requirements

- Device access
    
    For non-root users, an udev rule is necessary to access the device.

    `SUBSYSTEM=="usb", ATTR{idVendor}=="07ca", ATTR{idProduct}=="0026", MODE="0666"`

- v4l2loopback kernel module

    Loading kernel module for the video device /dev/video0:
    
    `sudo modprobe v4l2loopback exclusive_caps=0 video_nr=0 card_label="AVerMedia AVerTV USB 2.0"`

- VLC media player
    
    It is used to play audio and video stream. 
    
- Python >= 3.7
   
    It is recommended that using a virtual environment and installing the required modules with the command
   
    `pip install -r requirements.txt`

## Notes

- Audio control

    Audio control is only possible if the headphone output signal is transmitted to a sound input on the computer.
    
- TV system 

    The device is for reception of analog television signals. In the `tvChannels' module, a frequency dictinoary is given for PAL B/G TV standard.
    It needs to be modified for other TV standards.

- Channel scanner

    Use `tvM026-channel-scanner` to create and modify channel list.

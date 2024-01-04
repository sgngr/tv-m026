"""
================================================
A TV app for the AVerMedia AVerTV USB2.0
VLC module
================================================
Version:    0.1
Author:     Sinan Güngör
License:    GPL v2
"""

import vlc

class VlcApp(object):
    def __init__(self,audioMedia,videoMedia):
        self.audioMedia=audioMedia
        self.videoMedia=videoMedia
        self.vlcInstance=vlc.Instance("--video-on-top")
        self.audioPlayer=self.vlcInstance.media_player_new()
        self.videoPlayer=self.vlcInstance.media_player_new()
        if self.audioMedia != None:
            mediaAudio=self.vlcInstance.media_new(self.audioMedia)
            self.audioPlayer.set_media(mediaAudio)
        if self.videoMedia != None:
            mediaVideo=self.vlcInstance.media_new(self.videoMedia)
            self.videoPlayer.set_media(mediaVideo)         
    def set_audio_media(self,media):
        self.audioMedia=media
        mediaAudio=self.vlcInstance.media_new(media)
        self.audioPlayer.set_media(mediaAudio)
    def set_video_media(self,media):
        self.videoMedia=media
        mediaVideo=self.vlcInstance.media_new(media)
        self.videoPlayer.set_media(mediaVideo)

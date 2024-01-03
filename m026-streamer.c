/*
* m026-streamer.c
* Version:    0.1
* Author:     Sinan Güngör
* This code is to transmit the video data to a v4l2loopback device
* Compiling: gcc -lusb-1.0 m026-streamer.c -o m026-streamer
*/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <stdbool.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <assert.h>
#include <libusb-1.0/libusb.h>
#include <linux/videodev2.h>

#define VENDOR_ID 0x07ca
#define PRODUCT_ID 0x0026

volatile bool running = true;
volatile bool interrupted = false;
volatile bool verbose = false;
volatile bool update_capture = false;

static struct libusb_device_handle *devh = NULL;
static char buf[1024];

void ctrl_tx(int index, uint16_t value) {
   int r;
   r = libusb_control_transfer(devh,0x40,1,value,index,buf,0,1000);
}

unsigned char ctrl_rx(int index){
    int r;
    r = libusb_control_transfer(devh,0xc0,0,0,index,buf,1,1000);
    return buf[0];
}

static char v4l2_device[16];
int dev_fd;

char isobuf0[64 * 3072];
char isobuf1[64 * 3072];
char isobuf2[64 * 3072];
char isobuf3[64 * 3072];

static int startX = 0;
static int startY = 0;
static int endX = 1440;
static int endY = 288;

static int width = 720;
static int height = 576;

// Capture Frame Start Position 
#define DC1100_CFSPO 0x110
#define DC1100_CFSPO_STX_L 0x110
#define DC1100_CFSPO_STX_H 0x111
#define DC1100_CFSPO_STY_L 0x112
#define DC1100_CFSPO_STY_H 0x113

// Capture Frame End Position
#define DC1100_CFEPO 0x114
#define DC1100_CFEPO_ENX_L 0x114
#define DC1100_CFEPO_ENX_H 0x115
#define DC1100_CFEPO_ENY_L 0x116
#define DC1100_CFEPO_ENY_H 0x117

void getCaptureStart(){
    uint8_t xL, xH, yL, yH;
    xL=ctrl_rx(DC1100_CFSPO_STX_L);
    xH=ctrl_rx(DC1100_CFSPO_STX_H);
    startX=(int)(xH*256+xL);
    yL=ctrl_rx(DC1100_CFSPO_STY_L);
    yH=ctrl_rx(DC1100_CFSPO_STY_H);
    startY=(int)(yH*256+yL);
}

void getCaptureEnd(){
    uint8_t xL, xH, yL, yH;
    xL=ctrl_rx(DC1100_CFEPO_ENX_L);
    xH=ctrl_rx(DC1100_CFEPO_ENX_H);
    endX=(int)(xH*256+xL);
    yL=ctrl_rx(DC1100_CFEPO_ENY_L);
    yH=ctrl_rx(DC1100_CFEPO_ENY_H);
    endY=(int)(yH*256+yL);
}

size_t video_buffer_size;
uint8_t *video_buffer;
int video_offset=0;

size_t line_size;
uint8_t *line_buffer;
size_t line_offset=0;

int line=0;

uint8_t field=0;
uint8_t prev_field=0;

int bytes_in_field1=0;
int bytes_in_field2=0;
int bytes_in_frame=0;

int iTransfer=0;
int iFrame=0;

int setV4L2format(){

    fprintf(stderr, "* Setting v4l2 stream format\n");
    struct v4l2_format sdf;;
    sdf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
	if (ioctl(dev_fd, VIDIOC_G_FMT, &sdf) == -1) {
		fprintf(stderr, "*  ~~~ Can not get video device! ~~~\n");
		return(1);
	}
	fprintf(stderr, "*  Current v4l2 stream data format - Width: %d \n",sdf.fmt.pix.width);
    fprintf(stderr, "*  Current v4l2 stream data format - Height: %d \n",sdf.fmt.pix.height);
    fprintf(stderr, "*  Current v4l2 stream data format - Pixel format: %d \n",sdf.fmt.pix.pixelformat);
    
    sdf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
	sdf.fmt.pix.width = width;
	sdf.fmt.pix.height = height;
	sdf.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
	sdf.fmt.pix.sizeimage = video_buffer_size;
	sdf.fmt.pix.field = V4L2_FIELD_NONE;
	sdf.fmt.pix.colorspace = V4L2_COLORSPACE_REC709;
    
    fprintf(stderr, "* Set width: %d\n",sdf.fmt.pix.width);
    fprintf(stderr, "* Set height: %d\n",sdf.fmt.pix.height);
    
	if (ioctl(dev_fd, VIDIOC_S_FMT, &sdf) == -1) {
		fprintf(stderr, "*  ~~~ Can not set video device! ~~~\n");
		return(1);
	}
    
    if (ioctl(dev_fd, VIDIOC_G_FMT, &sdf) == -1) {
		fprintf(stderr, "*  ~~~ Can not get video device! ~~~\n");
		return(1);
	} 
	fprintf(stderr, "* v4l2 stream format is set\n");
	fprintf(stderr, "*  v4l2 stream data format - Width: %d \n",sdf.fmt.pix.width);
    fprintf(stderr, "*  v4l2 stream data format - Height: %d \n",sdf.fmt.pix.height);
    fprintf(stderr, "*  v4l2 stream data format - Pixel format: %d \n",sdf.fmt.pix.pixelformat);
    
    return(0);
}  


void getData_M026(struct libusb_transfer *trf){

    int n_packets = trf->num_iso_packets;
    
    int p;
    for(p =0 ; p < n_packets; p++ ) {
        
        char *data = libusb_get_iso_packet_buffer(trf, p );
        char *video_data;
        int video_data_len;
        
        // fprintf( stderr, "--- %06d, %02d, %04d --------------------------\n",iTransfer,p,trf->iso_packet_desc[p].actual_length);
        
        int l;
        l=trf->iso_packet_desc[p].actual_length;
        
        if ( l > 0) {
            
            if (data[1] == 0x40 || data[1] == 0xc0 )
                field=1;
            if (data[1] == 0x00 )
                field=2;

            // fprintf(stderr, "Line %3d, Field: %d\n",line, field);  
            
            if (prev_field == 2 && field == 1){
                line_offset=0;
                line=0;
                video_offset=0;
                
                bytes_in_frame=0;
                bytes_in_field1=0;
                bytes_in_field2=0;
            }
            
            if (prev_field == 1 && field == 2){
                line_offset=0;
                line=1;
                video_offset=line_size;
            }
      
        }   
                
        l=trf->iso_packet_desc[p].actual_length;
        if  ( l > 10 ) {
            video_data=data+2;    
            video_data_len=l-2;
            
            int remain=video_data_len;
            int video_data_offset=0;
            
            while (remain > 0 ) {
                int to_copy=line_size-line_offset;
                if (remain >= to_copy) {
                    for (int i=0;i<to_copy;i++)
                        line_buffer[line_offset+i]=video_data[video_data_offset+i];
                    line_offset+=to_copy;
                    
                    for (int i=0;i<line_size;i++){
                        // fprintf(stderr,"%d < %d\n",video_offset+i, video_buffer_size);
                        if (video_offset+i < video_buffer_size)
                        video_buffer[video_offset+i]=line_buffer[i];
                    }
                    video_offset+=line_size;
                    video_offset+=line_size ;
                    line+=2;
                    
                    line_offset=0;
                    
                    video_data_offset+=to_copy;
                    remain-=to_copy;
                }
                else {
                    to_copy=remain;
                    for (int i=0;i<to_copy;i++)
                        line_buffer[line_offset+i]=video_data[video_data_offset+i];
                    line_offset+=to_copy;
                    video_data_offset+=to_copy;
                    remain-=to_copy;
                }  
            }    
            
            video_offset=video_offset%video_buffer_size;
                    
            if (line >= (height-1) ){
                if (verbose == true)
                switch (iFrame%16){
                  case 0:
                    fprintf(stderr,"* -\n");
                    break;
                  case 1: 
                    fprintf(stderr,"* \\\n");
                    break;
                  case 2:
                    fprintf(stderr,"* |\n");
                    break;
                  case 3: 
                    fprintf(stderr,"* /\n");
                    break;
                  default:
                    break;
                } 
                
                size_t written_bytes ;	
                written_bytes = write(dev_fd,video_buffer, video_buffer_size);
                line=0;
                line_offset=0;
                video_offset=0;
                iFrame++;
            }   
            
            bytes_in_frame+=video_data_len;
            if (field == 1 )
                bytes_in_field1+=video_data_len;
            if (field == 2 )
                bytes_in_field2+=video_data_len;
    
        } 
        
        prev_field=field;
    
    }    
    
    int r;
    r = libusb_submit_transfer(trf);
    if (r != 0) {
        fprintf( stderr, "* libusb_submit_transfer failed with error %d\n", r);
        exit(1);
    }
    
    iTransfer++;
}

void signalHandler(int signal){
    fprintf(stderr, "\n* --> Signal: %d\n",signal);
    if (signal == SIGINT || signal == SIGTERM || signal == SIGQUIT || signal == SIGTSTP) 
        running = false;
    if (signal == SIGUSR1) {
        update_capture = true ;
        interrupted = false ;
        fprintf(stderr, "\n* --> Capture update or streaming resume request\n");
    }
    if (signal == SIGUSR2){
        interrupted = true ;
        fprintf(stderr, "\n* --> Streaming interrupt request\n");
    }
}


int main (int argc, char **argv) {

    sprintf(v4l2_device,"%s","/dev/video0");
    printf("* <----------------\n* Streamer started!\n");
    int opt;
    while((opt = getopt(argc, argv, ":id:w:h:v")) != -1)
	{
		switch(opt)
		{
            case 'd' :
                sprintf(v4l2_device,"%s",optarg);
                fprintf(stderr, "*  - v4l2 loopback device: %s\n", optarg);
                break;
			case 'w' :
                width = atoi(optarg);
                fprintf(stderr, "*  - Width: %d\n", width);
				break;
 			case 'h' :
                height = atoi(optarg);;
                fprintf(stderr, "*  - Height: %d\n", height);
				break; 
            case 'v' :
                verbose = true;
                break;
			case '?' :
				fprintf(stderr, "*  - Unknown option: %c\n", optopt);
				break;
		}
	}
    
    // Handle signals
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    signal(SIGQUIT, signalHandler);
    signal(SIGTSTP, signalHandler);
    signal(SIGUSR1, signalHandler);
    signal(SIGUSR2, signalHandler);
    
    int r;
    char c;
    libusb_device *dev = NULL;

    int current_config=-1;
    int config=-1;

    int kernel_driver_detached=0;
    int interface=0;
    libusb_context *usb_context = NULL;

    r = libusb_init(&usb_context);
    if (r < 0) {
       fprintf(stderr, "* Error initializing libusb: %s\n", libusb_error_name(r));
       exit(1);
    }

    devh = libusb_open_device_with_vid_pid(NULL, VENDOR_ID,PRODUCT_ID);
    if (!devh) {
       fprintf(stderr, "* Error finding USB device\n");
       goto out;
    }

    r=libusb_set_auto_detach_kernel_driver(devh,0);
    if (r==LIBUSB_SUCCESS)
       fprintf(stderr, "* Auto detach kernel driver for interface %d is disabled.\n",0);

    if (libusb_kernel_driver_active(devh, 0) == 1) { //find out if kernel driver is attached
       fprintf(stderr, "* Kernel driver active!\n");
       if(libusb_detach_kernel_driver(devh, 0) == 0) { //detach it
           fprintf(stderr, "*  Kernel driver detached.\n");
           kernel_driver_detached=1;
       }
     }
        
    fprintf(stderr, "* Claiming interface ...\n");
    r = libusb_claim_interface(devh, interface);
    if (r != 0) {
       fprintf(stderr, "*  Claiming interface failed with error %d\n", r);
       exit(1);
    }
    fprintf(stderr, "*  Interface %d is allowed\n", interface);

    fprintf(stderr, "* Getting configuration ...\n");
    r = libusb_get_configuration(devh,&current_config);
    if (r != 0) {
       fprintf(stderr, "* !! Getting configuration failed with error %d\n", r);
    }
    fprintf(stderr,"*  Configuration %d is active\n",current_config);

    config=1;
    if ( current_config != config ) {
       fprintf(stderr, "* Setting configuration %d ...\n",config);
       r = libusb_set_configuration(devh,config);
       if (r != 0) {
           fprintf(stderr, "* !! Setting configuration %d failed with error %d\n", config, r);
       }
    }

    fprintf(stderr, "* Select interface ...\n");
    r = libusb_set_interface_alt_setting(devh, 0, 5);
    if (r != 0)
       fprintf(stderr, "* !! Select interface (0,5) failed with error %d\n", r);
    else
       fprintf(stderr,"*  Interface %d, Setting %d is active\n",0,5);
    
    getCaptureStart();
    getCaptureEnd();
	width=(endX-startX)/2;
	height=(endY-startY)*2;
        
    line_size=width*2;
    line_buffer = calloc(line_size, sizeof(uint8_t));
    
	video_buffer_size=line_size*height;
	video_buffer = calloc(video_buffer_size, sizeof(uint8_t));
    
    fprintf(stderr,"* m026: Capture start: (%d,%d)\n",startX,startY);
    fprintf(stderr,"* m026: Capture end: (%d,%d)\n",endX,endY);
    fprintf(stderr,"* m026: Width: %d\n* m026: Height: %d\n",width,height);
    
// --------------------------------------------------------------------------
	
    dev_fd = open(v4l2_device, O_RDWR);
	if (dev_fd < 0) {
		perror(v4l2_device);
		return errno;
	}
	
	r=setV4L2format();

	size_t written_bytes ;	
	written_bytes = write(dev_fd,video_buffer, video_buffer_size);

// --------------------------------------------------------------------------
 
	struct libusb_transfer *trf0;
	trf0 = libusb_alloc_transfer( 64 );
	assert( trf0 != NULL ); 
	libusb_fill_iso_transfer(trf0, devh, 0x82, isobuf0, 64*3072, 64 , getData_M026, NULL, 2000 );
	libusb_set_iso_packet_lengths(trf0, 3072 );
  
	struct libusb_transfer *trf1;
	trf1 = libusb_alloc_transfer( 64 );
	assert( trf1 != NULL ); 
	libusb_fill_iso_transfer(trf1, devh, 0x82, isobuf1, 64*3072, 64 , getData_M026, NULL, 2000 );
	libusb_set_iso_packet_lengths(trf1, 3072 );
	
	struct libusb_transfer *trf2;
	trf2 = libusb_alloc_transfer( 64 );
	assert( trf2 != NULL ); 
	libusb_fill_iso_transfer(trf2, devh, 0x82, isobuf2, 64*3072, 64 , getData_M026, NULL, 2000 );
	libusb_set_iso_packet_lengths(trf2, 3072 );
	
	struct libusb_transfer *trf3;
	trf3 = libusb_alloc_transfer( 64 );
	assert( trf3 != NULL ); 
	libusb_fill_iso_transfer(trf3, devh, 0x82, isobuf3, 64*3072, 64 , getData_M026, NULL, 2000 );
	libusb_set_iso_packet_lengths(trf3, 3072 );
	

	r = libusb_submit_transfer(trf0);
	if (r != 0) {
		fprintf( stderr, "* libusb_submit_transfer failed with error %d\n", r);
		exit(1);
    }

	r = libusb_submit_transfer(trf1);
	if (r != 0) {
		fprintf( stderr, "* libusb_submit_transfer failed with error %d\n", r);
		exit(1);
    }

	r = libusb_submit_transfer( trf2 );
	if (r != 0) {
		fprintf( stderr, "* libusb_submit_transfer failed with error %d\n", r);
		exit(1);
    }
 
	r = libusb_submit_transfer( trf3 );
	if (r != 0) {
		fprintf( stderr, "* libusb_submit_transfer failed with error %d\n", r);
		exit(1);
    }

  
// -------------------------------------------------------------------------- 

    loop:
    // Run until termination
    while (running == true){
        if (update_capture == true) {
                getCaptureStart();
                getCaptureEnd();
                width=(endX-startX)/2;
                height=(endY-startY)*2;
                
                line_size=width*2;
                line_buffer = realloc(line_buffer, line_size*sizeof(uint8_t));
                
                video_buffer_size=line_size*height;
                video_buffer = realloc(video_buffer,video_buffer_size*sizeof(uint8_t));
                
                r=setV4L2format();
                if(r>0)
                    fprintf(stderr,"* ~~~ Setting v4l2 stream data format failed! ~~~\n");
                else {    
                    fprintf(stderr,"* m026: Capture start: (%d,%d)\n",startX,startY);
                    fprintf(stderr,"* m026: Capture end: (%d,%d)\n",endX,endY);
                    fprintf(stderr,"* m026: Width: %d\n* m026: Height: %d\n",width,height);
                }
                update_capture = false;
        }
        if (interrupted != true)
            libusb_handle_events(NULL);
    }

    fprintf(stderr, "* Select interface ...\n");
    r = libusb_set_interface_alt_setting(devh, 0, 0);
    if (r != 0)
       fprintf(stderr, "* !! Select interface (0,0) failed with error %d\n", r);
    else
       fprintf(stderr,"*  Interface %d, Setting %d is active\n",0,0);
    
    printf("* End of program.\n* <----------------\n");
    
    out:
    if (devh)
       libusb_close(devh);
    libusb_exit(usb_context);
    
    close(dev_fd);
  
    return 0;
}

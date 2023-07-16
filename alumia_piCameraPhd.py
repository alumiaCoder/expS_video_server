from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder, H264Encoder
from picamera2.outputs import FileOutput
from libcamera import Transform
from alumia_mjpegServer import StreamingServer, StreamingHandler, StreamingOutput
import socket
from threading import Thread, Event
import queue
import os

import cv2

from numpy import linspace

LORES_RES = (320,180)

class PiCameraStream(object):

    def __init__(self, root_win_folder, root_mon_folder, resolution: tuple, quality: int, encoder_type: str, sub_folder="/video/"):

        self.camera = Picamera2()
        self.kill = Event()

        self.current_fps = 30
        self.current_exp = 0 # tenho de perceber qual o inicial
        
        self.cam_config = self.camera.create_video_configuration()  
        self.cam_config['lores'] = {"size": LORES_RES, 'format': 'YUV420'} #180?
        self.main_resolution = resolution
        self.main_quality = quality 
        self.encoder = self.select_encoder(encoder_type=encoder_type, quality=quality)

        self.camera.configure(self.cam_config)
        self.set_cam_param(temp_change=False, resolution=resolution, quality=quality)        

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thread = 0 #used in http video server
        self.server = 0 #used in http video server

        #init the thread used to write the low res file
        self.lores_queue = queue.Queue(maxsize=1)
        self.lores_event = Event()
        self.lores_thread = Thread(target=self.lores_write, args=())
        self.lores_thread.daemon = True
        self.lores_thread.start()
        
        #STATE
        self.current_snippet = -1
        self.current_main = -1
        self.stream_state = False
        self.record_state = False
        self.root_win_folder = root_win_folder
        self.root_mon_folder = root_mon_folder
        self.date_folder = ""
        self.perf_folder = ""
        self.sub_folder = sub_folder
        self.total_win_path = ""
        self.total_mon_path = ""
        
        self.camera.start()

    def change_work_folder(self, date_folder, perf_folder):
        
        #WIN FOLDER
        partial_path = self.root_win_folder + date_folder + "/" + perf_folder
        if os.path.exists(partial_path):

            self.date_folder = date_folder
            self.perf_folder = perf_folder

            full_path = partial_path + self.sub_folder

            if not os.path.exists(full_path):
                os.mkdir(full_path)

            self.total_win_path = full_path
            self.get_last_video_number()
        
        #MONITOR FOLDER
        if not os.path.exists(self.root_mon_folder + date_folder):
            os.mkdir(self.root_mon_folder + date_folder)
        
        total_path = self.root_mon_folder + date_folder + "/" + perf_folder + "/"
        if not os.path.exists(total_path):
            os.mkdir(total_path)
        
        self.total_mon_path = total_path

    def get_last_video_number(self):
        
        all_files = os.scandir(self.total_win_path)
        large_n_main = -1
        large_n_snippet = -1
        for entry in all_files:
            if entry.name[-5:] == "mjpeg" and int(entry.name[:-6]) >= large_n_main:
                large_n_main = int(entry.name[:-6])

        all_files = os.scandir(self.total_win_path)
        # after finding the largest main, search for the largest snippet
        if large_n_main != -1:
            for entry in all_files:
                if entry.name[-3:] == "avi" and int(entry.name[:-4].split("_")[1]) >= large_n_snippet:
                    large_n_snippet = int(entry.name[:-4].split("_")[1])

        self.current_main = large_n_main
        self.current_snippet = large_n_snippet

    def select_encoder(self, encoder_type: str, quality: int):

        if encoder_type == "jpeg":
            encoder = JpegEncoder(q=quality)
        elif encoder_type == "h264":
            encoder = H264Encoder(q=quality)

        return [encoder, encoder_type]

    def init_perf(self):

        if self.record_state == False and self.stream_state == False:
            self.get_last_video_number()
            self.record_main()
            self.record_state = True
    
    def end_perf(self):

        if self.record_state == True:

            self.stop_recording()
            self.record_state = False

    def record_main(self):
        
        self.current_main += 1
        print("Recording main", self.current_main)
        output_name = self.total_win_path+str(self.current_main)+".mjpeg"
        self.camera.start_encoder(self.encoder[0], output=output_name)

    def record_snippet(self):
        
        self.current_snippet += 1
        
        self.lores_queue.put(str(self.current_main) + "_" + str(self.current_snippet))
        self.lores_event.set()

        self.record_state = True

    def record_stream(self, encoder, output):

        encoder.output = FileOutput(output)
        self.camera.start_encoder(encoder)

    def lores_write(self):

        while not self.kill.is_set():

            self.lores_event.wait()
            video_name = self.lores_queue.get()

            if video_name == "end_thread":
                continue
            
            print("lores", video_name)
            video_name = self.total_mon_path + video_name + "_lores"+".avi"

            video_out = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'MJPG'), float(self.current_fps), LORES_RES)
            
            while self.lores_event.is_set():
    
                low_res_frame = self.camera.capture_array(name="lores")

                low_res_frame = cv2.cvtColor(low_res_frame, cv2.COLOR_YUV420p2RGB)

                video_out.write(low_res_frame)

            video_out.release()

    def stop_snippet(self):
        self.lores_event.clear()

    def stop_recording(self):

        self.camera.stop_encoder()

    def init_stream(self, stream_quality=75, stream_resolution=(1920,1080)):
        
        #don't start if camera is already recording
        if self.record_state == False:

            output = StreamingOutput()
            encoder = JpegEncoder(q=stream_quality)
            self.record_stream(encoder=encoder, output=output)

            address = ('', 8000)
            #this stream handler hack is needed because "output" should be defined inside the do_GET method
            stream_handler = StreamingHandler
            stream_handler.define_output(stream_handler, output)

            self.server = StreamingServer(address, stream_handler)

            self.thread = Thread(None, self.server.run)
            self.thread.start()        
            self.stream_state = True

            print("Video stream is online!")

    def close_stream(self):
        
        self.server.shutdown()
        self.stop_recording()

        self.thread.join()

        self.set_cam_param(temp_change=False, quality=self.main_quality)
        
        self.stream_state = False

        print("Stream offline.")
    
    def get_cam_params(self):
        
        print("\n\n-----//-----PARAMS CORRESPONDING TO VIDEO CONFIGURATION-----//-----\n\n",self.cam_config)
        #caputure_metadata should only got if camera is recording
        #print("\n\n-----//-----PARAMS CORRESPONDING TO CAMERA CONTROLS-----//-----\n\n",self.camera.capture_metadata())
        
        return self.cam_config #self.camera.capture_metadata()

    def set_cam_param(self, temp_change=True, fps=None, resolution=(-1,-1), 
                        hflip = -1, exposure_time = -1, quality=-1, agc=-1, gain=-1, awb=-1):
        if fps != None:
            if fps == 1:
                if self.current_fps < 30:

                    self.current_fps += 1
                    picam_fps = int((1/self.current_fps)*1e6)
                    if temp_change == False:
                        self.cam_config["controls"]["FrameDurationLimits"] = (picam_fps,picam_fps)

                    self.camera.set_controls({"FrameDurationLimits": (picam_fps,picam_fps)})

            elif fps == -1:
                if self.current_fps > 1:

                    self.current_fps -= 1

                    picam_fps = int((1/self.current_fps)*1e6)
                    if temp_change == False:
                        self.cam_config["controls"]["FrameDurationLimits"] = (picam_fps,picam_fps)

                    self.camera.set_controls({"FrameDurationLimits": (picam_fps,picam_fps)})

        if resolution[0] != -1:
            
            if temp_change == False:
                self.main_resolution = resolution
                
            self.cam_config["main"]["size"] = resolution
            if self.camera.started:
                self.camera.stop()
                self.camera.configure(self.cam_config)
                self.camera.start()
            else:
                self.camera.configure(self.cam_config)

        if hflip != -1:
            if hflip == True: 

                self.cam_config["transform"] = Transform(hflip=True) 
                if self.camera.started:
                    self.camera.stop()
                    self.camera.configure(self.cam_config)
                    self.camera.start()
                else:
                    self.camera.configure(self.cam_config)
            else:

                self.cam_config["transform"] = Transform()
                if self.camera.started:
                    self.camera.stop()
                    self.camera.configure(self.cam_config)
                    self.camera.start()
                else:
                    self.camera.configure(self.cam_config)

        if exposure_time != None:

            if exposure_time == 1:
                if self.current_exp < 10:
                    
                    self.current_exp += 1

                    max_value = int((1/self.current_fps)*1e6)

                    exp_values = linspace(10000, max_value, num=11, dtype=int)

                    if temp_change == False:
                        self.cam_config["controls"]["ExposureTime"] = exp_values[self.current_exp]

                    self.camera.set_controls({"ExposureTime": exp_values[self.current_exp]})

            elif exposure_time == -1:
                if self.current_exp > 0:

                    self.current_exp -= 1

                    max_value = int((1/self.current_fps)*1e6)

                    exp_values = linspace(10000, max_value, num=11, dtype=int)

                    if temp_change == False:
                        self.cam_config["controls"]["ExposureTime"] = exp_values[self.current_exp]

                    self.camera.set_controls({"ExposureTime": exp_values[self.current_exp]})

        if quality != -1:
            if temp_change == False:
                self.main_quality = quality
            
            if self.encoder[1] == "jpeg":
  
                self.encoder[0] = JpegEncoder(q=quality)
            elif self.encoder[1] == "h264":

                self.encoder[0] = H264Encoder(quality=quality)
            
        if agc != -1:

            if agc == 0:
                self.cam_config["controls"]["AeEnable"] = False

                self.camera.set_controls({"AeEnable": False})
            else:
                self.cam_config["controls"]["AeEnable"] = True

                self.camera.set_controls({"AeEnable": True})

        if gain != -1:

                self.cam_config["controls"]["AnalogueGain"] = gain

                self.camera.set_controls({"AnalogueGain": gain})

        if awb != -1:

                if awb == 1:

                    self.cam_config["controls"]["AwbEnable"] = True

                    self.camera.set_controls({"AwbEnable": True})
                else:
                    self.cam_config["controls"]["AwbEnable"] = False

                    self.camera.set_controls({"AwbEnable": False})

    
    def close_cam(self):

        self.camera.stop()

        #kill lores thread
        self.kill.set()
        self.lores_queue.put("end_thread")
        #self.lores_queue_win.put("end_thread")
        self.lores_event.set()

        #self.lores_event_win.set()
        #self.lores_thread.join()
        #self.lores_thread_win.join()
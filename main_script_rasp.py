import alumia_TCP
import time
import alumia_piCameraPhd

PATH_TO_WIN = "/mnt/share/"
PATH_TO_MONITOR = "/mnt/share_monitor/"

client = alumia_TCP.TCPClient(server_ip="193.168.1.3", server_port=12840, code="ras")
picam2 = alumia_piCameraPhd.PiCameraStream(root_win_folder=PATH_TO_WIN, root_mon_folder=PATH_TO_MONITOR, resolution=(1920,1080), quality=90, encoder_type='jpeg')

client.client_connect()

while True:
    if client.connected:
        data_in = client.client_recv()
        print(data_in)
        if data_in[2] == "win":
            if data_in[0] == "bperf":
                picam2.init_perf()
                client.client_send("bperf_"+str(picam2.current_main))
                print("Started perf.")

            elif data_in[0] == "eperf":
                picam2.end_perf()
                client.client_send("eperf_0")
                print("Ended perf.")

            elif data_in[0] == "rec":
                #record video
                picam2.record_snippet()
                client.client_send("rec_"+str(picam2.current_main) + "&" + str(picam2.current_snippet))

            elif data_in[0] == "str":
                if picam2.stream_state == False:
                    print("Starting stream...")
                    picam2.init_stream()
                    client.client_send("str_1")
                else:
                    print("Stopping stream...")
                    client.client_send("str_0")
                    time.sleep(2)
                    picam2.close_stream()
            
            elif data_in[0] == "end":

                picam2.close_cam()
                client.client_close()
                print("RAS END SIGNAL")
                exit()

            elif data_in[0] == "stop":
                picam2.stop_snippet()
                client.client_send("stop_0")

            elif data_in[0] == "fld":
                params = data_in[1].split("&")
                picam2.change_work_folder(params[0], params[1])
                client.client_send("fld_"+data_in[1]+"&"+str(picam2.current_main)+"&"+str(picam2.current_snippet))
                print("main: ", picam2.current_main, "snippet: ", picam2.current_snippet)
                
            elif data_in[0] == "fps":
                if data_in[1] != "0":
                    picam2.set_cam_param(fps=int(data_in[1]))
                client.client_send("fps_"+str(picam2.current_fps))
                print("Changed framerate.")
                
            elif data_in[0] == "exp":
                if data_in[1] != "0":   
                    picam2.set_cam_param(exposure_time=int(data_in[1]))
                client.client_send("exp_"+str(picam2.current_exp))
                print("Changed exposure.")

            elif data_in[0] == "agc":
                picam2.set_cam_param(agc=int(data_in[1]))
                print("Changed AGC state.")
            
            elif data_in[0] == "isogain":
                picam2.set_cam_param(gain=float(data_in[1]))
                print("Changed analog gain.")

            elif data_in[0] == "awb":
                picam2.set_cam_param(awb=float(data_in[1]))
                print("Changed awb.")
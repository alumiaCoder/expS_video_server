> ### Developed with and for PhD candidate [Fil Botelho@Orpheus Institute](https://orpheusinstituut.be/en/orpheus-research-centre/researchers/filipa-botelho)
> This is part of the experimental_system (**expS**) repositories that are present on this github account.

# 📹video_server
`Python` code for a `Raspberry Pi` `http` `mjpeg` video server.

### Main characteristics:
> 1. `TCP` based communication with multiple clients.
> 2. Real time video manipulation (fps, exposure time, iso, etc).
> 3. Simultaneous high-res and low-res capture.
> 4. Simultaneous capture and manipulation.
> 5. Infrared capture. 

# 💻Requirements
## Hardware
- This was running on a overclocked (cpu and gpu) [8GB Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
- We used the [Raspberry Pi HQ Camera](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/) with the infrared filter removed.
- The server was communicating to a local windows machine via TCP. Three machines in total communicated via a network switch.
- 1 GigE was enough across all machines.
   
## Software
- `cifs-utils` and `samba client` for shared folder system
- `opencv-python`
- [picamera2](https://github.com/raspberrypi/picamera2)
  
# 🖱️ Use
As mentioned, this server is part of a bigger (multi-system) project (all repositories belonging to this project have `expS` as a prefix). It constitutes the video server that allows the user
to (from a menu controlled with a glove) record, play and manipulate real time video.

The user can:
> 1. Turn on/off a real time video stream that is accessible via `http` on any local network machine.
> 2. Manipulate that video's characteristics (fps, exposure time, iso) in real time.
> 3. Start/stop video capture (to storage) at will.
> 4. The captured video can be accessed while recording to disk, for almost zero delay video editing.
> 5. The captured video can be recorded on any shared folder of any machine on the local network. 

# ☮️Keep in mind
- I am sharing this here because some concepts might interest some people. **The code is not made to run first time**. All the system needs to be setup,
with all the credentials and the right hardware.
- If you want to use the code, or explore some idea, it is better if you contact me at: alumiamusic@gmail.com

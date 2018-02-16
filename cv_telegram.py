
from picamera.array import PiRGBArray
from picamera import PiCamera
import datetime
import time
import imutils
import json
import cv2

#import telepot

import telegram


conf =  json.load(open('conf.json'))

camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

print("warming up")
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = time.time()
motionCounter = 0

#bot1=telepot.Bot(conf["token"])
bot = telegram.Bot(token=conf["token"])

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = f.array
    timestamp = time.time()
    text = "Unoccupied"

    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    rawCapture.truncate(0)

    if avg is None:
        print ("Starting bg model")
        avg = gray.copy().astype("float")
        rawCapture.truncate(0)
        continue
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    
    for c in cnts:
         if cv2.contourArea(c) < conf["min_area"]:
             continue

         (x,y,w,h) = cv2.boundingRect(c)
         cv2.rectangle(frame, (x,y), (x+w, y+h),(0,0,255),2)
         text = "Occupied"


    if text=="Occupied":
        print text,time.ctime()
        if int(timestamp-lastUploaded) >= conf["min_upload_seconds"]:
            motionCounter+=1

            if motionCounter >= conf["min_motion_frames"]:
                filename= str(int(timestamp))
                filepath=filename+".jpg"
                time_msg = "Occupied "+time.ctime(timestamp)
                #bot1.sendMessage(conf["yadu_id"],time_msg)
                bot.send_message(chat_id=conf["telegram_id"], text= time_msg)
                cv2.imwrite('tosend.jpg',frame)
                

                
                #sent_data =bot1.sendPhoto(conf["yadu_id"],open("tel.jpg",'rb'))
                sent_data=bot.send_photo(chat_id=conf["telegram_id"], photo=open('tosend.jpg', 'rb'))
                print "Sent"
                

                motionCounter=0

    else:
        motionCounter = 0
    
    if 1:
        cv2.imshow("Video stream", frame)
        k_i = cv2.waitKey(1) & 0xFF
        if k_i ==ord("q"):
            break

    
    k_i = cv2.waitKey(1) & 0xFF
    if k_i == ord("q"):
        camera.close()
        print "camera closed"
        break







from flask import Flask, render_template, request, Response, redirect
import numpy as np
import cv2
from ultralytics import YOLO
from flask_mail import Mail, Message
import threading

app = Flask(__name__)
#mail = Mail(app)

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'rajatjakhar.2002@gmail.com'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

video = cv2.VideoCapture('')
photo = ''
PERSON_THRESHOLD_MED = 6
PERSON_THRESHOLD_MAX = 12
WASTE_THRESHOLD_MED = 2
WASTE_THRESHOLD_MAX = 4
MODEL_FILE="static/models/yolov8l.pt"
COCO_FILE="static/models/coco.txt"
MODEL_PHOTO="static/models/best.pt"
COCO_FILE1="static/models/coco1.txt"
# MODEL_FILE="static/yolov8s.pt"
# COCO_FILE="static/coco.txt"
# MODEL_PHOTO="static/yolov8s.pt"
# COCO_FILE1="static/coco.txt"

@app.route('/')
def index():
    return render_template('index.html')

VIDEO_EXTENSIONS = ['mp4']
PHOTO_EXTENSIONS = ['png','jpeg','jpg']

def fextension(filename):
    return filename.rsplit('.', 1)[1].lower()

@app.route('/upload', methods=['POST'])
def upload():
    global video
    global photo
    if 'video' not in request.files:
        return 'No video file found'
    file = request.files['video']
    if file.filename == '':
        return 'No video selected'
    if file:
        exttype=fextension(file.filename)
        print(exttype)
        if exttype in VIDEO_EXTENSIONS:
            file.save('static/input/video/' + file.filename)
            print('video')
            video = cv2.VideoCapture('static/input/video/' + file.filename)
            return redirect('/video_feed_new')
        elif exttype in PHOTO_EXTENSIONS:
            file.save('static/input/photo/' + file.filename)
            print('photo')
            photo = 'static/input/photo/' + file.filename
            return redirect('/video_feed_newp')
    return 'Invalid video file'

@app.route('/upload12', methods=['POST'])
def upload12():
    global video
    global photo
    if 'video' not in request.files:
        return 'No video file found'
    file = request.files['video']
    if file.filename == '':
        return 'No video selected'
    if file:
        exttype=fextension(file.filename)
        print(exttype)
        if exttype in VIDEO_EXTENSIONS:
            file.save('static/input/gvideo/' + file.filename)
            print('video')
            video = cv2.VideoCapture('static/input/gvideo/' + file.filename)
            return redirect('/video_feed_clean')
        elif exttype in PHOTO_EXTENSIONS:
            file.save('static/input/gphoto/' + file.filename)
            print('photo')
            photo = 'static/input/gphoto/' + file.filename
            return redirect('/video_feed_cleanp')
    return 'Invalid video file'


# def sendmessage(res,sub,body):
#     with app.app_context():
#         msg = Message(
#                     sub,
#                     sender ='shivanwhy999@gmail.com',
#                     recipients = res
#                 )
#         msg.body = body
#         mail.send(msg)

def sendmessage_async(recipients, subject, body):
    def send_message():
        with app.app_context():
            msg = Message(
                subject,
                sender='rajatjakhar.2002@gmail.com',
                recipients=recipients
            )
            msg.body = body
            mail.send(msg)

    # Create a new thread to send the message asynchronously
    message_thread = threading.Thread(target=send_message)
    message_thread.start()

def gen_new(video):
    # opening the file in read mode
    my_file = open(COCO_FILE, "r")
    # reading the file
    data = my_file.read()
    # replacing end splitting the text | when newline ('\n') is seen.
    class_list = data.split("\n")
    my_file.close()

    # load a pretrained YOLOv8n model
    model = YOLO(MODEL_FILE, "v8")
    #messagesent=False
    frame_count=0
    frame_face=[0,0,0,0,0]
    while True:
        ret, frame = video.read()
        frame_count=frame_count+1
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        frame = cv2.resize(frame, (720, 480))

        detect_params = model.predict(source=[frame], conf=0.45, save=False)
        print(detect_params)
        DP = detect_params[0].numpy()
        #print(DP)
        no_faces=0
        if len(DP) != 0:
            for i in range(len(detect_params[0])):
                print(i)

                boxes = detect_params[0].boxes
                box = boxes[i]  # returns one box
                clsID = box.cls.numpy()[0]
                conf = box.conf.numpy()[0]
                bb = box.xyxy.numpy()[0]

                cv2.rectangle(frame,(int(bb[0]), int(bb[1])),(int(bb[2]), int(bb[3])),(255,255,255),3,)
                # Display class name and confidence
                font = cv2.FONT_HERSHEY_COMPLEX_SMALL
                cv2.putText(frame,class_list[int(clsID)],(int(bb[0]), int(bb[1]) - 10),font,0.5,(255, 255, 255),1,)
                if class_list[int(clsID)] == "person":
                    no_faces=no_faces+1

        status=""
        i=frame_count % 5
        frame_face[i]=no_faces
        green_count=0
        yellow_count=0
        red_count=0
        sum=0
        for j in range(0,5):
            sum=sum+frame_face[j]
            if frame_face[j] < PERSON_THRESHOLD_MED:
                green_count=green_count+1
            elif frame_face[j] < PERSON_THRESHOLD_MAX:
                yellow_count=yellow_count+1
            else:
                red_count=red_count+1

        if red_count==5:
            status = "Red"
            clor = (0, 0, 255)
            #if not messagesent:
                #messagesent=True
            sendmessage_async(['01fe21bcs241@kletech.ac.in'],'High Crowd Detected in Station',str(no_faces)+' persons detected in station. Please take necessary action')
            cv2.putText(frame, "High Alert Message Sent!!", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        elif green_count==5:
            status = "Green"
            clor = (0, 255, 0)
        elif yellow_count==5:
            status = "Yellow"
            clor = (0, 255, 255)
        else:
            s=sum/5
            if s < PERSON_THRESHOLD_MED:
                status = "Green"
                clor = (0, 255, 0)
            else:
                status = "Yellow"
                clor = (0, 255, 255)

        cv2.putText(frame, "Persons: " + str(no_faces), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        cv2.putText(frame, "Status: ", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        cv2.putText(frame, status, (175, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, clor, 3)

        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed_new')
def video_feed_new():
    global video
    if not (video.isOpened()):
        return 'Could not process video'
    return Response(gen_new(video),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_feed')
def camera_feed():
    global video
    video = cv2.VideoCapture(0)
    if not (video.isOpened()):
        return 'Could not connect to camera'
    return Response(gen_new(video),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_new1(video):
    # opening the file in read mode
    my_file = open(COCO_FILE1, "r")
    # reading the file
    data = my_file.read()
    # replacing end splitting the text | when newline ('\n') is seen.
    class_list = data.split("\n")
    my_file.close()

    # load a pretrained YOLOv8n model
    model = YOLO(MODEL_PHOTO, "v8") 
    #messagesent=False
    frame_count=0
    frame_face=[0,0,0,0,0]
    while True:
        ret, frame = video.read()
        frame_count=frame_count+1
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        frame = cv2.resize(frame, (720, 480))

        detect_params = model.predict(source=[frame], conf=0.45, save=False)
        print(detect_params)
        DP = detect_params[0].numpy()
        #print(DP)
        no_waste=0
        if len(DP) != 0:
            for i in range(len(detect_params[0])):
                print(i)

                boxes = detect_params[0].boxes
                box = boxes[i]  # returns one box
                clsID = box.cls.numpy()[0]
                conf = box.conf.numpy()[0]
                bb = box.xyxy.numpy()[0]

                cv2.rectangle(frame,(int(bb[0]), int(bb[1])),(int(bb[2]), int(bb[3])),(255,255,255),3,)
                # Display class name and confidence
                font = cv2.FONT_HERSHEY_COMPLEX_SMALL
                cv2.putText(frame,class_list[int(clsID)],(int(bb[0]), int(bb[1]) - 10),font,0.5,(255, 255, 255),1,)
                if class_list[int(clsID)] == "garbage":
                    no_waste=no_waste+1

        status=""
        i=frame_count % 5
        frame_face[i]=no_waste
        green_count=0
        yellow_count=0
        red_count=0
        sum=0
        for j in range(0,5):
            sum=sum+frame_face[j]
            if frame_face[j] == 0:
                green_count=green_count+1
            
            else:
                red_count=red_count+1

        if red_count==5:
            status = "Red"
            clor = (0, 0, 255)
            #if not messagesent:
                #messagesent=True
            sendmessage_async(['01fe21bcs241@kletech.ac.in'],'Uncleanliness Detected in Station',str(no_waste)+' trash detected in station. Please clean the area.')
            cv2.putText(frame, "High Alert Message Sent!!", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        elif green_count==5:
            status = "Green"
            clor = (0, 255, 0)
        elif yellow_count==5:
            status = "Yellow"
            clor = (0, 255, 255)
        else:
            s=sum/5
            if s < WASTE_THRESHOLD_MED:
                status = "Green"
                clor = (0, 255, 0)
            else:
                status = "Yellow"
                clor = (0, 255, 255)

        cv2.putText(frame, "Garbage: " + str(no_waste), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        cv2.putText(frame, "Status: ", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        cv2.putText(frame, status, (175, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, clor, 3)

        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed_clean')
def video_feed_clean():
    global video
    if not (video.isOpened()):
        return 'Could not process video'
    return Response(gen_new1(video),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_feed12')
def camera_feed12():
    global video
    video = cv2.VideoCapture(0)
    if not (video.isOpened()):
        return 'Could not connect to camera'
    return Response(gen_new1(video),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_new2(photo):
    my_file = open(COCO_FILE1, "r")
    # reading the file
    data = my_file.read()
    # replacing end splitting the text | when newline ('\n') is seen.
    class_list = data.split("\n")
    my_file.close()

    # load a pretrained YOLOv8n model
    model = YOLO(MODEL_PHOTO, "v8") 
    print(photo)
    frame = cv2.imread(photo)
    frame=cv2.resize(frame, (720, 480))
    detect_params = model.predict(source=[frame], conf=0.45, save=False)
    print(detect_params)
    DP = detect_params[0].numpy()
    #print(DP)
    no_waste=0
    if len(DP) != 0:
        for i in range(len(detect_params[0])):
            print(i)

            boxes = detect_params[0].boxes
            box = boxes[i]  # returns one box
            clsID = box.cls.numpy()[0]
            conf = box.conf.numpy()[0]
            bb = box.xyxy.numpy()[0]

            cv2.rectangle(frame,(int(bb[0]), int(bb[1])),(int(bb[2]), int(bb[3])),(255,255,255),3,)
            # Display class name and confidence
            font = cv2.FONT_HERSHEY_COMPLEX_SMALL
            cv2.putText(frame,class_list[int(clsID)],(int(bb[0]), int(bb[1]) - 10),font,0.5,(255, 255, 255),1,)
            if class_list[int(clsID)] == "garbage":
                no_waste=no_waste+1
    
    status=""
    frame_face=no_waste
    status = "Red"
    clor = (0, 0, 255)
    #if not messagesent:
        #messagesent=True
    sendmessage_async(['01fe21bcs241@kletech.ac.in'],'Uncleanliness Detected in Station',str(no_waste)+' trash detected in station. Please clean the area.')
    cv2.putText(frame, "High Alert Message Sent!!", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    
    cv2.putText(frame, "Garbage: " + str(no_waste), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    cv2.putText(frame, "Status: ", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    cv2.putText(frame, status, (175, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, clor, 3)
    cv2.imwrite('static/input/photo/dskjds.jpg', frame) 
    
@app.route('/video_feed_cleanp')
def video_feed_cleanp():
    global photo
    gen_new2(photo)
    return render_template('preview_photo.html', file_name='dskjds.jpg', type='image/jpg')



def gen_new3(photo):
    my_file = open(COCO_FILE, "r")
    # reading the file
    data = my_file.read()
    # replacing end splitting the text | when newline ('\n') is seen.
    class_list = data.split("\n")
    my_file.close()

    # load a pretrained YOLOv8n model
    model = YOLO(MODEL_FILE, "v8") 
    print(photo)
    frame = cv2.imread(photo)
    frame=cv2.resize(frame, (720, 480))
    detect_params = model.predict(source=[frame], conf=0.45, save=False)
    print(detect_params)
    DP = detect_params[0].numpy()
    #print(DP)
    no_waste=0
    if len(DP) != 0:
        for i in range(len(detect_params[0])):
            print(i)

            boxes = detect_params[0].boxes
            box = boxes[i]  # returns one box
            clsID = box.cls.numpy()[0]
            conf = box.conf.numpy()[0]
            bb = box.xyxy.numpy()[0]

            cv2.rectangle(frame,(int(bb[0]), int(bb[1])),(int(bb[2]), int(bb[3])),(255,255,255),3,)
            # Display class name and confidence
            font = cv2.FONT_HERSHEY_COMPLEX_SMALL
            cv2.putText(frame,class_list[int(clsID)],(int(bb[0]), int(bb[1]) - 10),font,0.5,(255, 255, 255),1,)
            if class_list[int(clsID)] == "person":
                no_waste=no_waste+1
    
    status=""
    frame_face=no_waste
    green_count=0
    yellow_count=0
    red_count=0
    if frame_face< PERSON_THRESHOLD_MED:
        green_count=frame_face
    elif frame_face < PERSON_THRESHOLD_MAX:
        yellow_count=frame_face
    else:
        red_count=frame_face

    if red_count==5:
        status = "Red"
        clor = (0, 0, 255)
        #if not messagesent:
            #messagesent=True
        sendmessage_async(['01fe21bcs241@kletech.ac.in'],'High Crowd Detected in Station',str(no_waste)+' persons detected in station. Please take necessary action.')
        cv2.putText(frame, "High Alert Message Sent!!", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    elif green_count==5:
        status = "Green"
        clor = (0, 255, 0)
    elif yellow_count==5:
        status = "Yellow"
        clor = (0, 255, 255)
    else:
        s=frame_face
        if s < PERSON_THRESHOLD_MED:
            status = "Green"
            clor = (0, 255, 0)
        else:
            status = "Yellow"
            clor = (0, 255, 255)
    cv2.putText(frame, "Garbage: " + str(no_waste), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    cv2.putText(frame, "Status: ", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
    cv2.putText(frame, status, (175, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, clor, 3)
    cv2.imwrite('static/input/photo/dskjds.jpg', frame) 
    
@app.route('/video_feed_newp')
def video_feed_newp():
    global photo
    gen_new3(photo)
    return render_template('preview_photo.html', file_name='dskjds.jpg', type='image/jpg')

if __name__ == '__main__':
    app.run(debug=True)
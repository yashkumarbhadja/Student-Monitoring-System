from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate
from PyQt5.QtWidgets import QDialog
import cv2
import face_recognition
import numpy as np
import datetime
import os
import smtplib
from email.message import EmailMessage

class Ui_OutputDialog(QDialog):
    def __init__(self):
        super(Ui_OutputDialog, self).__init__()
        loadUi("./outputwindow.ui", self)    #load the ui file for gui
        #update time and date
        now = QDate.currentDate()
        current_date = now.toString('ddd dd MMMM yyyy')
        current_time = datetime.datetime.now().strftime("%I:%M %p")

        self.Date_Lable.setText(current_date)
        self.Time_Lable.setText(current_time)

    @pyqtSlot()
    def startVideo(self, camera_name):
        """
        camera_name: link of camera or usb camera
        """
        if len(camera_name) == 1:
        	self.capture = cv2.VideoCapture(int(camera_name)) #for video capture from webcam
        else:
        	self.capture = cv2.VideoCapture(int(camera_name))
        self.timer = QTimer(self)  # Create Timer
        path = 'ImagesAttendance'
        if not os.path.exists(path):
            os.mkdir(path)
        # known face encoding and known face name list
        images = []
        self.class_names = []
        self.encode_list = []
        attendance_list = os.listdir(path)
        #print(attendance_list)
        for cl in attendance_list:
            cur_img = cv2.imread(f'{path}/{cl}')
            images.append(cur_img)
            self.class_names.append(os.path.splitext(cl)[0])
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(img)
            encodes_cur_frame = face_recognition.face_encodings(img, boxes)[0]

            self.encode_list.append(encodes_cur_frame)
        self.timer.timeout.connect(self.update_frame)  # Connect timeout to the output function
        self.timer.start(10)  # emit the timeout() signal at x=40ms

    def face_rec_(self, frame, encode_list_known, class_names):
        """
         frame: frame from camera
         encode_list_known: known face encoding
         class_names: known face names
        """
        # csv
        def mark_attendance(name):
            """
             name: detected face known or unknown one
            """
            with open('Attendance.csv', 'r+') as f:
                mydatalist = f.readlines()
                namelist = []

                for line in mydatalist:
                    entry = line.split(',')
                    namelist.append(entry[0])
                if name not in namelist:
                    #now = datetime.now()
                    date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")

                    if (name != 'unknown'):
                        self.NameLable.setText(name)
                        self.StatusLable.setText('Present')
                        f.writelines(f'\n{name},{date_time_string},Present')
                        #self.mail()
                    else:
                        self.NameLable.setText(name)
                        self.StatusLable.setText('Not Registered')
                        f.writelines(f'\n{name},{date_time_string},Not Registered')

        # face recognition
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)

        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.50)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            best_match_index = np.argmin(face_dis)

            if match[best_match_index]:
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            mark_attendance(name)

        return frame

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        """
         image: frame from camera
         encode_list: known face encoding list
         class_names: known face names
         window: number of window

        """
        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)

    '''def mail(self):
        EMAIL_ADDRESS = '#'
        EMAIL_PASSWORD = '#'

        #contacts = ['mrhijokar@gmail.com', 'yashbhadja31@gmail.com']

        msg = EmailMessage()
        msg['Subject'] = 'Student Attendance'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = 'yashbhadja31@gmail.com'

        msg.set_content('Your ward is present today')


        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)'''

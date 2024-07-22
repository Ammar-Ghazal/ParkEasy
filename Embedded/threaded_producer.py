import threading
import os
import time
import cv2
from picamera2 import Picamera2
import pika
import base64
import numpy as np
import image_comparison as ic

def send_to_rabbitmq(image, routing_key):
    credentials = pika.PlainCredentials('FYDP', 'fydp')
    parameters = pika.ConnectionParameters('192.168.118.168', 5672, 'FYDPhost', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=routing_key)

    # Convert the image to bytes and then to a base64 string
    _, buffer = cv2.imencode('.jpg', image)
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    channel.basic_publish(exchange='', routing_key=routing_key, body=image_base64)
    connection.close()

def capture_usb1_camera():
    cap = cv2.VideoCapture(0)  # 0 for first USB camera
    previous_image_path = "/home/fydp/parkeasy/Embedded/previous1.jpg"
    current_image_path = None
    previous_image_exists = False
    while(1):
        ret, frame = cap.read()
        if ret:
            cv2.imwrite('/home/fydp/parkeasy/Embedded/current1.jpg', frame)
            print("writting current image")
            if current_image_path is None:
                current_image_path = "/home/fydp/parkeasy/Embedded/current1.jpg"
                continue
            if previous_image_exists:
                is_same_result = ic.is_same(previous_image_path, current_image_path)
                print("running comparison, result = ")
                print(is_same_result)
            else:
                is_same_result = 0
            if is_same_result == 0:
                print("sending image to rabbitmq")
                send_to_rabbitmq(frame, 'usb1_image_queue')
                if previous_image_exists:
                    os.remove(previous_image_path)
                    print("deleting previous image")
                os.rename(current_image_path, previous_image_path)
                print("renaming current image to previous image")
                previous_image_exists = True
            else:
                os.remove(current_image_path)
                print("deleting current image")
        #time.sleep(0.5)

def capture_usb2_camera():
    cap = cv2.VideoCapture(2)  # 0 for first USB camera
    previous_image_path = "/home/fydp/parkeasy/Embedded/previous2.jpg"
    current_image_path = None
    previous_image_exists = False
    while(1):
        ret, frame = cap.read()
        if ret:
            cv2.imwrite('/home/fydp/parkeasy/Embedded/current2.jpg', frame)
            print("writting current image")
            if current_image_path is None:
                current_image_path = "/home/fydp/parkeasy/Embedded/current2.jpg"
                continue
            if previous_image_exists:
                is_same_result = ic.is_same(previous_image_path, current_image_path)
                print("running comparison, result = ")
                print(is_same_result)
            else:
                is_same_result = 0
            if is_same_result == 0:
                print("sending image to rabbitmq")
                send_to_rabbitmq(frame, 'usb2_image_queue')
                if previous_image_exists:
                    os.remove(previous_image_path)
                    print("deleting previous image")
                os.rename(current_image_path, previous_image_path)
                print("renaming current image to previous image")
                previous_image_exists = True
            else:
                os.remove(current_image_path)
                print("deleting current image")
        #time.sleep(0.5)

def capture_csi2_camera():
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    for x in range(10):
        frame = picam2.capture_array()
        print("frame captured from CSI2 cam")
        send_to_rabbitmq(frame, 'csi2_image_queue')
        time.sleep(2)

if __name__ == '__main__':
    """
    image1_path = r'/home/fydp/parkeasy/Embedded/image1.jpg'
    image2_path = r'/home/fydp/parkeasy/Embedded/image1.jpg'
    if(ic.is_same(image1_path, image2_path)):
        print("same")
    else:
        print("different")
    """
    usb1_thread = threading.Thread(target=capture_usb1_camera)
    usb2_thread = threading.Thread(target=capture_usb2_camera)
    #csi2_thread = threading.Thread(target=capture_csi2_camera)

    usb1_thread.start()
    usb2_thread.start()
    #csi2_thread.start()

    usb1_thread.join()
    usb2_thread.join()
    os.remove("/home/fydp/parkeasy/Embedded/previous1.jpg")
    os.remove("/home/fydp/parkeasy/Embedded/previous2.jpg")
    #csi2_thread.join()


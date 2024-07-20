import threading
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

def capture_usb_camera():
    cap = cv2.VideoCapture(0)  # 0 for first USB camera
    for x in range(10):
        ret, frame = cap.read()
        if ret:
            print("frame captured from usb cam")
            send_to_rabbitmq(frame, 'usb_image_queue')
        time.sleep(2)

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
    image1_path = r'/home/fydp/parkeasy/Embedded/image1.jpg'
    image2_path = r'/home/fydp/parkeasy/Embedded/image1.jpg'
    if(ic.is_same(image1_path, image2_path)):
        print("same")
    else:
        print("different")
    #usb_thread = threading.Thread(target=capture_usb_camera)
    #csi2_thread = threading.Thread(target=capture_csi2_camera)

    #usb_thread.start()
    #csi2_thread.start()

    #usb_thread.join()
    #csi2_thread.join()


import threading
import time
import cv2
from picamera2 import Picamera2
import pika
import base64
import numpy as np

def send_to_rabbitmq(image, routing_key):
    credentials = pika.PlainCredentials('FYDP', 'fydp')
    parameters = pika.ConnectionParameters('192.168.118.168', 5672, 'FYDPhost', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='image_queue')

    # Convert the image to bytes and then to a base64 string
    _, buffer = cv2.imencode('.jpg', image)
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    channel.basic_publish(exchange='', routing_key='image_queue', body=image_base64)
    connection.close()

def capture_usb_camera():
    cap = cv2.VideoCapture(0)  # 0 for first USB camera
    for x in range(10):
        ret, frame = cap.read()
        if ret:
            print("frame captured from usb cam")
            send_to_rabbitmq(frame, 'image_queue')
        time.sleep(2)

def capture_csi2_camera():
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    for x in range(10):
        frame = picam2.capture_array()
        print("frame captured from CSI2 cam")
        send_to_rabbitmq(frame, 'image_queue')
        time.sleep(2)

if __name__ == '__main__':
    usb_thread = threading.Thread(target=capture_usb_camera)
    csi2_thread = threading.Thread(target=capture_csi2_camera)

    usb_thread.start()
    csi2_thread.start()

    usb_thread.join()
    csi2_thread.join()


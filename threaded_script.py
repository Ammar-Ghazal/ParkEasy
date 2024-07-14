import threading
import time
import cv2
from picamera2 import Picamera2
import pika

def send_to_rabbitmq(image, routing_key):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='your_rabbitmq_server_ip'))
    channel = connection.channel()
    channel.queue_declare(queue=routing_key)
    channel.basic_publish(exchange='', routing_key=routing_key, body=image.tobytes())
    connection.close()

def capture_usb_camera():
    cap = cv2.VideoCapture(0)  # 0 for first USB camera
    while True:
        ret, frame = cap.read()
        if ret:
            send_to_rabbitmq(frame, 'usb_camera')
        time.sleep(0.1)

def capture_csi2_camera():
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    while True:
        frame = picam2.capture_array()
        send_to_rabbitmq(frame, 'csi2_camera')
        time.sleep(0.1)

if __name__ == '__main__':
    usb_thread = threading.Thread(target=capture_usb_camera)
    csi2_thread = threading.Thread(target=capture_csi2_camera)

    usb_thread.start()
    csi2_thread.start()

    usb_thread.join()
    csi2_thread.join()


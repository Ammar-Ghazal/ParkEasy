import subprocess
import pika
import base64
import cv2
import numpy as np
import time
import threading
import sys
import shutil

def process_image(body, camera_type):
    # Decode the base64 image data
    image_data = base64.b64decode(body)
    
    # Convert the image data to a numpy array
    np_arr = np.frombuffer(image_data, np.uint8)
    
    # Decode the numpy array to an image
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # Create a unique filename based on the camera type and timestamp
    if (camera_type == 'USB1'):
        filename = f'parkingLot1.jpg'
    elif (camera_type == 'USB2'):
        filename = f'parkingLot2.jpg'
    else: 
        filename = f'received_image_{camera_type}_{int(time.time())}.jpg'
    
    # Save the image to a file
    cv2.imwrite(filename, img)
    print(f" [x] Received and saved {camera_type} camera image as {filename}")

def callback_csi2(ch, method, properties, body):
    process_image(body, 'CSI2')
def callback_usb1(ch, method, properties, body):
    process_image(body, 'USB1')
    #shutil.move('/home/hussain/Documents/S24/FYDP/parkeasy/Embedded/parkingLot1.jpg','/home/hussain/Documents/S24/FYDP/parkeasy/webapp/webapp/public/parkingLot1.jpg')
    shutil.move('/home/hussain/Documents/S24/FYDP/parkeasy/Embedded/parkingLot1.jpg','/home/hussain/Documents/S24/FYDP/parkeasy/parkinglotlayout/parkinglotimages/single_image_folder/parkingLot1.jpg')
    subprocess.run(['python3', '../parkinglotlayout/server_script.py'])

def callback_usb2(ch, method, properties, body):
    process_image(body, 'USB2')
    shutil.move('/home/hussain/Documents/S24/FYDP/parkeasy/Embedded/parkingLot2.jpg','/home/hussain/Documents/S24/FYDP/parkeasy/webapp/webapp/public/parkingLot2.jpg')

def start_consuming(queue_name, callback):
    # Set up RabbitMQ connection
    credentials = pika.PlainCredentials('FYDP', 'fydp')
    parameters = pika.ConnectionParameters(ip_address, 5672, 'FYDPhost', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    
    print(f' [*] Waiting for messages in {queue_name}. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    # Collect IP Address
    if len(sys.argv) != 2:
        print("Usage: python3 consumer.py <ip_address>")
        sys.exit(1)

    ip_address = sys.argv[1]
    # Start two threads to consume from both queues
    #thread_csi2 = threading.Thread(target=start_consuming, args=('csi2_image_queue', callback_csi2))
    thread_usb1 = threading.Thread(target=start_consuming, args=('usb1_image_queue', callback_usb1))
    thread_usb2 = threading.Thread(target=start_consuming, args=('usb2_image_queue', callback_usb2))

    #thread_csi2.start()
    thread_usb1.start()
    thread_usb2.start()

    #thread_csi2.join()
    thread_usb1.join()
    thread_usb2.join()


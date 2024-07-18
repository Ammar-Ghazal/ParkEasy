import pika
import base64
import cv2
import numpy as np
import time
import threading
import sys

def process_image(body, camera_type):
    # Decode the base64 image data
    image_data = base64.b64decode(body)
    
    # Convert the image data to a numpy array
    np_arr = np.frombuffer(image_data, np.uint8)
    
    # Decode the numpy array to an image
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # Create a unique filename based on the camera type and timestamp
    filename = f'received_image_{camera_type}_{int(time.time())}.jpg'
    
    # Save the image to a file
    cv2.imwrite(filename, img)
    print(f" [x] Received and saved {camera_type} camera image as {filename}")

def callback_csi2(ch, method, properties, body):
    process_image(body, 'CSI2')

def callback_usb(ch, method, properties, body):
    process_image(body, 'USB')

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
    thread_csi2 = threading.Thread(target=start_consuming, args=('csi2_image_queue', callback_csi2))
    thread_usb = threading.Thread(target=start_consuming, args=('usb_image_queue', callback_usb))

    thread_csi2.start()
    thread_usb.start()

    thread_csi2.join()
    thread_usb.join()


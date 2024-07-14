import pika
import base64
import cv2
import numpy as np
import time

def callback(ch, method, properties, body):
    # Decode the base64 image data
    image_data = base64.b64decode(body)
    
    # Convert the image data to a numpy array
    np_arr = np.frombuffer(image_data, np.uint8)
    
    # Decode the numpy array to an image
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # Create a unique filename based on the camera type and timestamp
    filename = f'received_image_{int(time.time())}.jpg'
    
    # Save the image to a file
    cv2.imwrite(filename, img)
    print(f" [x] Received and saved camera image as {filename}")

# Set up RabbitMQ connection
credentials = pika.PlainCredentials('FYDP', 'fydp')
parameters = pika.ConnectionParameters('192.168.118.168', 5672, 'FYDPhost', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.queue_declare(queue='image_queue')

channel.basic_consume(queue='image_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()


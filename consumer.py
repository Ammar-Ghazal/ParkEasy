import pika
import cv2
import numpy as np
import base64

def callback(ch, method, properties, body):
    # Decode the base64 string back to image
    image_data = base64.b64decode(body)
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # Display the frame
    cv2.imshow('Received Image', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return

def receive_images():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='image_queue')
    channel.basic_consume(queue='image_queue', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for images. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    receive_images()


import cv2
import pika
import base64
from picamera2 import Picamera2, Preview

def capture_and_send():
    
    # Initialize CSI2 Camera
    picam2 = Picamera2()
    camera_config = picam2.create_preview_configuration()
    picam2.configure(camera_config)
    picam2.start()

    # Initialize the camera
    camera = cv2.VideoCapture(0)
    
    # Set up RabbitMQ connection
    credentials = pika.PlainCredentials('FYDP', 'fydp')
    parameters = pika.ConnectionParameters('192.168.27.168', 5672, 'FYDPhost', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='image_queue')

    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        ret_CS12, frame_CSI2 = picam2.capture_array()
        if not ret_CSI2:
            break
        frame_CSI2 = cv2.cvtColor(frame_CSI2, cv2.COLOR_RGB2BGR)
        
        # Encode frame as a JPEG image
        _, buffer = cv2.imencode('.jpg', frame)
        image_as_text = base64.b64encode(buffer)
        
        # Encode frame_CSI2 as a JPEG image
        _, buffer = cv2.imencode('.jpg', frame_CSI2)
        image_as_text = base64.b64encode(buffer)
        
        # Send the images to the queue
        channel.basic_publish(exchange='',
                              routing_key='image_queue',
                              body=image_as_text)
        print(" [x] Sent image")

    camera.release()
    picam2.close()
    connection.close()

if __name__ == "__main__":
    capture_and_send()


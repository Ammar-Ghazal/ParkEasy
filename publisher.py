import cv2
import pika
import base64

def capture_and_send():
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
        
        # Encode the frame as a JPEG image
        _, buffer = cv2.imencode('.jpg', frame)
        image_as_text = base64.b64encode(buffer)
        
        # Send the image to the queue
        channel.basic_publish(exchange='',
                              routing_key='image_queue',
                              body=image_as_text)
        print(" [x] Sent image")

    camera.release()
    connection.close()

if __name__ == "__main__":
    capture_and_send()


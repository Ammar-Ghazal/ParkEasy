import os
from roboflow import Roboflow
from inference_sdk import InferenceHTTPClient
from inference_sdk.http.client import InferenceHTTPClient
import base64
import numpy as np
import cv2
import json

# using a parking lot MV model on roboflow:
# https://universe.roboflow.com/tasarimproject/car-space-find/model/2
# API Key is: hZHL7nrK0z63BmXWx6dI

def draw_rectangle(graphic, x, y, width, height, color):
    height = int(height/2)
    cv2.rectangle(graphic, (x-width, y-height), (x, y+height), color, thickness=2)

def scan_parking_lot(image_path):
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="hZHL7nrK0z63BmXWx6dI"
    )

    # image_path = "./parkinglotimages/parkinglot8.jpg"
    result = CLIENT.infer(image_path, model_id="parking-detection-jeremykevin/8")

    print(image_path)
    free_spots = 0
    occupied_spots = 0

    # Iterate over each prediction
    for prediction in result['predictions']:
        # Check if the class is 'free' and increment the counter
        if prediction['class'] == 'free':
            free_spots += 1
        elif prediction['class'] == 'car':
            occupied_spots += 1

    print("Total spots: ", free_spots + occupied_spots)
    print("Free spots: ", free_spots)
    print("Occupied spots: ", occupied_spots)
    print("\n")
    print("Result: \n", result)
    print("Type: ", type(result))

    with open("RoboFlowOutput.json", 'w') as f:
        json.dump(result, f, indent=4)

    # Now create the graphic for the parking lot:
    image_width = result["image"]["width"]
    image_height = result["image"]["height"]
    # image_width = 612
    # image_height = 433

    # Create a blank image
    parking_lot_graphic = np.zeros((image_height, image_width, 3), dtype=np.uint8)

    # Draw bounding boxes on the blank image
    for prediction in result['predictions']:
        x = int(prediction["x"])
        y = int(prediction["y"])
        width = int(prediction["width"])
        height = int(prediction["height"])

        color = (0, 0, 255) if prediction["class"] == "car" else (0, 255, 0) if prediction["class"] == "free" else (0, 255, 255)
    
        draw_rectangle(parking_lot_graphic, x, y, width, height, color)

    # Display the image
    cv2.namedWindow('Output Graphic', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Output Graphic', image_width, image_height)
    cv2.imshow('Output Graphic', parking_lot_graphic)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Save the image
    # cv2.imwrite('outputgraphic.jpg', parking_lot_graphic)

if __name__ == "__main__":
    parking_lot_images = './parkinglotimages'  # Replace with your input folder path
    
    images = os.listdir(parking_lot_images)
    for image in images:
        if image.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            image_path = os.path.join(parking_lot_images, image)
            scan_parking_lot(image_path)
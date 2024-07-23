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

def cleanup(result):
    # Clean up results:
    margin = 0.4
    num_parking_lots = len(result["predictions"])
    first_item = True
    working_set = []
    for i in range(num_parking_lots-1):
        curr_prediction = result["predictions"][i]
        x_curr = int(curr_prediction["x"])
        y_curr = int(curr_prediction["y"])
        width_curr = int(curr_prediction["width"])
        height_curr = int(curr_prediction["height"])

        next_prediction = result["predictions"][i+1]
        x_next = int(next_prediction["x"])
        y_next = int(next_prediction["y"])
        width_next = int(next_prediction["width"])
        height_next = int(next_prediction["height"])
        
        if (first_item):
            working_set.append(i)
            first_item = False
        else:
            if ((1-margin) <= y_curr/y_next <= (1+margin)):
                # The y values are close enough, now check the x values:
                if ((1-margin) <= ((x_curr+width_curr)/x_next) <= (1+margin)):
                    # If the x values are also close, add current prediction:
                    working_set.append(i)
                    print("Appended to working set!")
                else:
                    format(result, working_set)
                    working_set.clear()
                    first_item = True
            else:
                working_set.clear()
                first_item = True

def format(result, working_set):
    length = len(working_set)
    average_width = 0
    average_height = 0

    for i in range(length):
        index = working_set[i]

        average_width += result["predictions"][index]["width"]
        average_height += result["predictions"][index]["height"]

    average_width = int(average_width/length)
    average_height = int(average_height/length)

    # Extract x and y values of first box:
    first_x = result["predictions"][working_set[0]]["x"]
    first_y = result["predictions"][working_set[0]]["y"]


    # Now reassign width, height, x and y values
    for i in range(length):
        index = working_set[i]
        result["predictions"][index]["width"] = average_width
        result["predictions"][index]["height"] = average_height

        result["predictions"][index]["x"] = int(first_x + i*average_width)
        result["predictions"][index]["y"] = int(first_y + i*average_height)

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

    cleanup(result)

    # Draw bounding boxes on the blank image
    for prediction in result["predictions"]:
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
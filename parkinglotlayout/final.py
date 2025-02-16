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

def cleanup(result):
    """Align parking spot rectangles to create a cleaner parking lot layout."""
    if not result["predictions"]:
        return result
    
    # Convert predictions to rectangle format
    rectangles = [
        {
            'x1': pred["x"] - pred["width"]/2,
            'y1': pred["y"] - pred["height"]/2,
            'x2': pred["x"] + pred["width"]/2,
            'y2': pred["y"] + pred["height"]/2,
            'class': pred["class"],
            'confidence': pred["confidence"]
        }
        for pred in result["predictions"]
    ]
    
    # Create and use the rectangle aligner
    aligner = RectangleAligner(snap_threshold=10.0)  # Adjust threshold as needed
    aligned_rectangles = aligner.align_rectangles(rectangles)
    
    # Convert back to prediction format
    for i, rect in enumerate(aligned_rectangles):
        width = rect['x2'] - rect['x1']
        height = rect['y2'] - rect['y1']
        x = (rect['x1'] + rect['x2']) / 2
        y = (rect['y1'] + rect['y2']) / 2
        
        result["predictions"][i].update({
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height)
        })
    
    return result

class RectangleAligner:
    def __init__(self, snap_threshold: float = 5.0):
        self.snap_threshold = snap_threshold
        
    def get_rectangle_edges(self, rect: dict) -> tuple:
        return (rect['x1'], rect['x2'], rect['y1'], rect['y2'])
    
    def find_common_lines(self, rectangles: list) -> tuple:
        x_lines = []
        y_lines = []
        
        for rect in rectangles:
            left, right, top, bottom = self.get_rectangle_edges(rect)
            x_lines.extend([left, right])
            y_lines.extend([top, bottom])
        
        x_lines = self._cluster_lines(sorted(x_lines))
        y_lines = self._cluster_lines(sorted(y_lines))
        
        return x_lines, y_lines
    
    def _cluster_lines(self, lines: list) -> list:
        if not lines:
            return []
        
        clusters = []
        current_cluster = [lines[0]]
        
        for line in lines[1:]:
            if line - current_cluster[-1] <= self.snap_threshold:
                current_cluster.append(line)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [line]
        
        clusters.append(np.mean(current_cluster))
        return clusters
    
    def snap_rectangle(self, rect: dict, x_lines: list, y_lines: list) -> dict:
        left, right, top, bottom = self.get_rectangle_edges(rect)
        
        new_left = self._snap_to_nearest(left, x_lines)
        new_right = self._snap_to_nearest(right, x_lines)
        new_top = self._snap_to_nearest(top, y_lines)
        new_bottom = self._snap_to_nearest(bottom, y_lines)
        
        return {
            'x1': new_left,
            'y1': new_top,
            'x2': new_right,
            'y2': new_bottom,
            'class': rect['class'],
            'confidence': rect['confidence']
        }
    
    def _snap_to_nearest(self, value: float, lines: list) -> float:
        distances = [abs(line - value) for line in lines]
        min_distance = min(distances) if distances else float('inf')
        
        if min_distance <= self.snap_threshold:
            return lines[distances.index(min_distance)]
        return value
    
    def align_rectangles(self, rectangles: list) -> list:
        x_lines, y_lines = self.find_common_lines(rectangles)
        aligned_rectangles = [
            self.snap_rectangle(rect, x_lines, y_lines)
            for rect in rectangles
        ]
        return aligned_rectangles

script_dir = os.path.dirname(os.path.abspath(__file__))
car_icon_dir = os.path.join(script_dir, 'carpng.png')
car_icon = cv2.imread(car_icon_dir, cv2.IMREAD_UNCHANGED)  # Load with alpha channel

def draw_rectangle(graphic, x, y, width, height, color):
    height = int(height / 2)

    # Draw the red rectangle
    cv2.rectangle(graphic, (x - width, y - height), (x, y + height), color, thickness=2)

    # If color is red, overlay a car icon
    if color == (0, 0, 255):  # Red in BGR
        overlay_car(graphic, x - width // 2, y - height // 2, width, height)

def overlay_car(graphic, x, y, width, height):
    """Overlays a red car icon inside the rectangle."""
    global car_icon

    if car_icon is None:
        print("Car icon not loaded!")
        return

    # Resize the car icon to fit inside the rectangle
    car_resized = cv2.resize(car_icon, (width, height))

    # Get icon dimensions
    icon_h, icon_w, icon_c = car_resized.shape
    if icon_c == 4:  # If it has an alpha channel
        alpha_mask = car_resized[:, :, 3] / 255.0  # Normalize alpha to [0,1]
        for c in range(3):  # Blend only RGB channels
            graphic[y:y+icon_h, x:x+icon_w, c] = (1 - alpha_mask) * graphic[y:y+icon_h, x:x+icon_w, c] + alpha_mask * car_resized[:, :, c]
    else:
        graphic[y:y+icon_h, x:x+icon_w] = car_resized  # No alpha, just copy

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
    # Construct path to parkinglotimages relative to the script
    parking_lot_images = os.path.join(script_dir, 'parkinglotimages')

    # print("here is the location:", parking_lot_images)
    # Get list of images
    images = os.listdir(parking_lot_images)
    # parking_lot_images = './parkinglotimages'  # Replace with your input folder path
    
    # images = os.listdir(parking_lot_images)
    for image in images:
        if image.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            image_path = os.path.join(parking_lot_images, image)
            scan_parking_lot(image_path)
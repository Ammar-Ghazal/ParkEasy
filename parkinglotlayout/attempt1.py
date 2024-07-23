import cv2
import numpy as np
import os

def highlight_gridlines(image_path):
    # Load the image, and convert it to grayscale (black & white)
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Reduce noise in the image by applying gaussian filter:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding to separate foreground from background, using difference in pixel intensities
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Determine the contours using the separated foreground and background
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize variables to store largest contour
    max_area = 0
    best_cnt = None

    # Iterate through contours to find the largest one
    for c in contours:
        area = cv2.contourArea(c)
        if area > max_area:
            max_area = area
            best_cnt = c

    # Create a mask from the largest contour
    mask = np.zeros_like(gray, np.uint8)
    cv2.drawContours(mask, [best_cnt], -1, 255, -1)

    # Create output image using the mask
    out = np.zeros_like(gray)
    out[mask == 255] = gray[mask == 255]

    # Apply Gaussian blur again to the output image
    blur_out = cv2.GaussianBlur(out, (5, 5), 0)

    # Apply adaptive thresholding on the blurred output image
    thresh_out = cv2.adaptiveThreshold(blur_out, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours in the thresholded output image
    contours_out, _ = cv2.findContours(thresh_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours on the original image
    for c in contours_out:
        area = cv2.contourArea(c)
        if area > 1000:
            cv2.drawContours(image, [c], -1, (0, 255, 0), 3)

    # Display the final image with contours
    cv2.imshow("Final Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parking_lot_images = './parkinglotimages'  # Replace with your input folder path
    
    images = os.listdir(parking_lot_images)
    for image in images:
        if image.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            image_path = os.path.join(parking_lot_images, image)
            highlight_gridlines(image_path)

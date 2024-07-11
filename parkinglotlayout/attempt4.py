import cv2
import os
import numpy as np

def highlight_gridlines(image_path):
    # Load the image, and convert it to grayscale (black & white)
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Reduce noise in the image by applying gaussian filter:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try adding another filter for smoother results:
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        # didnt affect anything, visually speaking

    # Apply adaptive thresholding to separate foreground from background, using difference in pixel intensities
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        # modified adaptive thresholding parameters to filter the image

    # Additional noise reduction step:
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Detect lines using Hough transform
    lines = cv2.HoughLines(thresh, 1, np.pi/180, threshold=100)

    # Draw detected lines on a blank image
    line_image = np.zeros_like(thresh)
    if lines is not None:
        for line in lines:
            rho, theta = line[0]
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * (a))
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * (a))
            cv2.line(line_image, (x1, y1), (x2, y2), 255, 2)

    # Display the result
    cv2.imshow('Cleaned Image with Lines', line_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parking_lot_images = './parkinglotimages'  # Replace with your input folder path
    
    images = os.listdir(parking_lot_images)
    for image in images:
        if image.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            image_path = os.path.join(parking_lot_images, image)
            highlight_gridlines(image_path)

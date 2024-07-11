import cv2
import os
import numpy as np

def highlight_gridlines(image_path):
    # Load the image, and convert it to grayscale (black & white)
    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Grayscale Image', gray)

    # Reduce noise in the image by applying gaussian filter:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    cv2.imshow('Gaussian Blur Image', blur)

    # Try adding another filter for smoother results:
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    cv2.imshow('Bilateral Filter Image', filtered)
        # didnt affect anything, visually speaking

    # Apply adaptive thresholding to separate foreground from background, using difference in pixel intensities
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    cv2.imshow('Adaptive Threshold Image', thresh)
        # modified adaptive thresholding parameters to filter the image

    # Additional noise reduction step:
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    cv2.imshow('Morphology Image', opening)

    # Determine the contours using the separated foreground and background
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Draw the contours/gridlines
    contour_image = np.zeros_like(image)
    cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)

    # Show the results
    # cv2.imshow('Thresholded Image', thresh)
    cv2.imshow('Contours', contour_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parking_lot_images = './parkinglotimages'  # Replace with your input folder path
    
    images = os.listdir(parking_lot_images)
    for image in images:
        if image.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            image_path = os.path.join(parking_lot_images, image)
            highlight_gridlines(image_path)

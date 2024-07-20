import cv2
import os
from skimage.metrics import structural_similarity as ssim

# Function to compare two images using MSE and SSIM
def compare_images(image1_path, image2_path, ssim_threshold=0.85):
    # Check if image files exist
    if not os.path.exists(image1_path):
        raise ValueError(f"Image file does not exist at path: {image1_path}")
    if not os.path.exists(image2_path):
        raise ValueError(f"Image file does not exist at path: {image2_path}")

    # Read images
    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)

    # Check if images were loaded successfully
    if image1 is None:
        raise ValueError(f"Image at path {image1_path} could not be loaded.")
    if image2 is None:
        raise ValueError(f"Image at path {image2_path} could not be loaded.")

    # Resize images to match dimensions of the smaller image
    h1, w1 = image1.shape[:2]
    h2, w2 = image2.shape[:2]
    if h1 * w1 > h2 * w2:
        image1 = cv2.resize(image1, (w2, h2))
    else:
        image2 = cv2.resize(image2, (w1, h1))
    #print(f"Image resize was completed")

    # Convert images to grayscale
    gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    
    #print(f"Grayscale was completed")

    # Calculate MSE
    mse = ((gray_image1 - gray_image2) ** 2).mean()

    # Calculate SSIM
    ssim_index, _ = ssim(gray_image1, gray_image2, full=True)

    # Determine if images are different based on SSIM threshold
    if ssim_index < ssim_threshold:
        #print(f"Image is different. SSIM: {ssim_index:.4f}, MSE: {mse:.4f}")
        return 0
    else:
        #print(f"Images are similar enough. SSIM: {ssim_index:.4f}, MSE: {mse:.4f}")
        return 1

    return mse, ssim_index

def is_same(image1_path, image2_path):
    # Compare images if they were successfully loaded
    if os.path.exists(image1_path) and os.path.exists(image2_path):
        try:
            comparison = compare_images(image1_path, image2_path, ssim_threshold=0.85)
            return comparison
        except ValueError as ve:
            print(ve)
    else:
        print("One or both images could not be loaded. Comparison aborted.")

import cv2
import os
from skimage.metrics import structural_similarity as ssim

# Function to compare two images using MSE and SSIM
def compare_images(image1_path, image3_path):
    # Check if image files exist
    if not os.path.exists(image1_path):
        raise ValueError(f"Image file does not exist at path: {image1_path}")
    if not os.path.exists(image3_path):
        raise ValueError(f"Image file does not exist at path: {image3_path}")

    # Read images
    image1 = cv2.imread(image1_path)
    image3 = cv2.imread(image3_path)

    # Check if images were loaded successfully
    if image1 is None:
        raise ValueError(f"Image at path {image1_path} could not be loaded.")
    if image3 is None:
        raise ValueError(f"Image at path {image3_path} could not be loaded.")

    # Resize images to match dimensions of the smaller image
    h1, w1 = image1.shape[:2]
    h2, w2 = image3.shape[:2]
    if h1 * w1 > h2 * w2:
        image1 = cv2.resize(image1, (w2, h2))
    else:
        image2 = cv2.resize(image3, (w1, h1))
    print(f"Image resize was completed")

    # Convert images to grayscale
    gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray_image3 = cv2.cvtColor(image3, cv2.COLOR_BGR2GRAY)
    
    print(f"Grayscale was completed")

    # Calculate MSE
    mse = ((gray_image1 - gray_image3) ** 2).mean()

    # Calculate SSIM
    ssim_index, _ = ssim(gray_image1, gray_image3, full=True)

    return mse, ssim_index
    
    print(f"Calculations completed")

# Function to display images
def display_image(image_path):
    image = cv2.imread(image_path)
    if image is not None:
        cv2.imshow(f"Image: {image_path}", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"Failed to load and display image: {image_path}")

# Paths to your images
image1_path = r'/home/fydp/parkeasy/image1.jpg'
image2_path = r'/home/fydp/parkeasy/image2.jpg'
image3_path = r'/home/fydp/parkeasy/image3.jpg'

# Print image paths
print(f'Image 1 Path: {image1_path}')
print(f'Image 3 Path: {image3_path}')

# Check if images exist and can be opened
if os.path.exists(image1_path):
    print(f"Image 1 exists: {image1_path}")
else:
    print(f"Image 1 does not exist: {image1_path}")

if os.path.exists(image3_path):
    print(f"Image 3 exists: {image3_path}")
else:
    print(f"Image 3 does not exist: {image3_path}")



# Compare images if they were successfully loaded
if os.path.exists(image1_path) and os.path.exists(image2_path):
    try:
        mse_value, ssim_value = compare_images(image1_path, image3_path)
        # Print results
        print(f'MSE: {mse_value}')
        print(f'SSIM: {ssim_value}')
    except ValueError as ve:
        print(ve)
else:
    print("One or both images could not be loaded. Comparison aborted.")

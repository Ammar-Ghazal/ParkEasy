import cv2

# Initialize the camera
cap = cv2.VideoCapture('/dev/video3')

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    # Display the resulting frame
    cv2.imshow('CSI2 Camera', frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()


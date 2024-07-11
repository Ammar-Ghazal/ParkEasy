from ultralytics import YOLO

model = YOLO('yolov8m.pt')

results = model('parkinglot.jpeg', augment=True) 

results[0].show()

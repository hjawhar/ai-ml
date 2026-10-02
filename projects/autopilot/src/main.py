import os 
import cv2
import numpy as np 
import onnxruntime as ort
ort.set_default_logger_severity(3)   # 3 = show only errors

from ultralytics import YOLO

model = YOLO('yolo26s.onnx', task='detect')        # load once; the weights download on first run
# results = model('test.jpg')       # run it; also accepts a cv2 frame, a video path, a URL or a webcam index
# r = results[0]                    # one Results object per image/frame
# print(r)

# Read & display img
# img_path_input = os.path.join('.','','data/test.jpg')
# img = cv2.imread(img_path_input)
# img_path_output = os.path.join('.','','data/test_output.jpg')

# cv2.imwrite(img_path_output, img)
# cv2.imshow('image', img)
# cv2.waitKey(0)

# Read & display video
video_path_input = os.path.join('.','','data/traffic.mp4')
video = cv2.VideoCapture(video_path_input)

ret = True
while ret:
    ret, frame = video.read()
    if not ret:
        break

    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # k_size = 2
    # frame = cv2.blur(frame, (k_size, k_size))
    # Draw edges
    # frame = cv2.Canny(frame, 100, 200)
    
    # frame = cv2.dilate(frame, np.ones((3,3), dtype=np.int8))

    # frame = cv2.erode(frame, np.ones((3,3), dtype=np.int8))

    # results = model.track(frame, persist=True, classes=[2, 3, 5, 7], conf=0.4, verbose=False)

    # classes=[2, 3, 5, 7]
    # results = model.track(frame, persist=True, device=0, conf=0.4, verbose=False, quantize=16)
    results = model.track(frame, persist=True, device=0, classes=[2, 3, 5, 7], conf=0.4, verbose=False)
    
    frame = results[0].plot()

    # frame = cv2.resize(frame, (800, 480))
    cv2.imshow('frame', frame) 

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or cv2.getWindowProperty('frame', cv2.WND_PROP_VISIBLE) < 1:
        break

video.release()
cv2.destroyAllWindows()
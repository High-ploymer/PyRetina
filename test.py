import cv2
import numpy as np

print("1. Testing OpenCV Version:", cv2.__version__)

try:
    # 测试浮点数运算（这是之前报错的根源）
    print("2. Testing Float32 arithmetic...")
    img = np.zeros((100, 100), dtype=np.float32)
    res = cv2.GaussianBlur(img, (0,0), 1.0) - cv2.GaussianBlur(img, (0,0), 2.0)
    print("   -> Arithmetic OK.")
except Exception as e:
    print("   -> ARITHMETIC FAILED:", e)

try:
    # 测试摄像头
    print("3. Testing Camera Access...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("   -> Camera FAILED. Check Permissions in System Settings.")
    else:
        ret, frame = cap.read()
        if ret:
            print("   -> Camera OK. Frame shape:", frame.shape)
        else:
            print("   -> Camera connected but failed to read frame.")
    cap.release()
except Exception as e:
    print("   -> CAMERA ERROR:", e)

print("4. Done.")
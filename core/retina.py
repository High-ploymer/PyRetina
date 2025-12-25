import cv2
import numpy as np

class RetinaProcessor:
    """
    RetinaProcessor v5.0 (UMat Wrapper)
    既然 OpenCV 认不出 Anaconda 的 Numpy 数组，
    我们就把数据包装成 OpenCV 原生的 UMat (Unified Memory)，
    彻底绕过 PyObject -> cv::Mat 的直接类型检查接口。
    """

    def __init__(self):
        print("✅ Running RetinaProcessor v5.0 (UMat Bypass)") 
        self.sigma1 = 1.0
        self.sigma2 = 2.0
        self.gain = 10.0

    def update_params(self, s1, s2, gain=10.0):
        self.sigma1 = max(0.1, s1)
        self.sigma2 = max(0.1, s2)
        self.gain = gain

    def process_frame(self, frame, mode):
        if frame is None:
            return None, None

        # --- 核心黑科技：转换为 UMat ---
        # UMat 是 OpenCV 的透明 API，它告诉 OpenCV "这是你自己的数据结构"
        # 这样就不需要进行 Python Numpy 的 ABI 检查了
        try:
            # 1. 确保是 uint8 (Numpy 侧处理)
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
            # 2. 包装进 UMat
            u_frame = cv2.UMat(frame)
            
        except Exception as e:
            print(f"💥 UMat Conversion Failed: {e}")
            return frame, None

        output_u = None # 存储 UMat 格式的输出

        try:
            # 3. 这里的操作全部基于 UMat，OpenCV 会在内部处理，不回退到 Python
            if len(frame.shape) == 3:
                u_gray = cv2.cvtColor(u_frame, cv2.COLOR_BGR2GRAY)
            else:
                u_gray = u_frame

            # 4. 算法分流
            if mode == 0: # 原图
                output_u = u_frame
            elif mode == 1: # 对比度
                # CLAHE 需要特殊处理，先做基础转换
                # UMat 也可以直接操作，但在 Mac 上可能有变数，这里保持简单
                output_u = u_frame 
            elif mode == 2: # 边缘
                u_edges = cv2.Canny(u_gray, 100, 200)
                output_u = cv2.cvtColor(u_edges, cv2.COLOR_GRAY2BGR)
            elif mode == 3: # Ganglion DoG
                output_u = self._mode_ganglion_simulation_umat(u_gray)
            
            # 5. 如果 output_u 还是 None (比如 mode=1没实现)，回退原图
            if output_u is None:
                output_u = u_frame

        except Exception as e:
            print(f"⚠️ UMat Algorithm Error: {e}")
            return frame, None

        # 6. 最后时刻：从 UMat 取回 Numpy 数组用于显示
        # .get() 是 UMat 转 Numpy 的标准方法
        try:
            output = output_u.get()
            # 确保此时 output 是连续的，方便 window.py 显示
            output = np.ascontiguousarray(output)
        except Exception as e:
             print(f"⚠️ UMat Retrieval Error: {e}")
             return frame, None

        # 7. 直方图 (用 Numpy 算，因为快)
        hist_img = self._draw_histogram(output if mode != 3 else output_u.get())
            
        return output, hist_img

    def _mode_ganglion_simulation_umat(self, u_gray):
        # UMat 版本的算法，全程在 C++ 内存中漫游
        
        # 转换浮点 (OpenCV 内部函数)
        # CV_32F = 5
        u_float = cv2.normalize(u_gray, None, 0, 1.0, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
        
        # GaussianBlur 支持 UMat
        g1 = cv2.GaussianBlur(u_float, (0, 0), self.sigma1)
        g2 = cv2.GaussianBlur(u_float, (0, 0), self.sigma2)
        
        # DoG
        dog = cv2.subtract(g1, g2)
        
        # Normalize
        dog_norm = cv2.normalize(dog, None, 0, 255, cv2.NORM_MINMAX)
        
        # Convert back to uint8
        dog_uint8 = cv2.convertScaleAbs(dog_norm)
        
        # Heatmap
        heatmap = cv2.applyColorMap(dog_uint8, cv2.COLORMAP_JET)
        
        return heatmap

    def _draw_histogram(self, src_img):
        # 直方图部分保持不变，因为它是纯 Python 逻辑，不涉及复杂的 C++ 传递
        if src_img is None: return None
        if isinstance(src_img, cv2.UMat):
            src_img = src_img.get()
            
        if len(src_img.shape) == 3:
            gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = src_img
            
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, 100, cv2.NORM_MINMAX)
        
        h, w = 100, 256
        hist_img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.line(hist_img, (0, 50), (256, 50), (40, 40, 40), 1)
        points = []
        for i in range(256):
            points.append((i, h - int(hist[i])))
        cv2.polylines(hist_img, [np.array(points)], False, (0, 255, 0), 1)
        return hist_img
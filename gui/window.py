import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QFileDialog, QGroupBox,
                             QSlider, QFrame)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QFont
from core.retina import RetinaProcessor

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.processor = RetinaProcessor()
        self.timer = QTimer()
        self.cap = None
        self.is_camera = False
        self.current_frame = None
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PyRetina v2.0 - 神经形态视觉仿真平台")
        self.resize(1300, 750)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Microsoft YaHei', sans-serif; }
            QGroupBox { border: 1px solid #444; border-radius: 6px; margin-top: 12px; font-weight: bold; color: #88c0d0; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QPushButton { background-color: #3b4252; border: 1px solid #4c566a; border-radius: 4px; padding: 5px; min-height: 25px; }
            QPushButton:hover { background-color: #434c5e; border-color: #88c0d0; }
            QPushButton:pressed { background-color: #2e3440; }
            QComboBox { background-color: #3b4252; border: 1px solid #4c566a; padding: 5px; border-radius: 4px; }
            QSlider::groove:horizontal { border: 1px solid #444; height: 6px; background: #2e3440; margin: 2px 0; border-radius: 3px; }
            QSlider::handle:horizontal { background: #88c0d0; width: 14px; margin: -4px 0; border-radius: 7px; }
        """)

        # === 主布局 ===
        main_layout = QVBoxLayout()
        
        # 1. 顶部：双屏显示区
        view_layout = QHBoxLayout()
        self.view_original = self.create_monitor_screen("生物视觉输入 (Biological Input)")
        self.view_processed = self.create_monitor_screen("神经节细胞响应 (Ganglion Response)")
        
        view_layout.addWidget(self.view_original)
        view_layout.addSpacing(15)
        view_layout.addWidget(self.view_processed)
        
        # 2. 底部：控制台
        dashboard_layout = QHBoxLayout()
        
        # [控制区 A] 数据源
        box_input = QGroupBox("数据源控制 (DATA SOURCE)")
        l_input = QVBoxLayout()
        self.btn_img = QPushButton("加载静态图像")
        self.btn_img.clicked.connect(self.open_image)
        
        self.btn_cam = QPushButton("启动实时视频流")
        self.btn_cam.setStyleSheet("color: #a3be8c;") 
        self.btn_cam.clicked.connect(self.toggle_camera)
        
        self.combo_mode = QComboBox()
        self.combo_mode.addItems([
            "0: 直通模式 (Pass-Through)", 
            "1: 自适应对比度 (Adaptive Contrast)", 
            "2: 边缘通路 (Edge Pathway)", 
            "3: 神经节 DoG 仿真 (Ganglion Model)"
        ])
        self.combo_mode.setCurrentIndex(3)
        self.combo_mode.currentIndexChanged.connect(self.refresh_static)
        
        l_input.addWidget(QLabel("算法模式选择:"))
        l_input.addWidget(self.combo_mode)
        l_input.addWidget(self.btn_img)
        l_input.addWidget(self.btn_cam)
        l_input.addStretch()
        box_input.setLayout(l_input)
        
        # [控制区 B] 神经参数
        box_params = QGroupBox("神经动力学参数 (NEURAL TUNING)")
        l_params = QVBoxLayout()
        
        # Slider 1
        self.lbl_s1 = QLabel("兴奋中心 σ (Excitatory): 1.0")
        self.slider_s1 = QSlider(Qt.Orientation.Horizontal)
        self.slider_s1.setRange(1, 100) 
        self.slider_s1.setValue(10)
        self.slider_s1.valueChanged.connect(self.update_params)
        
        # Slider 2
        self.lbl_s2 = QLabel("抑制周边 σ (Inhibitory/Lateral): 2.0")
        self.slider_s2 = QSlider(Qt.Orientation.Horizontal)
        self.slider_s2.setRange(1, 100)
        self.slider_s2.setValue(20)
        self.slider_s2.valueChanged.connect(self.update_params)
        
        l_params.addWidget(self.lbl_s1)
        l_params.addWidget(self.slider_s1)
        l_params.addSpacing(10)
        l_params.addWidget(self.lbl_s2)
        l_params.addWidget(self.slider_s2)
        l_params.addStretch()
        box_params.setLayout(l_params)
        
        # [控制区 C] 信号分析
        box_data = QGroupBox("信号特征分析 (ANALYSIS)")
        l_data = QVBoxLayout()
        self.lbl_hist = QLabel()
        self.lbl_hist.setFixedSize(256, 100)
        self.lbl_hist.setStyleSheet("background-color: #000; border: 1px solid #333;")
        l_data.addWidget(QLabel("时空信号强度直方图 (Sparsity)"))
        l_data.addWidget(self.lbl_hist)
        l_data.addStretch()
        box_data.setLayout(l_data)
        
        dashboard_layout.addWidget(box_input, 1)
        dashboard_layout.addWidget(box_params, 2)
        dashboard_layout.addWidget(box_data, 1)

        main_layout.addLayout(view_layout, 7)
        main_layout.addLayout(dashboard_layout, 3)
        
        self.setLayout(main_layout)
        self.timer.timeout.connect(self.update_frame)

    def create_monitor_screen(self, title):
        frame = QFrame()
        frame.setStyleSheet("background-color: #000; border: 2px solid #333; border-radius: 8px;")
        layout = QVBoxLayout()
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("color: #666; font-weight: bold; border: none; margin-bottom: 5px;")
        
        lbl_display = QLabel("NO SIGNAL")
        lbl_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_display.setStyleSheet("color: #333; border: none;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_display)
        frame.setLayout(layout)
        
        frame.display_lbl = lbl_display 
        return frame

    def update_params(self):
        s1 = self.slider_s1.value() / 10.0
        s2 = self.slider_s2.value() / 10.0
        
        self.lbl_s1.setText(f"兴奋中心 σ (Excitatory): {s1:.1f}")
        self.lbl_s2.setText(f"抑制周边 σ (Inhibitory/Lateral): {s2:.1f}")
        
        self.processor.update_params(s1, s2)
        self.refresh_static()

    def refresh_static(self):
        if not self.is_camera and self.current_frame is not None:
            self.process_and_display()

    def open_image(self):
        if self.is_camera: self.toggle_camera()
        path, _ = QFileDialog.getOpenFileName(self, "Load Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.current_frame = cv2.imread(path)
            self.process_and_display()

    def toggle_camera(self):
        if not self.is_camera:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.is_camera = True
                self.btn_cam.setText("停止采集 (Stop)")
                self.btn_cam.setStyleSheet("color: #bf616a;") 
                self.timer.start(30)
        else:
            self.timer.stop()
            self.cap.release()
            self.is_camera = False
            self.btn_cam.setText("启动实时视频流")
            self.btn_cam.setStyleSheet("color: #a3be8c;") 

    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.process_and_display()

    def process_and_display(self):
        if self.current_frame is None: return

        mode = self.combo_mode.currentIndex()
        processed, hist = self.processor.process_frame(self.current_frame.copy(), mode)
        
        self.show_image(self.current_frame, self.view_original.display_lbl)
        self.show_image(processed, self.view_processed.display_lbl)
        
        if hist is not None:
            self.show_image(hist, self.lbl_hist, is_bgr=False) 

    def show_image(self, cv_img, label_widget, is_bgr=True):
        if cv_img is None: return
        
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        
        if is_bgr:
            img_disp = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        else:
            img_disp = cv_img
            
        q_img = QImage(img_disp.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        label_widget.setPixmap(pixmap.scaled(label_widget.size(), Qt.AspectRatioMode.KeepAspectRatio))
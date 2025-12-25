import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QFrame, 
                             QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPixmap, QColor, QPalette, QBrush, QLinearGradient, QFont, QIcon

# ================= 配置区域 =================
# 请将你的图片路径填入此处，或者将图片重命名为对应的名字
IMAGE_MAP = {
    "rgb_intro": "PyRetina/slide1.png",  # 对应PPT第一张：传统RGB缺陷
    "dvs_intro": "PyRetina/slide2.png",  # 对应PPT第二张：DVS仿生原理
    "cover_bg": "cover_placeholder.png" # 封面图（可选，代码里有兜底逻辑）
}

# ================= 样式表 (QSS) =================
STYLESHEET = """
/* 全局字体与背景 */
QWidget {
    font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    color: #E2E8F0;
}

/* 主窗口背景 - 这里的颜色会在代码里通过 Palette 覆盖，但这里做备用 */
QWidget#MainWindow {
    background-color: #0f172a;
}

/* 右侧内容面板容器 */
QFrame#ContentPanel {
    background-color: rgba(30, 41, 59, 0.75);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    border-top-left-radius: 20px;
    border-bottom-left-radius: 20px;
}

/* 标题 */
QLabel#Title {
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
    background-color: transparent;
}

QLabel#Subtitle {
    font-size: 18px;
    font-weight: 600;
    color: #38bdf8; /* 天蓝色高亮 */
    margin-bottom: 10px;
}

/* 正文段落 */
QLabel#BodyText {
    font-size: 15px;
    line-height: 1.6;
    color: #cbd5e1;
    padding: 10px 0;
}

/* 重点强调卡片 */
QFrame#HighlightCard {
    background-color: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 8px;
    padding: 15px;
}

/* 按钮样式 */
QPushButton {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 25px; /* 圆角胶囊 */
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 30px;
}
QPushButton:hover {
    background-color: rgba(56, 189, 248, 0.2); /* 悬停蓝光 */
    border-color: #38bdf8;
}
QPushButton:pressed {
    background-color: rgba(56, 189, 248, 0.4);
}

/* 主行动按钮 (Launch) */
QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #2563eb);
    border: none;
    font-size: 16px;
    font-weight: bold;
}
QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #1d4ed8);
}

/* 进度点 */
QLabel#DotActive {
    background-color: #38bdf8;
    border-radius: 4px;
    min-width: 20px;
    max-height: 8px;
    min-height: 8px;
}
QLabel#DotInactive {
    background-color: #475569;
    border-radius: 4px;
    min-width: 8px;
    max-height: 8px;
    min-height: 8px;
}
"""

class IntroWindow(QWidget):
    launch_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyRetina - Neuromorphic Vision System")
        self.resize(1200, 750)
        self.setObjectName("MainWindow")
        
        # 1. 设置酷炫的深空背景
        self.setup_background()
        
        # 2. 应用样式
        self.setStyleSheet(STYLESHEET)
        
        # 3. 初始化 UI 布局
        self.init_ui()

    def setup_background(self):
        palette = QPalette()
        # 创建深邃的径向渐变背景
        gradient = QLinearGradient(0, 0, 1200, 750)
        gradient.setColorAt(0.0, QColor("#0f172a")) # 左上深蓝
        gradient.setColorAt(0.5, QColor("#1e1b4b")) # 中间深紫
        gradient.setColorAt(1.0, QColor("#020617")) # 右下近黑
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)

    def init_ui(self):
        # 主布局：左右分割
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 左侧：视觉展示区 (Image / Illustration) ===
        # 使用 QStackedWidget 方便切换图片
        self.visual_stack = QStackedWidget()
        self.visual_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 对应4个页面的图片容器
        self.visual_stack.addWidget(self.create_visual_page("cover", icon="👁️"))
        self.visual_stack.addWidget(self.create_visual_page("rgb", img_path=IMAGE_MAP["rgb_intro"]))
        self.visual_stack.addWidget(self.create_visual_page("dvs", img_path=IMAGE_MAP["dvs_intro"]))
        self.visual_stack.addWidget(self.create_visual_page("algo", icon="🧠"))
        
        main_layout.addWidget(self.visual_stack, 6) # 左侧占 60%

        # === 右侧：交互叙事区 (Text / Controls) ===
        right_panel = QFrame()
        right_panel.setObjectName("ContentPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50, 60, 50, 60)
        
        # 1. 顶部：步骤指示器 (Progress)
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.dots = []
        for i in range(4):
            dot = QLabel()
            dot.setObjectName("DotInactive")
            self.dots.append(dot)
            self.dots_layout.addWidget(dot)
        right_layout.addLayout(self.dots_layout)
        right_layout.addSpacing(30)

        # 2. 中部：文字内容堆叠区
        self.text_stack = QStackedWidget()
        self.text_stack.addWidget(self.page_1_welcome())
        self.text_stack.addWidget(self.page_2_rgb_limit())
        self.text_stack.addWidget(self.page_3_bio_inspire())
        self.text_stack.addWidget(self.page_4_system())
        right_layout.addWidget(self.text_stack)
        
        right_layout.addStretch() # 弹簧，把内容顶上去

        # 3. 底部：导航按钮
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("Back")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.prev_step)
        self.btn_back.hide() # 第一页隐藏

        self.btn_next = QPushButton("Next Step")
        self.btn_next.setObjectName("PrimaryBtn")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self.next_step)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        
        right_layout.addLayout(nav_layout)
        
        # 添加右侧面板到主布局
        main_layout.addWidget(right_panel, 4) # 右侧占 40%

        # 初始化状态
        self.current_step = 0
        self.update_dots()

    # ================= 辅助函数：创建左侧视觉页 =================
    def create_visual_page(self, page_type, img_path=None, icon=None):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 容器 Frame 用于做阴影和边框
        container = QFrame()
        container.setStyleSheet("""
            background-color: rgba(0,0,0,0.3); 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 15px;
        """)
        con_layout = QVBoxLayout(container)
        con_layout.setContentsMargins(10,10,10,10)

        content_lbl = QLabel()
        content_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 逻辑：如果有图片且路径存在，显示图片；否则显示图标
        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            # 图片缩放逻辑
            scaled_pix = pixmap.scaled(QSize(600, 500), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            content_lbl.setPixmap(scaled_pix)
        else:
            # 默认占位图或者图标
            if icon:
                content_lbl.setText(icon)
                content_lbl.setStyleSheet("font-size: 150px; color: rgba(255,255,255,0.2); border:none;")
            else:
                content_lbl.setText("IMAGE NOT FOUND\n" + (img_path if img_path else ""))
                content_lbl.setStyleSheet("color: red; border:none;")
        
        con_layout.addWidget(content_lbl)
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

        layout.addWidget(container)
        
        # 如果是封面页，加个大标题在图上面
        if page_type == "cover":
            container.setVisible(False) # 封面不需要框
            title = QLabel("PyRetina")
            title.setStyleSheet("font-size: 80px; font-weight: 900; color: #38bdf8; letter-spacing: 2px;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

        return page

    # ================= 右侧文字内容工厂 =================

    def create_rich_text(self, title, subtitle, content, highlight=None):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(15)

        # 1. 小标题 (Category)
        lbl_sub = QLabel(subtitle.upper())
        lbl_sub.setObjectName("Subtitle")
        layout.addWidget(lbl_sub)

        # 2. 主标题 (Headline)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("Title")
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)
        
        layout.addSpacing(10)

        # 3. 正文 (Body)
        lbl_body = QLabel(content)
        lbl_body.setObjectName("BodyText")
        lbl_body.setWordWrap(True)
        lbl_body.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(lbl_body)

        # 4. 高亮卡片 (Highlight - Optional)
        if highlight:
            card = QFrame()
            card.setObjectName("HighlightCard")
            c_layout = QVBoxLayout(card)
            
            icon_lbl = QLabel("💡 核心洞察")
            icon_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 14px; border:none; background:transparent;")
            
            txt_lbl = QLabel(highlight)
            txt_lbl.setStyleSheet("color: #e2e8f0; font-size: 14px; border:none; background:transparent;")
            txt_lbl.setWordWrap(True)
            
            c_layout.addWidget(icon_lbl)
            c_layout.addWidget(txt_lbl)
            layout.addWidget(card)

        layout.addStretch()
        return widget

    # --- Page 1: 欢迎页 ---
    def page_1_welcome(self):
        return self.create_rich_text(
            title="神经形态视觉仿真系统",
            subtitle="Project Overview",
            content="""
            <p>欢迎使用 <b>PyRetina</b>。</p>
            <p>本系统旨在探索下一代机器视觉范式。通过模拟视网膜神经节细胞（RGC）的时空编码机制，我们试图解决传统计算机视觉在<b>高速运动</b>与<b>高动态范围</b>场景下的固有缺陷。</p>
            <p style='color: #94a3b8; font-size: 13px;'>Ready to explore the invisible?</p>
            """
        )

    # --- Page 2: 传统RGB缺陷 (对应 PPT 1) ---
    def page_2_rgb_limit(self):
        return self.create_rich_text(
            title="传统视觉的瓶颈",
            subtitle="The Challenge",
            content="""
            <p>传统 RGB 相机采用<b>“积分成像”</b>模式。无论场景是否有意义，它都以固定频率记录所有像素。</p>
            <ul>
            <li><b>数据冗余：</b>90% 的带宽被浪费在静止背景上。</li>
            <li><b>动态范围受限：</b>隧道出口或逆光下，细节完全丢失。</li>
            <li><b>时延瓶颈：</b>受限于曝光时间和帧率，无法捕捉高速瞬态。</li>
            </ul>
            """,
            highlight="结论：传统帧成像机制限制了端侧场景下的实时感知效率。"
        )

    # --- Page 3: DVS 仿生原理 (对应 PPT 2) ---
    def page_3_bio_inspire(self):
        return self.create_rich_text(
            title="受人眼启发的事件范式",
            subtitle="Bio-Inspiration",
            content="""
            <p>本系统模拟了视网膜<b>周边视觉 (Peripheral Vision)</b> 的工作机制：只关注变化。</p>
            <p><b>DVS (动态视觉传感器) 原理：</b><br>
            每个像素独立工作，仅在光强变化超过阈值时触发。输出数据不再是图像帧，而是连续的<b>事件流 (Event Stream)</b>：</p>
            <p align='center' style='font-size:18px; font-weight:bold; color:#a78bfa;'>ε = {x, y, t, p}</p>
            """,
            highlight="优势：微秒级响应 (μs)、极高动态范围 (>120dB)、极低功耗。"
        )

    # --- Page 4: 系统功能 ---
    def page_4_system(self):
        return self.create_rich_text(
            title="准备启动仿真",
            subtitle="System Ready",
            content="""
            <p>PyRetina 仿真器已就绪。</p>
            <p>我们将使用算法模拟视网膜感受野的<b>“中心-周边拮抗”</b>机制，将输入的 RGB 视频流实时转换为时空事件数据。</p>
            <p>请观察接下来的输出窗口：</p>
            <ul>
            <li><b>On-Events (红点)：</b> 亮度增强</li>
            <li><b>Off-Events (蓝点)：</b> 亮度减弱</li>
            </ul>
            """
        )

    # ================= 交互逻辑 =================
    def update_dots(self):
        for i, dot in enumerate(self.dots):
            if i == self.current_step:
                dot.setObjectName("DotActive")
                # 稍微拉长当前点
                dot.setFixedWidth(30)
            else:
                dot.setObjectName("DotInactive")
                dot.setFixedWidth(8)
            # 刷新样式
            dot.style().unpolish(dot)
            dot.style().polish(dot)

    def next_step(self):
        if self.current_step < 3:
            self.current_step += 1
            self.visual_stack.setCurrentIndex(self.current_step)
            self.text_stack.setCurrentIndex(self.current_step)
            self.update_dots()
            
            # 按钮逻辑
            self.btn_back.show()
            if self.current_step == 3:
                self.btn_next.setText("Launch System 🚀")
                self.btn_next.setStyleSheet("""
                    QPushButton#PrimaryBtn {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                    }
                """)
        else:
            self.launch_signal.emit()
            self.close()

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.visual_stack.setCurrentIndex(self.current_step)
            self.text_stack.setCurrentIndex(self.current_step)
            self.update_dots()
            
            self.btn_next.setText("Next Step")
            # 恢复蓝色按钮样式
            self.btn_next.setStyleSheet("") 
            
            if self.current_step == 0:
                self.btn_back.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntroWindow()
    
    # 模拟启动信号的槽函数
    def start_simulation():
        print(">>> 仿真系统启动！加载主窗口...")
    
    window.launch_signal.connect(start_simulation)
    window.show()
    sys.exit(app.exec())
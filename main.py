import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.intro import IntroWindow  # 导入新写的引导页
from gui.window import MainWindow  # 导入原来的主界面

def main():
    # 1. DPI 适配
    if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, 'PassThrough'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    
    # 2. 实例化两个窗口
    intro = IntroWindow()
    main_win = MainWindow()
    
    # 3. 定义跳转逻辑
    def show_main_window():
        intro.close()      # 关闭引导页
        main_win.show()    # 显示主界面
    
    # 4. 连接信号
    intro.launch_signal.connect(show_main_window)
    
    # 5. 先显示引导页
    intro.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
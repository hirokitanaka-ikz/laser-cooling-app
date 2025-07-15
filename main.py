from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from widgets.ipg_fiber_laser_widget import LaserControlWidget


def main():
    app = QApplication([])

    win = QWidget()
    layout = QVBoxLayout()
    laser_widget = LaserControlWidget()
    layout.addWidget(laser_widget)
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()
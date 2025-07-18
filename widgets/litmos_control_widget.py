from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QFileDialog, QMessageBox, QVBoxLayout
)
from PyQt6.QtCore import QTimer
import csv
import yaml
from pathlib import Path
import logging
import datetime
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def default_filename() -> str:
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{now}_LITMoS"


class LitmosControlPanel(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("LITMoS Control Panel", parent)

        # UI Elements
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked(self.toggle_start)

        layout = QVBoxLayout()
        layout.addWidget(self.start_btn)

        self.setLayout(layout)

    
    def toggle_start(self):
        
        folder = QFileDialog.getExistingDirectory(self, "Select Save Destination Folder")
        if not folder:
            QMessageBox.warning(self, "Cancel", "No save folder selected - measurement not starting")
            return
        
        folder_path = Path(folder)
        default_name = default_filename()
        csv_path = folder_path / f"{default_name}.csv"
        yml_path = folder_path / f"{default_name}.yml"

        # create CSV file
        with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=["timestamp", "device1", "device2"])
            writer.writeheader()

        # create YAML file
        metadata = {
            "start_time": datetime.datetime.now().isoformat()
        }
        with open(yml_path, "w", encoding="utf-8") as f_yml:
            yaml.dump(metadata, f_yml, allow_unicode=True)

        QMessageBox.information(self, "File Created", f"save path: \n{csv_path}\n{yml_path}\n\nmeasurement starting")


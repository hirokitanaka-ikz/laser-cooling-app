import csv
import yaml
import os
from data_interface import IData
from pathlib import Path


ENCODING = "utf-8"


class DataLogger:

    def __init__(self, csv_path, yml_path):
        self._csv_path = csv_path
        self._yml_path = yml_path


    @property
    def csv_path(self) -> Path:
        return self._csv_path
    
    
    @property
    def yml_path(self) -> Path:
        return self._yml_path
    
    
    def write_csv(self, data: IData) -> None:
        """
        Use IData as an interface for different data classes.
        """
        data_dict = data.to_dict()
        # write header if file not existing
        if not os.path.exists(self._csv_path):
            with open(self._csv_path, "w", newline="", encoding=ENCODING) as f_csv:
                writer = csv.DictWriter(f_csv, fieldnames=data_dict.keys())
                writer.writeheader()

        # add data (create csv file if not existing)
        with open(self._csv_path, "a", newline="", encoding=ENCODING) as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=data_dict.keys())
            writer.writerow(data_dict)
    

    def save_meta_data(self, meta_data:dict[str, any]):
        with open(self._yml_path, "w", encoding=ENCODING) as f_yml:
            yaml.dump(meta_data, f_yml, allow_unicode=True)
        


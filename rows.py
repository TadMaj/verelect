import re
from ultralytics import YOLO
from tqdm import tqdm
from PIL import Image
import numpy as np
import cv2
import os
import torch

row_model = YOLO('models/data-row-model.pt')
source = "./data/"

def create_folders_data(num, path):
    os.makedirs(f"{path}/lijst{num}/rows", exist_ok=True)
    return

def data_row_model():
    print("Running data row model")

    for municipality in os.listdir(source):
        print(f"Processing {municipality}")
        for stem in os.listdir(f"{source}/{municipality}"):
            for lijst in [x for x in os.listdir(f"{source}/{municipality}/{stem}") if x.startswith("lijst")]:
                lijst_num = int(lijst.split("lijst")[1])

                create_folders_data(lijst_num, f"{source}/{municipality}/{stem}")
                
                tables = []
                for table in os.listdir(f"{source}/{municipality}/{stem}/{lijst}/table"):
                    tables.append(Image.open(f"{source}/{municipality}/{stem}/{lijst}/table/{table}"))
                
                rows = []
                for index, table in enumerate(tables):
                    row = row_model(table, verbose=False, conf=0.7)
                    for box in row[0].boxes:
                        bounding_box = box.xyxy.tolist()
                        rows.append(table.crop(bounding_box[0]))
                
                for index, row in enumerate(rows):
                    row.save(f"{source}/{municipality}/{stem}/{lijst}/rows/row-{municipality[:4]}-{stem}-{lijst}-{rows.index(row)}.png")

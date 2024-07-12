import re
from ultralytics import YOLO
from PIL import Image
import pytesseract
import numpy as np
import cv2
import os
import torch
import pypdfium2 as pdfium

form_model = YOLO('models/form-object-model.pt')
source = "./data/"

def create_folders_form(num, path):
    os.makedirs(f"{path}/lijst{num}", exist_ok=True)
    os.makedirs(f"{path}/lijst{num}/party", exist_ok=True)
    os.makedirs(f"{path}/lijst{num}/table", exist_ok=True)
    os.makedirs(f"{path}/lijst{num}/subtotal", exist_ok=True)
    os.makedirs(f"{path}/lijst{num}/total", exist_ok=True)
    return

def get_num_from_prediction(elements):
    num = -1
    for element in elements:
        if element[0] == "party":
            name = pytesseract.image_to_string(element[1], lang='eng', config='--psm 6')
            match = re.search(r'Lijst ([0-9]+) ', name)
            try:
                num = int(match.group(1))
            except Exception as e:
                num = -1
    return num

def categorize_form_elements(prediction):
    im_array = prediction.plot(labels=False, conf=False, boxes=False)
    total_types = prediction.names
    elements = []
    for box in prediction.boxes:
        type = total_types[int(box.cls)]
        box = box.xyxy.tolist()
        im = Image.fromarray(im_array[..., ::-1])
        cropped_image = im.crop(box[0])
        elements.append((type, cropped_image))
    return elements


def get_images_from_pdf(pdf):
    f = pdfium.PdfDocument(pdf)
    n_pages = len(f)
    images = []
    for page_number in range(n_pages):
        page = f.get_page(page_number)
        pil_image = page.render(2).to_pil()
        images.append(pil_image)
    return images

def check_relevance(boxes):
    classes = set()
    for box in boxes:
        classes.add(box[0])
    if not "tables" in classes:
        return False
    if not "party" in classes:
        return False
    if not "subtotaal" or not "totaal" in classes:
        return False
    return True  

def form_element_model():
    print("Running form element model")
    # Find data
    for municipality in os.listdir(source):
        print(f"Processing {municipality}")
        for stem in os.listdir(f"{source}/{municipality}"):
            for pdf in os.listdir(f"{source}/{municipality}/{stem}"):
                if pdf.endswith(".pdf"):
                    print(f"Processing {pdf}")
                    images = get_images_from_pdf(f"{source}/{municipality}/{stem}/{pdf}")
                    print(f"Found {len(images)} pages")

                    for index, image in enumerate(images):
                        prediction = form_model(image, verbose=False, stream=True, conf=0.5)
                        for p in prediction:
                            pred = p

                        elements = categorize_form_elements(pred)

                        if not check_relevance(elements):
                            continue

                        lijst_num = get_num_from_prediction(elements)
                        if lijst_num == -1:
                            continue
                        create_folders_form(lijst_num, f"{source}/{municipality}/{stem}/")

                        for element in elements:
                            if element[0] == "party":
                                element[1].save(f"{source}/{municipality}/{stem}/lijst{lijst_num}/party/party-{municipality[:4]}-{stem}-{lijst_num}-{index}-{elements.index(element)}.png")
                            elif element[0] == "tables":
                                element[1].save(f"{source}/{municipality}/{stem}/lijst{lijst_num}/table/table-{municipality[:4]}-{stem}-{lijst_num}-{index}-{elements.index(element)}.png")
                            elif element[0] == "subtotaal":
                                element[1].save(f"{source}/{municipality}/{stem}/lijst{lijst_num}/subtotal/subtotal-{municipality[:4]}-{stem}-{lijst_num}-{index}-{elements.index(element)}.png")
                            elif element[0] == "totaal":
                                element[1].save(f"{source}/{municipality}/{stem}/lijst{lijst_num}/total/total-{municipality[:4]}-{stem}-{lijst_num}-{index}-{elements.index(element)}.png")
                break
    


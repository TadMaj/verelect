import os
from PIL import Image
import cv2
import numpy as np
import shutil
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
import json


source = "./data/"
joined = "./ocr_data/joined"
batched = "./ocr_data/batched"
json_zipped = "./ocr_data/json_zipped"
json_unzipped = "./ocr_data/json"
results = "./ocr_data/results"

endpoint = "https://westeurope.api.cognitive.microsoft.com/"
key = ""

document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

def create_folders_data():
    os.makedirs(joined, exist_ok=True)
    os.makedirs(batched, exist_ok=True)
    os.makedirs(json_zipped, exist_ok=True)
    os.makedirs(json_unzipped, exist_ok=True)
    os.makedirs(results, exist_ok=True)
    return

def overlap(x1, x2, y1, y2):
    return x1 <= y2 and y1 <= x2

def row_joiner():
    for municipality in os.listdir(source):
        m_path = os.path.join(source, municipality)
        for stembureau in os.listdir(m_path):
            st_path = os.path.join(m_path, stembureau)
            for party in [f for f in os.listdir(st_path) if f.startswith("lijst")]:
                p_path = os.path.join(st_path, party)
                images = []
                for fi in [f for f in os.listdir(os.path.join(p_path, "rows")) if f.endswith(".png") and not f.endswith("full.png")]:
                    images.append(Image.open(os.path.join(p_path, "rows", fi)))
                if len(images) == 0:
                    continue

                # Add padding to all of the images
                for idx, im in enumerate(images):
                    im = np.array(im)
                    im = cv2.copyMakeBorder(im, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                    im = Image.fromarray(im)
                    images[idx] = im

                widths, heights = zip(*(i.size for i in images))
                max_width = max(widths)
                total_height = sum(heights)
                new_im = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))

                y_offset = 0
                for im in images:
                    new_im.paste(im, (0,y_offset))   
                    y_offset += im.size[1]

                new_im.save(os.path.join(joined, f"{municipality[5:]}-{stembureau}-{party}.png"))

def batcher():
    files = os.listdir(joined)

    files_a = files[:len(files)//2]
    files_b = files[len(files)//2:]

    zipped_files = list(zip(files_a, files_b))

    for (fa, fb) in zipped_files:
        fa_path = os.path.join(joined, fa)
        fb_path = os.path.join(joined, fb)
        
        im_a = Image.open(fa_path)
        im_b = Image.open(fb_path)

        width_a, height_a = im_a.size
        width_b, height_b = im_b.size

        max_width = max(width_a, width_b)
        max_height = max(height_a, height_b)

        new_im = Image.new('RGB', (max_width * 2, max_height), color=(255, 255, 255))

        new_im.paste(im_a, (0, 0))
        new_im.paste(im_b, (max_width, 0))

        new_im.save(os.path.join(batched, f"{fa.split('.')[0]}&{fb.split('.')[0]}.png"))

    if len(files) % 2 != 0:
        shutil.copy(os.path.join(joined, files[-1]), batched)

def azure_request():
    for fi in os.listdir(batched):
        path = os.path.join(batched, fi)
        image = None
        with open(path, "rb") as f:
            image = f.read()

        analyze_request = {"base64Source": image}

        poller = document_intelligence_client.begin_analyze_document("prebuilt-read", analyze_request)
        result = poller.result()

        d = result.as_dict()

        destination_path = os.path.join(json_zipped, fi.split(".")[0] + ".json")
        #write to file 
        with open(destination_path, "w") as f:
            f.write(json.dumps(d))

def unzip_json():
    for fi in os.listdir(json_zipped):
        if fi.count("&") == 0:
            with open(f"{json_zipped}/{fi}", "r") as f:
                data = json.load(f)
                data = data["paragraphs"]
                d = []
                for paragraph in data:
                    content = paragraph["content"]
                    bounding_box = paragraph["boundingRegions"][0]["polygon"]
                    x1, y1, x2, y2, x3, y3, x4, y4 = bounding_box

                    content = content.replace(" ", "")
                    content = content.replace("-", "")
                    content = content.replace(":", "")
                    content = content.replace(";", "")
                    content = content.replace("!", "1")

                    if content == "":
                        continue
                    d.append((content, bounding_box))
                if len(d) != 0:
                    with open(f"{json_unzipped}/{fi}", "w") as f:
                        json.dump(d, f)
            continue
        
        filename = fi.split(".")[0]

        orig_filename = filename + ".png"
        fi1 = filename.split("&")[0] + ".json"
        fi2 = filename.split("&")[1] + ".json"

        image = Image.open(f"{batched}/{orig_filename}")

        # Get dimentions of image
        width, height = image.size
        single_width = width // 2

        data = None
        with open(f"{json_zipped}/{fi}", "r") as f:
            data = json.load(f)
        
        data = data["paragraphs"]

        data1 = []
        data2 = []

        for paragraph in data:
            content = paragraph["content"]
            bounding_box = paragraph["boundingRegions"][0]["polygon"]
            x1, y1, x2, y2, x3, y3, x4, y4 = bounding_box

            content = content.replace(" ", "")
            content = content.replace("-", "")
            content = content.replace(":", "")
            content = content.replace(";", "")
            content = content.replace("!", "1")
            
            if content == "":
                continue

            if x3 <= single_width:
                data1.append((content, bounding_box))
            else:
                data2.append((content, bounding_box))
        if len(data1) != 0:
            with open(f"{json_unzipped}/{fi1}", "w") as f:
                json.dump(data1, f)
        if len(data2) != 0:
            with open(f"{json_unzipped}/{fi2}", "w") as f:
                json.dump(data2, f)

def parse_results():
    for fi in os.listdir(json_unzipped):
        path = os.path.join(json_unzipped, fi)
        data = None
        with open(path, "r") as f:
            data = json.load(f)

        fields = []
        for d in data:
            content, bounding_box = d
            x1, y1, x2, y2, x3, y3, x4, y4 = bounding_box
            min_y = min(y1, y2, y3, y4)
            max_y = max(y1, y2, y3, y4)
            fields.append((content, min_y, max_y, x1))

        fields.sort(key=lambda x: x[1])
        groups = []
        groups.append([fields[0]])
        for i in range(1, len(fields)):
            if overlap(groups[-1][0][1], groups[-1][0][2], fields[i][1], fields[i][2]):
                groups[-1].append(fields[i])
            else:
                groups.append([fields[i]])
        for g in groups:
            g.sort(key=lambda x: x[3])

        dict = {}
        for g in groups:
            key = g[0][0]
            key = ''.join(filter(str.isdigit, key))
            val = ""
            for i in g[1:]:
                val += i[0]
            dict[key] = val
        
        with open(f"{results}/{fi}", "w") as f:
            json.dump(dict, f)

def ocr():
    create_folders_data()
    row_joiner()
    batcher()
    azure_request()
    unzip_json()
    parse_results()
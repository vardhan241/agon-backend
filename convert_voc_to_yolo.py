import os
import xml.etree.ElementTree as ET
import random
import shutil

IMAGE_DIR = "raw_dataset/images"
ANNOTATION_DIR = "raw_dataset/annotations"

TRAIN_IMG = "dataset/train/images"
TRAIN_LABEL = "dataset/train/labels"

VALID_IMG = "dataset/valid/images"
VALID_LABEL = "dataset/valid/labels"

os.makedirs(TRAIN_IMG, exist_ok=True)
os.makedirs(TRAIN_LABEL, exist_ok=True)
os.makedirs(VALID_IMG, exist_ok=True)
os.makedirs(VALID_LABEL, exist_ok=True)

xml_files = [f for f in os.listdir(ANNOTATION_DIR) if f.endswith(".xml")]

random.shuffle(xml_files)

split = int(len(xml_files)*0.8)

train_files = xml_files[:split]
valid_files = xml_files[split:]


def convert(xml_file, output_label):

    tree = ET.parse(os.path.join(ANNOTATION_DIR, xml_file))
    root = tree.getroot()

    width = int(root.find("size/width").text)
    height = int(root.find("size/height").text)

    lines = []

    for obj in root.findall("object"):

        xmin = float(obj.find("bndbox/xmin").text)
        ymin = float(obj.find("bndbox/ymin").text)
        xmax = float(obj.find("bndbox/xmax").text)
        ymax = float(obj.find("bndbox/ymax").text)

        x_center = ((xmin+xmax)/2)/width
        y_center = ((ymin+ymax)/2)/height
        w = (xmax-xmin)/width
        h = (ymax-ymin)/height

        lines.append(f"0 {x_center} {y_center} {w} {h}")

    with open(output_label, "w") as f:
        f.write("\n".join(lines))


for xml_file in train_files:

    image_name = xml_file.replace(".xml", ".png")

    convert(
        xml_file,
        os.path.join(TRAIN_LABEL, xml_file.replace(".xml", ".txt"))
    )

    shutil.copy(
        os.path.join(IMAGE_DIR, image_name),
        os.path.join(TRAIN_IMG, image_name)
    )


for xml_file in valid_files:

    image_name = xml_file.replace(".xml", ".png")

    convert(
        xml_file,
        os.path.join(VALID_LABEL, xml_file.replace(".xml", ".txt"))
    )

    shutil.copy(
        os.path.join(IMAGE_DIR, image_name),
        os.path.join(VALID_IMG, image_name)
    )

print("Dataset conversion completed.")
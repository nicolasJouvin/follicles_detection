import os
import glob
import xml.etree.ElementTree as ET

import click
import pandas as pd


def convert_class_to_int_label(label_text):
    conversion = {
        "Negative": 0,
        "Primordial": 1,
        "Primary": 2,
        "Secondary": 3,
        "Tertiary": 4,
    }
    return conversion[label_text]


def xml_to_csv(path):
    xml_list = []
    for xml_file in glob.glob(path + "/*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for member in root.findall("object"):
            label_text = member[0].text
            label_int = convert_class_to_int_label(label_text)

            value = (
                root.find("filename").text,
                int(root.find("size")[0].text),
                int(root.find("size")[1].text),
                label_text,
                label_int,
                int(member[4][0].text),
                int(member[4][1].text),
                int(member[4][2].text),
                int(member[4][3].text),
            )

            xml_list.append(value)

    column_names = [
        "filename",
        "width",
        "height",
        "class",
        "label",
        "xmin",
        "ymin",
        "xmax",
        "ymax",
    ]
    xml_df = pd.DataFrame(xml_list, columns=column_names)
    xml_df = xml_df.sort_values(by=["filename", "class", "xmin", "ymin"])
    return xml_df


def remove_impossible_bounding_boxes(xml_df):
    boxes = xml_df.loc[:, ["xmin", "ymin", "xmax", "ymax"]]

    has_nan = boxes.isnull().any(axis="columns")
    print(f"Bounding boxes with NaN coordinates: {has_nan.sum()}")

    has_nagative = (boxes < 0).any(axis="columns")
    print(f"Bounding boxes with negative coordinates: {has_nagative.sum()}")

    max_pixel_width = 50_000
    has_huge = (boxes > max_pixel_width).any(axis="columns")
    print(f"Bounding boxes with very large coordinates: {has_huge.sum()}")

    to_remove = has_nan | has_nagative | has_huge
    print(f"Removing {to_remove.sum()} coordinates from the dataset.")
    xml_df = xml_df.loc[~to_remove]

    return xml_df


@click.command()
@click.argument("xml_folder", type=click.Path(exists=True, file_okay=False))
@click.argument("csv_path", type=click.Path(dir_okay=False))
def main(xml_folder, csv_path):
    """Convert xml files in folder XML_FOLDER to a single labels.csv"""
    parent_folder = os.path.dirname(xml_folder)
    assert csv_path.endswith(".csv")
    # output_filename = os.path.join(parent_folder, "labels.csv")

    # image_path = os.path.join(os.getcwd(), folder)
    print(f"Reading xml files in {parent_folder}")

    xml_df = xml_to_csv(xml_folder)
    xml_df = remove_impossible_bounding_boxes(xml_df)
    xml_df.to_csv(csv_path, index=None)

    print(f"Successfully converted xml to csv: {csv_path}")


if __name__ == "__main__":
    main()
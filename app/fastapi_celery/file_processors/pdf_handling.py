"""
Utility function for showing images.

Intended to be imported in Jupyter notebooks to display pixmap images.

Invocation: "show_image(item, title)", where item is a PyMuPDF object
which has a "get_pixmap" method, and title is an optional string.

The function executes "item.get_pixmap(dpi=150)" and show the resulting
image.


Dependencies
------------
numpy, matplotlib, pymupdf
"""
import os
from pathlib import Path
import pandas as pd
import pymupdf as fitz
import numpy as np
import matplotlib.pyplot as plt

class PDFHandling:
    def __init__(self, file: Path):
        self.file_path = file

    @staticmethod
    def __show_image(item, title=""):
        """Display a pixmap.

        Just to display Pixmap image of "item" - ignore the man behind the curtain.

        Args:
            item: any PyMuPDF object having a "get_pixmap" method.
            title: a string to be used as image title

        Generates an RGB Pixmap from item using a constant DPI and using matplotlib
        to show it inline of the notebook.
        """
        DPI = 150  # use this resolution

        # %matplotlib inline
        pix = item.get_pixmap(dpi=DPI)
        img = np.ndarray([pix.h, pix.w, 3], dtype=np.uint8, buffer=pix.samples_mv)
        plt.figure(dpi=DPI)  # set the figure's DPI
        plt.title(title)  # set title of image
        _ = plt.imshow(img, extent=(0, pix.w * 72 / DPI, pix.h * 72 / DPI, 0))
    
    def table_extraction(
        self,
        # We must look through all pages to extract all texts from every single page
        page=0
    ):
        doc = fitz.open(self.file_path)
        page = doc[page]
        # self.__show_image(page,"First Page Content")

        tables_found = page.find_tables()  # detect the tables
        for i,tab in enumerate(tables_found):  # iterate over all tables
            for cell in tab.header.cells:
                page.draw_rect(cell,color=fitz.pdfcolor["red"],width=0.3)
            page.draw_rect(tab.bbox,color=fitz.pdfcolor["green"])
            print(f"Table {i} column names: {tab.header.names}, external: {tab.header.external}")
            
        # self.__show_image(page, f"Table & Header BBoxes")

        # choose the second table for conversion to a DataFrame
        # tab = tables_found[0]
        # df = tab.to_pandas()

        # show the DataFrame
        # print(df)

        return page, tables_found

    def page_reviewer(
        self,
        # We must look through all pages to extract all texts from every single page
        page=0
    ):
        page, tables_found = self.table_extraction(page=page)
        # self.__show_image(page,"First Page Content")

        for i,tab in enumerate(tables_found):  # iterate over all tables
            for cell in tab.header.cells:
                page.draw_rect(cell,color=fitz.pdfcolor["red"],width=0.3)
            page.draw_rect(tab.bbox,color=fitz.pdfcolor["green"])
            print(f"Table {i} column names: {tab.header.names}, external: {tab.header.external}")
            
        self.__show_image(page, f"Table & Header BBoxes")
    
    def extract_text_outside_of_table(
        self,
        # Define how many lines to consider as part of the header/footer
        # For example, skip the first and last 10 lines
        header_footer_line_count=10,
        # We must look through all pages to extract all texts from every single page
        page=0
    ):
        # Open the document
        doc = fitz.open(self.file_path)
        page = doc[page]

        # Find tables on the page
        tables = page.find_tables()

        # Extract the bounding boxes of the tables
        table_bboxes = [table.bbox for table in tables]  # Get the coordinates (x0, y0, x1, y1)

        # Extract text as a dictionary
        text_dict = page.get_text("dict")

        # Initialize a list to store the filtered text
        filtered_text = []

        # Track the number of lines to skip
        total_lines = len(text_dict["blocks"])
        skip_lines = set(range(header_footer_line_count))  # Skip first N lines
        skip_lines.update(range(total_lines - header_footer_line_count, total_lines))  # Skip last N lines

        # Loop through blocks of text
        for i, block in enumerate(text_dict["blocks"]):
            if block['type'] == 0:  # It's a text block
                # If the block is in the header or footer, skip it
                if i in skip_lines:
                    continue
                
                # Get the block's bounding box (x0, y0, x1, y1)
                block_bbox = block["bbox"]
                
                # Check if the block is inside any of the tables' bounding boxes
                inside_table = False
                for table_bbox in table_bboxes:
                    if (
                        block_bbox[0] >= table_bbox[0]
                        and block_bbox[1] >= table_bbox[1]
                        and block_bbox[2] <= table_bbox[2]
                        and block_bbox[3] <= table_bbox[3]
                    ):
                        inside_table = True
                        break
                
                # If the block is not inside a table, add it to the filtered text
                if not inside_table:
                    # Process the block text (split into lines)
                    lines = block["lines"]
                    for line in lines:
                        # Extract the text in the line
                        filtered_text.append(" ".join([span['text'] for span in line["spans"]]))

        # You now have the filtered text (outside the tables and header/footer) in `filtered_text`
        filtered_text_str = "\n".join(filtered_text)
        print(filtered_text_str)
        return filtered_text_str
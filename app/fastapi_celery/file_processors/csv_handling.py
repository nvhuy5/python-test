from pathlib import Path
import pandas as pd
import csv
import chardet
from typing import List, Dict, Any, Optional
import re
import os
from dotenv import load_dotenv

load_dotenv()

METADATA_SEPARATOR = os.getenv("METADATA_SEPARATOR", "：")

class CSVHandling:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.encoding = self.detect_encoding()
        self.delimiter = self.guess_delimiter()
        self.rows = self.read_rows()

    def detect_encoding(self) -> str:
        with open(self.file_path, "rb") as f:
            result = chardet.detect(f.read())
        return result["encoding"] or "utf-8"

    def guess_delimiter(self) -> str:
        with open(self.file_path, "r", encoding=self.encoding) as f:
            sample = f.read(2048)
        sniffer = csv.Sniffer()
        return sniffer.sniff(sample).delimiter

    def read_rows(self) -> List[List[str]]:
        with open(self.file_path, "r", encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            return [row for row in reader if any(cell.strip() for cell in row)]
    
    def extract(self) -> Dict[str, Any]:
        metadata = {}
        items = []
        i = 0

        while i < len(self.rows):
            row = self.rows[i]
            key_value_pairs = self.extract_metadata_from_row(row)

            if key_value_pairs:
                metadata.update(key_value_pairs)
                i += 1
                continue

            # Start checking for table data
            header_row = row
            table_block = []
            j = i + 1

            while j < len(self.rows):
                current_row = self.rows[j]
                kv_pairs = self.extract_metadata_from_row(current_row)

                # If metadata is found, stop processing the table and update metadata
                if kv_pairs:
                    metadata.update(kv_pairs)
                    break

                # If the current row has the same number of columns as the header, it is part of the table
                if len(current_row) == len(header_row):
                    table_block.append(current_row)
                    j += 1
                else:
                    break

            # If at least one valid data row is found, treat it as a valid table
            if table_block:
                headers = header_row
                for row_data in table_block:
                    items.append(dict(zip(headers, row_data)))
                i = j  # Move to the row after the table block
            else:
                i += 1  # If no table data is found, move to the next row

        return {"metadata": metadata, "items": items}

    def extract_metadata_from_row(self, row: List[str]) -> Dict[str, str]:
        metadata = {}
        cells = [cell.strip() for cell in row if cell.strip()]
        if not cells:
            return metadata

        handled_cells = set()

        # Special case first: detect header-style with key-value in parentheses
        for cell in cells:
            match = re.search(
                r"(.*)\(([^()]*?" + re.escape(METADATA_SEPARATOR) + r"[^()]*)\)", cell
            )
            if match:
                metadata["header"] = cell
                inner = match.group(2)
                if METADATA_SEPARATOR in inner:
                    key, value = map(str.strip, inner.split(METADATA_SEPARATOR, 1))
                    if key:
                        metadata[key] = value if value else None
                handled_cells.add(cell)

        # Colon-style key-value pairs (also check adjacent cells if value is empty)
        for idx, cell in enumerate(cells):
            if cell in handled_cells:
                continue
            if METADATA_SEPARATOR in cell:
                # Skip if it's a URL when separator is ":"
                if METADATA_SEPARATOR == ":" and re.match(r"https?://", cell):
                    continue

                parts = cell.split(METADATA_SEPARATOR, 1)
                key = parts[0].strip()
                value = parts[1].strip()
                if not value and idx + 1 < len(cells):
                    value = cells[idx + 1].strip()
                if key:
                    metadata[key] = value if value else None

        return metadata

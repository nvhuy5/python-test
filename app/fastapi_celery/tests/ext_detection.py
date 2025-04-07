import unittest
from file_processors.ext_detection import FileExtensionProcessor
from pathlib import Path


file_path = f'{Path(__file__).parent}/samples/chinese-table.pdf'
file_processor = FileExtensionProcessor(file_path)

class TestExtDetection(unittest.TestCase):
    def test_valid_extension(self):
        """Test a file with a valid extension."""
        result = file_processor.get_file_extension()
        print("The result: ", result)
        self.assertEqual(result, ".pdf")
    
    def test_no_extension(self):
        """Test a file with no extension."""
        result = file_processor.get_file_extension()
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()

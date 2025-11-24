import unittest
from datetime import date, datetime
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.retriever import RAGRetriever

class TestTimeLeakage(unittest.TestCase):
    def setUp(self):
        # Mock the vector store to avoid needing actual ChromaDB
        self.retriever = RAGRetriever()
        self.retriever.vector_store = MagicMock()
        
    def create_mock_doc(self, filename, metadata_date=None):
        doc = MagicMock()
        doc.metadata = {'source': f"/path/to/{filename}"}
        if metadata_date:
            doc.metadata['date'] = metadata_date
        return doc

    def test_extract_date_from_filename(self):
        # Test JPM pattern
        d = self.retriever._extract_date_from_filename("JPM_Global_Markets_2008-09-15_12345.pdf")
        self.assertEqual(d, date(2008, 9, 15))
        
        # Test BIS Quarterly pattern
        d = self.retriever._extract_date_from_filename("r_qt0809.pdf")
        self.assertEqual(d, date(2008, 9, 28)) # Approximate end of month
        
        # Test BIS Annual pattern
        d = self.retriever._extract_date_from_filename("ar2007e.pdf")
        self.assertEqual(d, date(2007, 12, 31))

    def test_filter_by_date_strict(self):
        # Simulation date: January 2008 (End of month)
        sim_date = date(2008, 1, 31)
        
        docs = [
            self.create_mock_doc("JPM_2008-01-15.pdf"), # Should keep (past)
            self.create_mock_doc("JPM_2007-12-31.pdf"), # Should keep (past)
            self.create_mock_doc("JPM_2008-02-01.pdf"), # Should remove (future)
            self.create_mock_doc("JPM_2008-09-15.pdf"), # Should remove (future)
            self.create_mock_doc("ar2008e.pdf"),        # Should remove (Dec 31 2008)
        ]
        
        filtered = self.retriever._filter_by_date(docs, sim_date)
        
        filenames = [os.path.basename(d.metadata['source']) for d in filtered]
        self.assertIn("JPM_2008-01-15.pdf", filenames)
        self.assertIn("JPM_2007-12-31.pdf", filenames)
        self.assertNotIn("JPM_2008-02-01.pdf", filenames)
        self.assertNotIn("JPM_2008-09-15.pdf", filenames)
        self.assertNotIn("ar2008e.pdf", filenames)
        
        print(f"Test 1 (Jan 2008): Kept {len(filtered)}/{len(docs)} docs. Correct.")

    def test_filter_by_date_september(self):
        # Simulation date: September 2008
        # Note: In the code we might map "September 2008" to Sept 30 or Oct 1.
        # Let's assume we pass Sept 30.
        sim_date = date(2008, 9, 30)
        
        docs = [
            self.create_mock_doc("JPM_2008-09-15.pdf"), # Should keep
            self.create_mock_doc("JPM_2008-10-01.pdf"), # Should remove
            self.create_mock_doc("r_qt0809.pdf"),       # Should keep (Sept 28)
            self.create_mock_doc("r_qt0812.pdf"),       # Should remove (Dec)
        ]
        
        filtered = self.retriever._filter_by_date(docs, sim_date)
        
        filenames = [os.path.basename(d.metadata['source']) for d in filtered]
        self.assertIn("JPM_2008-09-15.pdf", filenames)
        self.assertIn("r_qt0809.pdf", filenames)
        self.assertNotIn("JPM_2008-10-01.pdf", filenames)
        self.assertNotIn("r_qt0812.pdf", filenames)
        
        print(f"Test 2 (Sept 2008): Kept {len(filtered)}/{len(docs)} docs. Correct.")

if __name__ == '__main__':
    unittest.main()

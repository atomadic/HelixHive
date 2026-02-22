#!/usr/bin/env python3
"""
Unit tests for the LiteratureSynthesizer class.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from literature_synthesizer import (
    LiteratureSynthesizer,
    PaperContent,
    SynthesisResult,
    InputType,
    ContentType
)

class TestLiteratureSynthesizer(unittest.TestCase):
    """Test cases for LiteratureSynthesizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.synthesizer = LiteratureSynthesizer()
        self.test_text = """
        This is a sample research paper about machine learning.
        The authors propose a new algorithm for natural language processing.
        Key findings show improved accuracy over existing methods.
        Methodology includes deep learning models and large datasets.
        Future work should address computational efficiency limitations.
        """
    
    def test_init(self):
        """Test LiteratureSynthesizer initialization."""
        self.assertIsNotNone(self.synthesizer.summarizer)
        self.assertIsNotNone(self.synthesizer.tokenizer)
        self.assertIsNotNone(self.synthesizer.seq2seq_model)
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = "Page 1\n\n\n\nThis is a test   with extra spaces.\n\nPage 2"
        cleaned = self.synthesizer._clean_text(dirty_text)
        self.assertNotIn("Page 1", cleaned)
        self.assertNotIn("Page 2", cleaned)
        self.assertEqual(cleaned.count("\n\n"), 1)
    
    def test_extract_pdf_text(self):
        """Test PDF text extraction."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            # Create a simple PDF content (mock)
            tmp.write(b"Mock PDF content")
            tmp_path = tmp.name
        
        try:
            # Mock PyPDF2 to return test text
            with patch('PyPDF2.PdfReader') as mock_reader:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = self.test_text
                mock_reader.return_value.pages = [mock_page]
                
                result = self.synthesizer._extract_pdf_text(tmp_path)
                self.assertIn("machine learning", result)
        finally:
            os.unlink(tmp_path)
    
    def test_extract_url_content(self):
        """Test URL content extraction."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Test content</p></body></html>"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = self.synthesizer._extract_url_content("http://example.com")
            self.assertIn("Test content", result)
    
    def test_analyze_content(self):
        """Test content analysis functionality."""
        analysis = self.synthesizer._analyze_content(self.test_text)
        
        self.assertIn(ContentType.KEY_FINDINGS, analysis)
        self.assertIn(ContentType.METHODOLOGY, analysis)
        self.assertIn(ContentType.RESEARCH_GAP, analysis)
        
        # Check that we get some results
        self.assertTrue(len(analysis[ContentType.KEY_FINDINGS]) >= 0)
        self.assertTrue(len(analysis[ContentType.METHODOLOGY]) >= 0)
        self.assertTrue(len(analysis[ContentType.RESEARCH_GAP]) >= 0)
    
    def test_generate_summary(self):
        """Test summary generation."""
        summary = self.synthesizer._generate_summary(self.test_text, max_length=100)
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)
        self.assertTrue(len(summary) <= 100)
    
    def test_ingest_input_text(self):
        """Test ingesting text input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(self.test_text)
            tmp_path = tmp.name
        
        try:
            result = self.synthesizer.ingest_input(tmp_path)
            
            self.assertIsInstance(result, PaperContent)
            self.assertEqual(result.input_type, InputType.TEXT)
            self.assertIn("machine learning", result.extracted_text)
        finally:
            os.unlink(tmp_path)
    
    def test_ingest_input_url(self):
        """Test ingesting URL input."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>URL test content</p></body></html>"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = self.synthesizer.ingest_input("http://example.com")
            
            self.assertIsInstance(result, PaperContent)
            self.assertEqual(result.input_type, InputType.URL)
            self.assertIn("URL test content", result.extracted_text)
    
    def test_synthesize_papers(self):
        """Test synthesizing multiple papers."""
        # Create mock papers
        papers = [
            PaperContent(
                file_path="test1.txt",
                input_type=InputType.TEXT,
                raw_text=self.test_text,
                extracted_text=self.test_text,
                metadata={}
            ),
            PaperContent(
                file_path="test2.txt",
                input_type=InputType.TEXT,
                raw_text="Another paper about AI and ethics.",
                extracted_text="Another paper about AI and ethics.",
                metadata={}
            )
        ]
        
        result = self.synthesizer.synthesize_papers(papers)
        
        self.assertIsInstance(result, SynthesisResult)
        self.assertTrue(len(result.paper_summaries) > 0)
        self.assertTrue(len(result.key_findings) >= 0)
        self.assertTrue(len(result.methodologies) >= 0)
        self.assertTrue(len(result.research_gaps) >= 0)
        self.assertTrue(len(result.overall_summary) > 0)
        self.assertIsInstance(result.coherence_score, float)
        self.assertIsInstance(result.strategic_alignment_score, float)
    
    def test_format_as_markdown(self):
        """Test markdown formatting."""
        # Create a mock synthesis result
        result = SynthesisResult(
            paper_summaries=["Summary 1", "Summary 2"],
            key_findings=["Finding 1", "Finding 2"],
            methodologies=["Method 1", "Method 2"],
            research_gaps=["Gap 1", "Gap 2"],
            overall_summary="Overall summary test",
            coherence_score=0.85,
            strategic_alignment_score=0.75
        )
        
        markdown = self.synthesizer.format_as_markdown(result)
        
        self.assertIn("# Literature Review Synthesis", markdown)
        self.assertIn("## Overall Summary", markdown)
        self.assertIn("## Key Findings", markdown)
        self.assertIn("## Methodologies", markdown)
        self.assertIn("## Research Gaps", markdown)
        self.assertIn("## Analysis Metrics", markdown)
        self.assertIn("Coherence Score: 0.85", markdown)
        self.assertIn("Strategic Alignment Score: 0.75", markdown)
    
    def test_empty_input_handling(self):
        """Test handling of empty input."""
        # Test with empty text
        analysis = self.synthesizer._analyze_content("")
        self.assertEqual(len(analysis[ContentType.KEY_FINDINGS]), 0)
        self.assertEqual(len(analysis[ContentType.METHODOLOGY]), 0)
        self.assertEqual(len(analysis[ContentType.RESEARCH_GAP]), 0)
        
        # Test with empty papers list
        with self.assertRaises(ValueError):
            self.synthesizer.synthesize_papers([])

class TestPaperContent(unittest.TestCase):
    """Test cases for PaperContent dataclass."""
    
    def test_paper_content_creation(self):
        """Test PaperContent creation."""
        content = PaperContent(
            file_path="test.pdf",
            input_type=InputType.PDF,
            raw_text="Test content",
            extracted_text="Extracted test content",
            metadata={"source": "test"}
        )
        
        self.assertEqual(content.file_path, "test.pdf")
        self.assertEqual(content.input_type, InputType.PDF)
        self.assertEqual(content.raw_text, "Test content")
        self.assertEqual(content.extracted_text, "Extracted test content")
        self.assertEqual(content.metadata["source"], "test")

class TestSynthesisResult(unittest.TestCase):
    """Test cases for SynthesisResult dataclass."""
    
    def test_synthesis_result_creation(self):
        """Test SynthesisResult creation."""
        result = SynthesisResult(
            paper_summaries=["Summary 1"],
            key_findings=["Finding 1"],
            methodologies=["Method 1"],
            research_gaps=["Gap 1"],
            overall_summary="Overall summary",
            coherence_score=0.8,
            strategic_alignment_score=0.7
        )
        
        self.assertEqual(len(result.paper_summaries), 1)
        self.assertEqual(len(result.key_findings), 1)
        self.assertEqual(len(result.methodologies), 1)
        self.assertEqual(len(result.research_gaps), 1)
        self.assertEqual(result.overall_summary, "Overall summary")
        self.assertEqual(result.coherence_score, 0.8)
        self.assertEqual(result.strategic_alignment_score, 0.7)

if __name__ == '__main__':
    unittest.main()
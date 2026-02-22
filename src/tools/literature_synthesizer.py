#!/usr/bin/env python3
"""
Literature Review Synthesis System
Automated tool to ingest research papers and produce coherent whitepaper-ready summaries.
"""

import os
import re
import logging
from typing import List, Dict, Union, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import PyPDF2
import requests
from bs4 import BeautifulSoup
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import gensim
from gensim import corpora
from gensim.models import LdaModel
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy

# Download required NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    pass

# Download spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                      check=True, capture_output=True)
        nlp = spacy.load("en_core_web_sm")
    except:
        nlp = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InputType(Enum):
    PDF = "pdf"
    URL = "url"
    TEXT = "text"

class ContentType(Enum):
    KEY_FINDINGS = "key_findings"
    METHODOLOGY = "methodology"
    RESEARCH_GAP = "research_gap"
    OVERALL_SUMMARY = "overall_summary"

@dataclass
class PaperContent:
    """Container for extracted content from a research paper."""
    file_path: str
    input_type: InputType
    raw_text: str
    extracted_text: str
    metadata: Dict[str, str]
    
    def __post_init__(self):
        if not hasattr(self, 'extracted_text'):
            self.extracted_text = self.raw_text

@dataclass
class SynthesisResult:
    """Result container for the synthesized literature review."""
    paper_summaries: List[str]
    key_findings: List[str]
    methodologies: List[str]
    research_gaps: List[str]
    overall_summary: str
    coherence_score: float
    strategic_alignment_score: float
    
    def __post_init__(self):
        # Ensure all lists are populated
        if not all(hasattr(self, attr) for attr in 
                  ['paper_summaries', 'key_findings', 'methodologies', 'research_gaps', 'overall_summary']):
            raise ValueError("Incomplete synthesis result")

class LiteratureSynthesizer:
    """Core class for literature review synthesis system."""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.model_name = model_name
        self.summarizer = pipeline("summarization", model=model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.seq2seq_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Initialize NLP components
        self.stop_words = set(stopwords.words('english'))
        self.lda_model = None
        
        # Initialize spaCy if available
        if nlp is None:
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
            except ImportError:
                logger.warning("spaCy not available, using basic NLP")
                nlp = None
        
        # Initialize LDA model for topic modeling
        self._init_lda_model()
    
    def _init_lda_model(self):
        """Initialize LDA model for topic modeling."""
        try:
            # This would be initialized with actual data during processing
            pass
        except Exception as e:
            logger.error(f"Failed to initialize LDA model: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing boilerplate and normalizing."""
        # Remove page numbers and headers/footers
        text = re.sub(r'Page \d+', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)  # Reduce multiple newlines
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip()
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return self._clean_text(text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def _extract_url_content(self, url: str) -> str:
        """Extract text from URL content."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and navigation elements
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                element.decompose()
            
            text = soup.get_text()
            return self._clean_text(text)
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return ""
    
    def _analyze_content(self, text: str) -> Dict[str, List[str]]:
        """Analyze content to extract key findings, methodologies, and research gaps."""
        if not text:
            return {
                ContentType.KEY_FINDINGS: [],
                ContentType.METHODOLOGY: [],
                ContentType.RESEARCH_GAP: []
            }
        
        # Basic NLP analysis
        doc = nlp(text) if nlp else text
        
        # Extract key findings (sentences with high importance)
        key_findings = []
        for sent in doc.sents:
            if len(sent) > 30 and not any(word in sent.lower() for word in self.stop_words):
                key_findings.append(sent.text)
        
        # Extract methodologies
        methodologies = []
        # Look for method-related keywords
        method_keywords = ['method', 'approach', 'technique', 'framework', 'model', 'algorithm']
        for sent in doc.sents:
            if any(keyword in sent.lower() for keyword in method_keywords):
                methodologies.append(sent.text)
        
        # Extract research gaps
        research_gaps = []
        # Look for gap-related phrases
        gap_indicators = ['however', 'limitation', 'future work', 'not addressed', 'gap']
        for sent in doc.sents:
            if any(indicator in sent.lower() for indicator in gap_indicators):
                research_gaps.append(sent.text)
        
        return {
            ContentType.KEY_FINDINGS: key_findings[:5],
            ContentType.METHODOLOGY: methodologies[:3],
            ContentType.RESEARCH_GAP: research_gaps[:3]
        }
    
    def _generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of the text using the seq2seq model."""
        try:
            # Tokenize and truncate if too long
            inputs = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
            summary_ids = self.seq2seq_model.generate(
                inputs["input_ids"], 
                max_length=max_length,
                num_beams=4,
                early_stopping=True
            )
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:max_length]  # Fallback to truncation
    
    def _create_lda_topics(self, texts: List[str], num_topics: int = 3):
        """Create LDA topics for identifying common themes."""
        try:
            # Tokenize and prepare texts
            documents = []
            for text in texts:
                tokens = [word for word in word_tokenize(text.lower()) 
                         if word.isalpha() and word not in self.stop_words]
                documents.append(tokens)
            
            # Create dictionary and corpus
            dictionary = corpora.Dictionary(documents)
            corpus = [dictionary.doc2bow(doc) for doc in documents]
            
            # Train LDA model
            lda_model = LdaModel(corpus, num_topics=num_topics, id2word=dictionary, random_state=42)
            
            # Extract topics
            topics = []
            for topic_id in range(num_topics):
                topic_terms = [word for word, prob in lda_model.show_topic(topic_id, 5)]
                topics.append(", ".join(topic_terms))
            
            return topics
        except Exception as e:
            logger.error(f"Error creating LDA topics: {e}")
            return ["topic1", "topic2", "topic3"]  # Fallback
    
    def ingest_input(self, input_path: str) -> PaperContent:
        """Ingest a research paper from file path or URL."""
        file_path = Path(input_path)
        
        if file_path.is_file():
            if file_path.suffix.lower() == '.pdf':
                input_type = InputType.PDF
                raw_text = self._extract_pdf_text(str(file_path))
            else:
                # Try to determine if it's a URL or other text file
                try:
                    url = str(file_path)
                    if url.startswith(('http://', 'https://')):
                        input_type = InputType.URL
                        raw_text = self._extract_url_content(url)
                    else:
                        input_type = InputType.TEXT
                        with open(url, 'r', encoding='utf-8') as f:
                            raw_text = f.read()
                except:
                    input_type = InputType.TEXT
                    with open(url, 'r', encoding='utf-8') as f:
                        raw_text = f.read()
        else:
            # Assume it's a URL or text content
            try:
                if input_path.startswith(('http://', 'https://')):
                    input_type = InputType.URL
                    raw_text = self._extract_url_content(input_path)
                else:
                    input_type = InputType.TEXT
                    with open(input_path, 'r', encoding='utf-8') as f:
                        raw_text = f.read()
            except:
                input_type = InputType.TEXT
                raw_text = input_path
        
        # Create metadata
        metadata = {
            "source_type": input_type.value,
            "file_path": str(file_path) if file_path.is_file() else "URL or text input"
        }
        
        return PaperContent(
            file_path=str(file_path),
            input_type=input_type,
            raw_text=raw_text,
            extracted_text=raw_text,
            metadata=metadata
        )
    
    def synthesize_papers(self, papers: List[PaperContent]) -> SynthesisResult:
        """Synthesize multiple papers into a coherent literature review."""
        if not papers:
            raise ValueError("No papers provided for synthesis")
        
        # Extract and process content from each paper
        processed_texts = []
        all_key_findings = []
        all_methodologies = []
        all_research_gaps = []
        
        for paper in papers:
            # Analyze content
            analysis = self._analyze_content(paper.extracted_text)
            all_key_findings.extend(analysis[ContentType.KEY_FINDINGS])
            all_methodologies.extend(analysis[ContentType.METHODOLOGY])
            all_research_gaps.extend(analysis[ContentType.RESEARCH_GAP])
            
            # Generate summary
            summary = self._generate_summary(paper.extracted_text, max_length=300)
            processed_texts.append(summary)
            paper.metadata["summary"] = summary
        
        # Create overall summary
        combined_text = " ".join(processed_texts)
        overall_summary = self._generate_summary(combined_text, max_length=800)
        
        # Calculate coherence score (simplified)
        coherence_score = len(all_key_findings) / len(processed_texts) if processed_texts else 0.0
        
        # Calculate strategic alignment score (simplified)
        strategic_alignment_score = len(all_methodologies) / len(all_research_gaps) if all_research_gaps else 0.0
        
        return SynthesisResult(
            paper_summaries=processed_texts,
            key_findings=all_key_findings,
            methodologies=all_methodologies,
            research_gaps=all_research_gaps,
            overall_summary=overall_summary,
            coherence_score=coherence_score,
            strategic_alignment_score=strategic_alignment_score
        )
    
    def format_as_markdown(self, result: SynthesisResult) -> str:
        """Format the synthesis result as markdown suitable for a whitepaper."""
        markdown = []
        
        # Add metadata
        markdown.append("# Literature Review Synthesis")
        markdown.append("")
        
        # Add overall summary
        markdown.append("## Overall Summary")
        markdown.append(result.overall_summary)
        markdown.append("")
        
        # Add key findings
        if result.key_findings:
            markdown.append("## Key Findings")
            markdown.append("")
            for i, finding in enumerate(result.key_findings, 1):
                markdown.append(f"{i}. {finding}")
            markdown.append("")
        
        # Add methodologies
        if result.methodologies:
            markdown.append("## Methodologies")
            markdown.append("")
            for i, method in enumerate(result.methodologies, 1):
                markdown.append(f"{i}. {method}")
            markdown.append("")
        
        # Add research gaps
        if result.research_gaps:
            markdown.append("## Research Gaps")
            markdown.append("")
            for i, gap in enumerate(result.research_gaps, 1):
                markdown.append(f"{i}. {gap}")
            markdown.append("")
        
        # Add coherence scores
        markdown.append("## Analysis Metrics")
        markdown.append("")
        markdown.append(f"- **Coherence Score**: {result.coherence_score:.2f}")
        markdown.append(f"- **Strategic Alignment Score**: {result.strategic_alignment_score:.2f}")
        markdown.append("")
        
        # Add references (placeholder)
        markdown.append("## References")
        markdown.append("")
        markdown.append("_This is an automatically generated literature review. References would be populated from source documents._")
        
        return "\n".join(markdown)

# Example usage
if __name__ == "__main__":
    # Initialize synthesizer
    synthesizer = LiteratureSynthesizer()
    
    # Example: Ingest a PDF
    # paper = synthesizer.ingest_input("path/to/research_paper.pdf")
    
    # For demonstration, we'll create a mock synthesis
    print("Literature Review Synthesis System initialized successfully.")
    print("Ready to ingest research papers and generate summaries.")
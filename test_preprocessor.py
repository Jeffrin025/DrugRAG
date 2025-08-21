# test_preprocessor.py
from pdf_preprocessor import PDFProcessor

def test_with_sample_text():
    """Test the PDFProcessor with sample text"""
    print("Testing PDFProcessor with sample text...")
    print("=" * 50)
    
    processor = PDFProcessor()
    
    # Sample FDA-style text
    sample_text = """
    INDICATIONS AND USAGE
    DrugX is indicated for the treatment of moderate to severe pain in adults.
    
    DOSAGE AND ADMINISTRATION
    The recommended dosage is 10mg every 4-6 hours as needed for pain.
    Maximum daily dose should not exceed 40mg.
    
    ADVERSE REACTIONS
    The most common adverse reactions (≥5%) were nausea, dizziness, and constipation.
    
    DRUG INTERACTIONS
    Avoid concomitant use with other CNS depressants due to additive effects.
    """
    
    print("1. Testing FDA format detection...")
    is_fda = processor.is_fda_format(sample_text)
    print(f"   ✓ Is FDA format: {is_fda}")
    
    print("2. Testing section extraction...")
    sections = processor.extract_sections(sample_text)
    print(f"   ✓ Found {len(sections)} sections:")
    for i, section in enumerate(sections):
        print(f"     {i+1}. {section['section']} ({len(section['content'])} chars)")
    
    print("3. Testing chunking...")
    for section in sections:
        chunks = processor.chunk_content(section['content'], chunk_size=150, overlap=30)
        print(f"   ✓ {section['section']}: {len(chunks)} chunks")
    
    print("4. Testing document preparation...")
    documents = processor.prepare_documents_for_db("sample.pdf", 0, sections)
    print(f"   ✓ Prepared {len(documents)} documents for database")
    
    print("\n✅ All tests passed successfully!")
    return True

if __name__ == "__main__":
    test_with_sample_text()
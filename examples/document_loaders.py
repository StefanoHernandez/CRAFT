"""
Examples for Document Loaders: PDF, CSV, Web

This demonstrates the document loaders added in CRAFT v1.4.0
"""

from pathlib import Path
from craft.loaders import PDFLoader, CSVLoader, WebLoader


def example_1_pdf_basic():
    """Example 1: Load PDF document"""
    print("\n=== Example 1: Load PDF ===\n")

    loader = PDFLoader()

    # Load PDF (replace with actual PDF path)
    pdf_path = "path/to/document.pdf"

    try:
        documents = loader.load(pdf_path)
        print(f"Loaded {len(documents)} pages")

        # Show first page preview
        if documents:
            first_page = documents[0]
            print(f"\nFirst page preview:")
            print(f"Content: {first_page.content[:200]}...")
            print(f"Metadata: {first_page.metadata}")

    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
        print("Create a sample PDF or update the path")


def example_2_pdf_chunking():
    """Example 2: Load PDF and split into chunks"""
    print("\n=== Example 2: PDF Chunking ===\n")

    loader = PDFLoader()

    try:
        # Load and split into 500-character chunks
        chunks = loader.load_and_split(
            "path/to/document.pdf",
            chunk_size=500,
            chunk_overlap=100
        )

        print(f"Split into {len(chunks)} chunks")

        if chunks:
            print(f"\nFirst chunk:")
            print(f"Content: {chunks[0].content}")
            print(f"Metadata: {chunks[0].metadata}")

    except FileNotFoundError:
        print("PDF file not found")


def example_3_pdf_specific_pages():
    """Example 3: Load specific PDF pages"""
    print("\n=== Example 3: Load Specific Pages ===\n")

    loader = PDFLoader()

    try:
        # Load only pages 1, 3, and 5
        pages = loader.load_pages("path/to/document.pdf", page_numbers=[1, 3, 5])

        print(f"Loaded {len(pages)} specific pages")

        for page in pages:
            print(f"Page {page.metadata['page']}: {len(page.content)} characters")

    except FileNotFoundError:
        print("PDF file not found")


def example_4_csv_basic():
    """Example 4: Load CSV document"""
    print("\n=== Example 4: Load CSV ===\n")

    # Create sample CSV first
    import csv
    sample_csv = "sample_data.csv"

    with open(sample_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "content", "author", "date"])
        writer.writeheader()
        writer.writerow({
            "title": "Introduction to RAG",
            "content": "RAG combines retrieval and generation for better AI responses.",
            "author": "Alice",
            "date": "2024-01-15"
        })
        writer.writerow({
            "title": "Advanced RAG Techniques",
            "content": "Hybrid search and reranking improve retrieval quality.",
            "author": "Bob",
            "date": "2024-02-20"
        })

    # Load CSV
    loader = CSVLoader(content_column="content", metadata_columns=["title", "author", "date"])
    documents = loader.load(sample_csv)

    print(f"Loaded {len(documents)} documents from CSV")

    for doc in documents:
        print(f"\nTitle: {doc.metadata.get('title')}")
        print(f"Content: {doc.content}")
        print(f"Author: {doc.metadata.get('author')}")

    # Cleanup
    Path(sample_csv).unlink()


def example_5_csv_multiple_columns():
    """Example 5: CSV with multiple content columns"""
    print("\n=== Example 5: CSV Multiple Columns ===\n")

    import csv
    sample_csv = "articles.csv"

    with open(sample_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "summary", "body", "category"])
        writer.writeheader()
        writer.writerow({
            "title": "CRAFT Framework",
            "summary": "Easy chatbot and RAG integration",
            "body": "CRAFT provides a unified API for multiple LLM providers.",
            "category": "Technology"
        })

    # Combine title, summary, and body as content
    loader = CSVLoader(
        content_columns=["title", "summary", "body"],
        metadata_columns=["category"]
    )

    documents = loader.load(sample_csv)

    print(f"Loaded {len(documents)} documents")
    print(f"\nCombined content: {documents[0].content}")
    print(f"Category: {documents[0].metadata.get('category')}")

    Path(sample_csv).unlink()


def example_6_web_basic():
    """Example 6: Load web page"""
    print("\n=== Example 6: Load Web Page ===\n")

    loader = WebLoader()

    try:
        # Load a web page
        documents = loader.load("https://example.com")

        print(f"Loaded web page")
        print(f"\nTitle: {documents[0].metadata.get('title')}")
        print(f"Content preview: {documents[0].content[:300]}...")

    except Exception as e:
        print(f"Error loading web page: {e}")


def example_7_web_with_selector():
    """Example 7: Extract specific content with CSS selector"""
    print("\n=== Example 7: Web with CSS Selector ===\n")

    # Extract only article content
    loader = WebLoader(selector="article")

    try:
        documents = loader.load("https://example.com/blog/post")

        print(f"Extracted article content")
        print(f"Content: {documents[0].content[:200]}...")

    except Exception as e:
        print(f"Error: {e}")


def example_8_web_batch():
    """Example 8: Load multiple URLs"""
    print("\n=== Example 8: Load Multiple URLs ===\n")

    loader = WebLoader()

    urls = [
        "https://example.com",
        "https://example.org",
        "https://example.net"
    ]

    try:
        documents = loader.load_batch(urls)

        print(f"Loaded {len(documents)} web pages")

        for doc in documents:
            print(f"\nURL: {doc.metadata.get('source')}")
            print(f"Title: {doc.metadata.get('title')}")
            print(f"Length: {len(doc.content)} characters")

    except Exception as e:
        print(f"Error: {e}")


def example_9_web_chunking():
    """Example 9: Load web page and split into chunks"""
    print("\n=== Example 9: Web Chunking ===\n")

    loader = WebLoader()

    try:
        chunks = loader.load_and_split(
            "https://example.com",
            chunk_size=500,
            chunk_overlap=100
        )

        print(f"Split web page into {len(chunks)} chunks")

        if chunks:
            print(f"\nFirst chunk: {chunks[0].content[:200]}...")

    except Exception as e:
        print(f"Error: {e}")


def example_10_combined_loaders():
    """Example 10: Combine multiple loaders for comprehensive ingestion"""
    print("\n=== Example 10: Combined Loaders ===\n")

    all_documents = []

    # Load PDFs
    pdf_loader = PDFLoader()
    try:
        pdf_docs = pdf_loader.load("path/to/document.pdf")
        all_documents.extend(pdf_docs)
        print(f"Loaded {len(pdf_docs)} PDF pages")
    except FileNotFoundError:
        print("No PDF found, skipping")

    # Load CSVs
    import csv
    sample_csv = "temp.csv"
    with open(sample_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text"])
        writer.writeheader()
        writer.writerow({"text": "Sample CSV content"})

    csv_loader = CSVLoader(content_column="text")
    csv_docs = csv_loader.load(sample_csv)
    all_documents.extend(csv_docs)
    print(f"Loaded {len(csv_docs)} CSV rows")

    Path(sample_csv).unlink()

    # Load Web pages
    web_loader = WebLoader()
    try:
        web_docs = web_loader.load("https://example.com")
        all_documents.extend(web_docs)
        print(f"Loaded {len(web_docs)} web pages")
    except Exception as e:
        print(f"Web loading failed: {e}")

    print(f"\nTotal documents loaded: {len(all_documents)}")

    # Show document sources
    sources = set(doc.metadata.get("format") for doc in all_documents)
    print(f"Document formats: {sources}")


if __name__ == "__main__":
    print("CRAFT v1.4.0 - Document Loader Examples")
    print("=" * 50)

    examples = [
        example_1_pdf_basic,
        example_2_pdf_chunking,
        example_3_pdf_specific_pages,
        example_4_csv_basic,
        example_5_csv_multiple_columns,
        example_6_web_basic,
        example_7_web_with_selector,
        example_8_web_batch,
        example_9_web_chunking,
        example_10_combined_loaders,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample error: {str(e)[:100]}")

    print("\n" + "=" * 50)
    print("Examples completed!")

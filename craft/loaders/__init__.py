"""Document loaders for various formats."""

from craft.loaders.base import DocumentLoader, Document

__all__ = [
    "DocumentLoader",
    "Document",
]

# Conditional imports for optional loaders
try:
    from craft.loaders.pdf import PDFLoader
    __all__.append("PDFLoader")
except ImportError:
    pass

try:
    from craft.loaders.csv_loader import CSVLoader
    __all__.append("CSVLoader")
except ImportError:
    pass

try:
    from craft.loaders.web import WebLoader
    __all__.append("WebLoader")
except ImportError:
    pass

"""CSV document loader."""

import csv
from pathlib import Path
from typing import List, Optional, Union

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from craft.loaders.base import DocumentLoader, Document


class CSVLoader(DocumentLoader):
    """
    CSV document loader with pandas support.

    Supports:
    - CSV files with various delimiters
    - Content column selection
    - Metadata from other columns
    - Row-level documents
    - Optional pandas for advanced features

    Example:
        >>> from craft.loaders import CSVLoader
        >>>
        >>> # Load CSV with content from 'text' column
        >>> loader = CSVLoader(content_column="text")
        >>> documents = loader.load("data.csv")
        >>>
        >>> # Use multiple columns as content
        >>> loader = CSVLoader(
        ...     content_columns=["title", "description", "body"],
        ...     metadata_columns=["author", "date", "category"]
        ... )
        >>> documents = loader.load("articles.csv")
    """

    def __init__(
        self,
        content_column: Optional[str] = None,
        content_columns: Optional[List[str]] = None,
        metadata_columns: Optional[List[str]] = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
        **kwargs
    ):
        """
        Initialize CSV loader.

        Args:
            content_column: Single column to use as content (auto-detect if None)
            content_columns: Multiple columns to combine as content
            metadata_columns: Columns to include as metadata (all others if None)
            delimiter: CSV delimiter character
            encoding: File encoding
            **kwargs: Additional loader configuration
        """
        super().__init__(
            content_column=content_column,
            content_columns=content_columns,
            metadata_columns=metadata_columns,
            delimiter=delimiter,
            encoding=encoding,
            **kwargs
        )

        self.content_column = content_column
        self.content_columns = content_columns
        self.metadata_columns = metadata_columns
        self.delimiter = delimiter
        self.encoding = encoding

    def load(self, source: Union[str, Path]) -> List[Document]:
        """
        Load CSV file as documents.

        Args:
            source: Path to CSV file

        Returns:
            List of documents (one per row)
        """
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")

        if PANDAS_AVAILABLE:
            return self._load_with_pandas(source_path)
        else:
            return self._load_with_csv(source_path)

    def _load_with_pandas(self, source_path: Path) -> List[Document]:
        """Load CSV using pandas."""
        df = pd.read_csv(
            source_path,
            delimiter=self.delimiter,
            encoding=self.encoding
        )

        # Determine content columns
        if self.content_columns:
            content_cols = self.content_columns
        elif self.content_column:
            content_cols = [self.content_column]
        else:
            # Auto-detect: use first column that looks like text content
            content_cols = [df.columns[0]]
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ["text", "content", "description", "body"]):
                    content_cols = [col]
                    break

        # Determine metadata columns
        if self.metadata_columns:
            meta_cols = self.metadata_columns
        else:
            meta_cols = [col for col in df.columns if col not in content_cols]

        documents = []
        for idx, row in df.iterrows():
            # Combine content columns
            content_parts = []
            for col in content_cols:
                if col in row and pd.notna(row[col]):
                    content_parts.append(str(row[col]))

            content = " ".join(content_parts)

            if not content.strip():
                continue  # Skip empty rows

            # Build metadata
            metadata = {
                "source": str(source_path),
                "row": int(idx) + 1,
                "format": "csv",
            }

            for col in meta_cols:
                if col in row and pd.notna(row[col]):
                    metadata[col] = row[col]

            documents.append(Document(
                content=content,
                metadata=metadata
            ))

        return documents

    def _load_with_csv(self, source_path: Path) -> List[Document]:
        """Load CSV using standard csv module."""
        documents = []

        with open(source_path, "r", encoding=self.encoding) as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            headers = reader.fieldnames

            if not headers:
                return documents

            # Determine content columns
            if self.content_columns:
                content_cols = self.content_columns
            elif self.content_column:
                content_cols = [self.content_column]
            else:
                # Auto-detect
                content_cols = [headers[0]]
                for col in headers:
                    if any(keyword in col.lower() for keyword in ["text", "content", "description", "body"]):
                        content_cols = [col]
                        break

            # Determine metadata columns
            if self.metadata_columns:
                meta_cols = self.metadata_columns
            else:
                meta_cols = [col for col in headers if col not in content_cols]

            for idx, row in enumerate(reader):
                # Combine content columns
                content_parts = []
                for col in content_cols:
                    if col in row and row[col]:
                        content_parts.append(row[col])

                content = " ".join(content_parts)

                if not content.strip():
                    continue

                # Build metadata
                metadata = {
                    "source": str(source_path),
                    "row": idx + 2,  # +2 because idx is 0-based and header is row 1
                    "format": "csv",
                }

                for col in meta_cols:
                    if col in row and row[col]:
                        metadata[col] = row[col]

                documents.append(Document(
                    content=content,
                    metadata=metadata
                ))

        return documents

    def load_and_split(
        self,
        source: Union[str, Path],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Load CSV and split rows into chunks.

        Args:
            source: Path to CSV file
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of chunked documents
        """
        rows = self.load(source)
        all_chunks = []

        for row_doc in rows:
            # Split each row into chunks if needed
            if len(row_doc.content) > chunk_size:
                chunks = self._split_text(
                    row_doc.content,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    metadata=row_doc.metadata
                )
                all_chunks.extend(chunks)
            else:
                all_chunks.append(row_doc)

        return all_chunks


__all__ = ["CSVLoader", "PANDAS_AVAILABLE"]

import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from io import StringIO


class TransactionParser:
    """Parses transaction CSV files with automatic delimiter and column detection."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.delimiter = ','
        self.headers: List[str] = []
        self.rows: List[Dict[str, str]] = []
        self.date_col: Optional[str] = None
        self.description_col: Optional[str] = None
        self.amount_col: Optional[str] = None

    def parse(self) -> Dict[str, any]:
        """Parse the transaction CSV and return structured data."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Transaction file not found: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            content = f.read()

        # Detect delimiter
        self.delimiter = self._detect_delimiter(content)

        # Parse CSV
        reader = csv.DictReader(StringIO(content), delimiter=self.delimiter)
        self.headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
        
        # Filter out empty rows
        self.rows = [
            {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items() if k}
            for row in reader
            if any(v and str(v).strip() for v in row.values() if v is not None)
        ]

        # Auto-detect important columns
        self._detect_columns()

        return {
            'delimiter': self.delimiter,
            'headers': self.headers,
            'rows': self.rows,
            'date_col': self.date_col,
            'description_col': self.description_col,
            'amount_col': self.amount_col,
            'total_rows': len(self.rows)
        }

    def _detect_delimiter(self, content: str) -> str:
        """Detect CSV delimiter (comma, semicolon, tab)."""
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(content[:2048], delimiters=',;\t')
            return dialect.delimiter
        except Exception:
            comma_count = content[:2048].count(',')
            semicolon_count = content[:2048].count(';')
            tab_count = content[:2048].count('\t')

            if semicolon_count > comma_count and semicolon_count > tab_count:
                return ';'
            elif tab_count > comma_count:
                return '\t'
            else:
                return ','

    def _detect_columns(self):
        """Auto-detect Date, Description, and Amount columns."""
        if not self.headers:
            return

        # Score-based detection
        for header in self.headers:
            lower = header.lower().strip()
            
            # Date detection
            if not self.date_col:
                if lower in ['date', 'transaction date', 'trans date', 'posting date', 'post date']:
                    self.date_col = header
                elif 'date' in lower or 'time' in lower:
                    self.date_col = header

            # Description detection
            if not self.description_col:
                if lower in ['description', 'payee', 'merchant', 'details', 'transaction description', 'narrative', 'memo']:
                    self.description_col = header
                elif any(k in lower for k in ['desc', 'merchant', 'payee', 'name', 'memo']):
                    self.description_col = header

            # Amount detection
            if not self.amount_col:
                if lower in ['amount', 'trans amount', 'transaction amount', 'value']:
                    self.amount_col = header
                elif any(k in lower for k in ['amount', 'debit', 'total']):
                    self.amount_col = header

    def update_column_mapping(self, date_col: Optional[str] = None, description_col: Optional[str] = None, amount_col: Optional[str] = None):
        """Manually update column mappings."""
        if date_col and date_col in self.headers:
            self.date_col = date_col
        if description_col and description_col in self.headers:
            self.description_col = description_col
        if amount_col and amount_col in self.headers:
            self.amount_col = amount_col

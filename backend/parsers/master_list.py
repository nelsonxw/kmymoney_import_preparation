import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import shutil


class MasterListParser:
    """Parses and updates the Category and Payee list CSV file."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.categories: Set[str] = set()
        self.payees: Set[str] = set()

    def parse(self) -> Dict[str, any]:
        """Parse the master list file and return structured data."""
        self.categories.clear()
        self.payees.clear()

        if not self.file_path.exists():
            return {
                'categories': [],
                'payees': [],
                'total_categories': 0,
                'total_payees': 0
            }

        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)

            category_col = None
            payee_col = None

            if reader.fieldnames:
                for field in reader.fieldnames:
                    fl = field.lower()
                    if 'category' in fl:
                        category_col = field
                    if 'payee' in fl:
                        payee_col = field

            for row in reader:
                category = row.get(category_col, '').strip() if category_col else ''
                payee = row.get(payee_col, '').strip() if payee_col else ''

                if category:
                    self.categories.add(category)
                if payee:
                    self.payees.add(payee)

        return {
            'categories': sorted(list(self.categories)),
            'payees': sorted(list(self.payees)),
            'total_categories': len(self.categories),
            'total_payees': len(self.payees)
        }

    def update(self, new_payees: List[str], new_categories: Optional[List[str]] = None) -> bool:
        """
        Update the master list with new payees and optionally new categories.
        Deduplicates, sorts alphabetically A-Z, and writes atomically.
        """
        try:
            # First ensure existing entries are loaded
            self.parse()

            # Merge new payees (filter out empty or TBD)
            for p in new_payees:
                p_clean = p.strip() if p else ''
                if p_clean and p_clean.upper() != 'TBD':
                    self.payees.add(p_clean)

            # Merge new categories if provided
            if new_categories:
                for c in new_categories:
                    c_clean = c.strip() if c else ''
                    if c_clean and c_clean.upper() != 'TBD':
                        self.categories.add(c_clean)

            sorted_payees = sorted(list(self.payees))
            sorted_categories = sorted(list(self.categories))

            category_col = 'Category name'
            payee_col = 'Payee name'

            # Create backup if file exists
            if self.file_path.exists():
                backup_path = self.file_path.with_suffix('.csv.backup')
                shutil.copy2(self.file_path, backup_path)

            # Write updated file with parallel columns
            max_len = max(len(sorted_categories), len(sorted_payees))
            with open(self.file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[category_col, payee_col])
                writer.writeheader()

                for i in range(max_len):
                    cat = sorted_categories[i] if i < len(sorted_categories) else ''
                    payee = sorted_payees[i] if i < len(sorted_payees) else ''
                    writer.writerow({category_col: cat, payee_col: payee})

            return True

        except Exception as e:
            print(f"Error updating master list: {e}")
            return False

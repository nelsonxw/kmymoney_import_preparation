import csv
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


class HistoryParser:
    """Parses KMyMoney Transaction History report CSV and standard tabular formats."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.payee_to_categories: Dict[str, Set[str]] = defaultdict(set)
        self.payee_frequencies: Dict[str, int] = defaultdict(int)
        self.payee_category_amounts: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.all_payees: Set[str] = set()
        self.all_categories: Set[str] = set()

    def parse(self) -> Dict[str, any]:
        """Parse the history file and return structured data with amount statistics."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"History file not found: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Detect if it's KMyMoney report format or standard tabular
        if "Report: Transactions by Payee" in content or "Payee and Date" in content:
            return self._parse_kmymoney_report(content)
        else:
            return self._parse_standard_csv(content)

    def _parse_kmymoney_report(self, content: str) -> Dict[str, any]:
        """Parse KMyMoney report format with Payee headers, Category lines, and Amounts."""
        lines = content.splitlines()
        current_payee = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip report header lines
            if line.startswith('Report:') or 'through' in line.lower() or line.startswith('Payee and Date'):
                continue

            # Skip Total lines
            if line.startswith('Total '):
                continue

            # Parse line using csv.reader for proper quoting and escaping
            try:
                row = list(csv.reader([line]))[0]
            except Exception:
                row = [p.strip() for p in line.split(',')]

            if not row or not row[0]:
                continue

            first_col = row[0].strip()
            is_date = bool(re.match(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$', first_col))

            if not is_date:
                # Payee header line (e.g. "Amazon,," or "0860_YVR_Coastal_News")
                current_payee = first_col
                self.all_payees.add(current_payee)
            else:
                # Transaction line under current_payee
                if current_payee and len(row) >= 2:
                    category = row[1].strip() if len(row) > 1 else ''
                    amt_str = row[2].strip() if len(row) > 2 else ''

                    if category:
                        self.payee_to_categories[current_payee].add(category)
                        self.all_categories.add(category)
                        self.payee_frequencies[current_payee] += 1

                        if amt_str:
                            try:
                                clean_amt = abs(float(amt_str.replace('$', '').replace(',', '').strip()))
                                self.payee_category_amounts[current_payee][category].append(clean_amt)
                            except Exception:
                                pass

        return self._build_result()

    def _parse_standard_csv(self, content: str) -> Dict[str, any]:
        """Parse standard tabular CSV format (Date, Payee, Category, Amount or similar)."""
        reader = csv.DictReader(content.splitlines())
        payee_col = None
        category_col = None
        amount_col = None

        # Detect column names
        if reader.fieldnames:
            for field in reader.fieldnames:
                fl = field.lower()
                if fl in ['payee', 'merchant', 'description']:
                    payee_col = field
                if fl in ['category', 'classification']:
                    category_col = field
                if fl in ['amount', 'value', 'total']:
                    amount_col = field

        if not payee_col and reader.fieldnames and len(reader.fieldnames) >= 2:
            payee_col = reader.fieldnames[1]
        if not category_col and reader.fieldnames and len(reader.fieldnames) >= 3:
            category_col = reader.fieldnames[2]

        for row in reader:
            payee = row.get(payee_col, '').strip() if payee_col else ''
            category = row.get(category_col, '').strip() if category_col else ''
            amt_str = row.get(amount_col, '').strip() if amount_col else ''

            if payee:
                self.all_payees.add(payee)
                self.payee_frequencies[payee] += 1

                if category:
                    self.payee_to_categories[payee].add(category)
                    self.all_categories.add(category)

                    if amt_str:
                        try:
                            clean_amt = abs(float(amt_str.replace('$', '').replace(',', '').strip()))
                            self.payee_category_amounts[payee][category].append(clean_amt)
                        except Exception:
                            pass

        return self._build_result()

    def _build_result(self) -> Dict[str, any]:
        """Compute structured stats including amount ranges and patterns per category."""
        payee_category_stats: Dict[str, Dict[str, Any]] = {}

        for payee, cats in self.payee_category_amounts.items():
            payee_category_stats[payee] = {}
            for cat, amts in cats.items():
                if amts:
                    min_a = round(min(amts), 2)
                    max_a = round(max(amts), 2)
                    avg_a = round(sum(amts) / len(amts), 2)
                    payee_category_stats[payee][cat] = {
                        "count": len(amts),
                        "range": f"${min_a:.2f} - ${max_a:.2f}" if min_a != max_a else f"${min_a:.2f}",
                        "avg": f"${avg_a:.2f}",
                        "min": min_a,
                        "max": max_a,
                        "avg_val": avg_a,
                        "sample_amounts": [round(a, 2) for a in amts[:5]]
                    }

        return {
            'payee_to_categories': {k: sorted(list(v)) for k, v in self.payee_to_categories.items()},
            'payee_category_stats': payee_category_stats,
            'payee_frequencies': dict(self.payee_frequencies),
            'all_payees': sorted(list(self.all_payees)),
            'all_categories': sorted(list(self.all_categories)),
            'total_payees': len(self.all_payees),
            'total_categories': len(self.all_categories)
        }

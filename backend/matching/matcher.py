from typing import Dict, List, Set, Tuple, Optional
from rapidfuzz import fuzz, process
from .normalizer import StringNormalizer


class PayeeMatcher:
    """Multi-stage Payee matching engine to maximize reuse of existing payees."""

    def __init__(self, history_payees: Set[str], master_payees: Set[str]):
        self.history_payees = history_payees
        self.master_payees = master_payees
        self.all_payees = history_payees.union(master_payees)

        # Build normalized index: normalized_str -> original_payee
        self.normalized_payee_map: Dict[str, str] = {}
        # Also lowercased exact index: lower_str -> original_payee
        self.lower_payee_map: Dict[str, str] = {}

        for payee in self.all_payees:
            if not payee:
                continue
            self.lower_payee_map[payee.lower()] = payee
            norm = StringNormalizer.normalize_for_matching(payee)
            if norm:
                self.normalized_payee_map[norm] = payee

    def match(self, description: str) -> Tuple[Optional[str], str, float]:
        """
        Match a transaction description to an existing Payee.
        Returns: (matched_payee, match_method, confidence_score)
        """
        if not description or not description.strip():
            return None, 'none', 0.0

        desc = description.strip()

        # Stage 1: Exact case-sensitive match
        if desc in self.all_payees:
            return desc, 'exact', 1.0

        # Stage 2: Exact case-insensitive match
        if desc.lower() in self.lower_payee_map:
            return self.lower_payee_map[desc.lower()], 'exact_ci', 0.98

        # Stage 3: Known merchant / noise cleaning
        cleaned = StringNormalizer.clean_description(desc)
        if cleaned in self.all_payees:
            return cleaned, 'cleaned_exact', 0.95
        if cleaned.lower() in self.lower_payee_map:
            return self.lower_payee_map[cleaned.lower()], 'cleaned_ci', 0.95

        # Stage 4: Normalized exact match
        norm_desc = StringNormalizer.normalize_for_matching(desc)
        if norm_desc in self.normalized_payee_map:
            return self.normalized_payee_map[norm_desc], 'normalized', 0.90

        # Stage 5: Substring / Token match (e.g. "Costco" inside "Costco Whse Austin")
        for payee in sorted(self.all_payees, key=len, reverse=True):
            if len(payee) < 3:
                continue
            payee_lower = payee.lower()
            # Check word boundary presence
            if f" {payee_lower} " in f" {desc.lower()} ":
                return payee, 'substring', 0.85

        # Stage 6: Fuzzy match using RapidFuzz
        candidates = list(self.all_payees)
        if candidates:
            result = process.extractOne(
                cleaned,
                candidates,
                scorer=fuzz.token_set_ratio,
                score_cutoff=85
            )
            if result:
                matched_payee, score, _ = result
                confidence = round(score / 100.0, 2)
                return matched_payee, 'fuzzy', confidence

        return None, 'none', 0.0


class CategoryMatcher:
    """Category matching with conflict detection for established payees."""

    def __init__(self, payee_to_categories: Dict[str, List[str]], master_categories: Set[str]):
        self.payee_to_categories = payee_to_categories
        self.master_categories = master_categories

    def get_categories_for_payee(self, payee: str) -> Tuple[List[str], bool]:
        """
        Get historical categories for a payee.
        Returns: (categories_list, has_conflict)
        """
        if not payee:
            return [], False

        categories = self.payee_to_categories.get(payee, [])
        has_conflict = len(categories) > 1
        return categories, has_conflict

import re
from typing import List, Optional, Tuple


class StringNormalizer:
    """Normalizes transaction descriptions and extracts merchant names."""

    # Common payment processor / bank prefixes to strip so we get the merchant name
    PAYMENT_GATEWAYS = [
        r'^(?:SQ|TST|PAYPAL|PY|SP)\s*\*\s*',
        r'^(?:POS|ACH|PIN|TRF|XFER|DEBIT|CHECKCARD)\s+(?:PURCHASE|DEBIT|WITHDRAWAL)?\s*',
        r'^(?:PURCHASE|TRANSACTION)\s+AUTHORIZED\s+ON\s+\d{1,2}/\d{1,2}\s*',
        r'^AUTOMATIC\s+PAYMENT\s+-\s+THANK\s+YOU\s*',
        r'^ONLINE\s+PAYMENT\s+-\s+THANK\s+YOU\s*',
    ]

    # Common major merchant patterns to canonical name mapping
    COMMON_MERCHANTS: List[Tuple[str, str]] = [
        (r'^(?:AMZN|AMAZON)(?:\.COM|\s+MKTP|\s+MARKETPLACE|\s+PRIME|\s+RETAIL|\s+GROCERY|\s+VIDEO|\s+WEB\s+SERVICES|\s+DIGITAL)?(?:\s+US|\s+CA)?(?:[\*\s].*)?$', 'Amazon'),
        (r'^APPLE(?:\.COM/BILL|\s+STORE|\s+CASH|\.COM)?(?:\s+.*)?$', 'Apple'),
        (r'^UBER(?:\s*\*TRIP|\s*\*EATS|\s+PENDING|\s+TRIP|\s+EATS)?(?:\s+.*)?$', 'Uber'),
        (r'^LYFT(?:\s*\*RIDE|\s+PENDING|\s+RIDE)?(?:\s+.*)?$', 'Lyft'),
        (r'^NETFLIX(?:\.COM)?(?:\s+.*)?$', 'Netflix'),
        (r'^STARBUCKS(?:\s+STORE|\s+COFFEE)?(?:\s+.*)?$', 'Starbucks'),
        (r'^COSTCO(?:\s+WHSE|\s+WHOLESALE|\.COM|\s+GAS)?(?:\s+.*)?$', 'Costco'),
        (r'^WAL-?MART(?:\s+STORE|\s+SUPERCENTER|\.COM)?(?:\s+.*)?$', 'Walmart'),
        (r'^TARGET(?:\s+T-|\s+STORE|\.COM)?(?:\s+.*)?$', 'Target'),
        (r'^SHELL(?:\s+OIL)?(?:\s+.*)?$', 'Shell'),
        (r'^CHEVRON(?:\s+.*)?$', 'Chevron'),
        (r'^EXXON(?:\s+.*)?$', 'Exxon'),
        (r'^HEB(?:\s+STORE|\s+GROCERY|\s+FOODS)?(?:\s+.*)?$', 'H-E-B'),
        (r'^TRADER\s+JOE\'?S?(?:\s+.*)?$', "Trader Joe's"),
        (r'^WHOLEFDS(?:\s+.*)?$', 'Whole Foods'),
        (r'^SPOTIFY(?:\s+USA|\s+AB)?(?:\s+.*)?$', 'Spotify'),
        (r'^PROVIDENT\s+FUND(?:IN|ING)?(?:\s+.*)?$', 'Provident Funding'),
    ]

    @staticmethod
    def clean_description(text: str) -> str:
        """Strip transaction noise, payment prefixes, reference codes, store numbers."""
        if not text:
            return ''

        t = text.strip()

        # Check known common merchants first
        for pat, canonical in StringNormalizer.COMMON_MERCHANTS:
            if re.match(pat, t, re.IGNORECASE):
                return canonical

        # Strip payment gateway prefixes
        for pat in StringNormalizer.PAYMENT_GATEWAYS:
            t = re.sub(pat, '', t, flags=re.IGNORECASE)

        # Strip reference IDs like *123456 or *4A82K7
        t = re.sub(r'[\*\#]+[A-Z0-9]+$', '', t).strip()

        # Strip confirmation/auth/ref numbers like Confirmation# 2090261626 or AUTH# 1234
        t = re.sub(r'(?:CONFIRMATION|CONF|AUTH|REF)?\s*#\s*[A-Z0-9]+', '', t, flags=re.IGNORECASE).strip()

        # Strip ACH payment codes (e.g., DES:ACH PMT ID:12345, INDN:NAME CO ID:12345)
        t = re.sub(r'DES:ACH\s+PMT\s+ID:\d+', '', t, flags=re.IGNORECASE).strip()
        t = re.sub(r'INDN:[A-Z\s]+\s+CO\s+ID:\d+', '', t, flags=re.IGNORECASE).strip()
        t = re.sub(r'ID:\d+', '', t, flags=re.IGNORECASE).strip()

        # Strip trailing store numbers like STORE 1234 or #1234
        t = re.sub(r'\bSTORE\s*#?\d+\b', '', t, flags=re.IGNORECASE).strip()

        # Strip trailing pure numeric IDs (4+ digits)
        t = re.sub(r'\s+\d{4,}$', '', t).strip()

        # Strip any dangling trailing # or *
        t = re.sub(r'[#\*]+$', '', t).strip()

        # Strip trailing single letters that are often payment codes (e.g., ' P', ' D', ' C')
        t = re.sub(r'\s+[A-Z]$', '', t).strip()

        return t

    @staticmethod
    def normalize_for_matching(text: str) -> str:
        """Normalize string to lowercase alphanumeric with single spaces for robust matching."""
        if not text:
            return ''

        # First clean noise
        cleaned = StringNormalizer.clean_description(text)

        # Lowercase
        normalized = cleaned.lower()

        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        # Collapse whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

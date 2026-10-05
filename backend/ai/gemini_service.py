import httpx
import json
import time
from typing import Dict, List, Optional, Any, Set
from matching.normalizer import StringNormalizer


class GeminiClassificationError(Exception):
    """Raised when all Gemini AI models fail to respond."""
    pass


class GeminiService:
    """Google Gemini Flash AI service for transaction classification."""

    # Active Google Gemini models in order of preference
    CANDIDATE_MODELS = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=60.0)

    def classify_batch(
        self,
        batch_items: List[Dict[str, any]],
        master_payees: List[str],
        master_categories: List[str],
        payee_to_categories: Optional[Dict[str, List[str]]] = None,
        payee_category_stats: Optional[Dict[str, Dict[str, Any]]] = None,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Dict[str, any]]:
        """
        Classify unique transaction items using Google Gemini Flash.
        - Prioritizes matching against master_payees first (even with bank noise/abbreviations)
        - Analyzes payment amount patterns (ranges, averages) for payees with multiple categories
        - Constrains category strictly to master_categories or TBD
        - Raises GeminiClassificationError if all candidate models fail
        """
        if not batch_items:
            return {}

        if not self.api_key or not self.api_key.strip():
            raise GeminiClassificationError(
                "Gemini API key is not configured. Please add your key in Settings or the backend .env file."
            )

        results_map: Dict[str, Dict[str, any]] = {}
        chunk_size = 25
        total_chunks = max(1, (len(batch_items) + chunk_size - 1) // chunk_size)

        for chunk_idx, i in enumerate(range(0, len(batch_items), chunk_size)):
            if progress_callback:
                progress_callback(
                    chunk_idx,
                    total_chunks,
                    f"Querying Gemini 3.8 Flash (Batch {chunk_idx + 1} of {total_chunks})..."
                )

            chunk = batch_items[i:i + chunk_size]
            chunk_results = self._call_gemini_chunk(
                chunk,
                master_payees,
                master_categories,
                payee_to_categories or {},
                payee_category_stats or {}
            )
            results_map.update(chunk_results)

            if progress_callback:
                progress_callback(
                    chunk_idx + 1,
                    total_chunks,
                    f"Completed Batch {chunk_idx + 1} of {total_chunks}"
                )

        return results_map

    def _call_gemini_chunk(
        self,
        chunk: List[Dict[str, any]],
        master_payees: List[str],
        master_categories: List[str],
        payee_to_categories: Dict[str, List[str]],
        payee_category_stats: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, any]]:
        """Call Gemini for a single chunk of items with retry and fallback across models."""
        prompt = self._build_prompt(chunk, master_payees, master_categories, payee_to_categories, payee_category_stats)
        valid_categories = set(master_categories)
        master_payees_set = set(master_payees)
        master_payees_lower = {p.lower(): p for p in master_payees}

        attempted_errors: List[str] = []

        for model in self.CANDIDATE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            for attempt in range(2):  # Retry once on temporary spike (503/429)
                try:
                    response = self.client.post(
                        url,
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "temperature": 0.1,
                                "responseMimeType": "application/json"
                            }
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get('candidates', [])
                        if candidates:
                            text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                            parsed = self._extract_json(text)
                            if parsed and 'results' in parsed:
                                return self._sanitize_results(
                                    parsed['results'],
                                    chunk,
                                    valid_categories,
                                    master_payees_set,
                                    master_payees_lower
                                )

                    # If temporary spike (503 or 429), wait 1.5s and retry once
                    if response.status_code in (503, 429) and attempt == 0:
                        time.sleep(1.5)
                        continue

                    # Extract error details
                    try:
                        err_body = response.json().get('error', {})
                        err_msg = err_body.get('message', response.text[:120])
                    except Exception:
                        err_msg = response.text[:120]

                    attempted_errors.append(f"{model} (HTTP {response.status_code}: {err_msg})")
                    break

                except Exception as e:
                    attempted_errors.append(f"{model} (Exception: {str(e)})")
                    break

        error_details = " | ".join(attempted_errors) if attempted_errors else "No response received"
        raise GeminiClassificationError(
            f"AI classification failed across all models ({', '.join(self.CANDIDATE_MODELS)}). Reason: {error_details}. Please try again in a few moments."
        )

    def _build_prompt(
        self,
        chunk: List[Dict[str, any]],
        master_payees: List[str],
        master_categories: List[str],
        payee_to_categories: Dict[str, List[str]],
        payee_category_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Construct a structured prompt with payee list, master categories, and amount patterns."""
        payees_json = json.dumps(master_payees, ensure_ascii=False)
        categories_json = json.dumps(master_categories, ensure_ascii=False)

        # Build category history enriched with payment amount patterns (ranges, averages, counts)
        combined_history: Dict[str, Any] = {}
        for payee, cats in payee_to_categories.items():
            if payee in payee_category_stats and payee_category_stats[payee]:
                combined_history[payee] = {
                    cat: {
                        "typical_range": payee_category_stats[payee].get(cat, {}).get("range", "N/A"),
                        "avg_amount": payee_category_stats[payee].get(cat, {}).get("avg", "N/A"),
                        "frequency": payee_category_stats[payee].get(cat, {}).get("count", 1)
                    }
                    for cat in cats
                }
            else:
                combined_history[payee] = cats

        history_mappings_json = json.dumps(combined_history, ensure_ascii=False, indent=2)

        return f"""You are an expert personal finance classification engine for KMyMoney accounting software.

Analyze each transaction description and amount, then assign the most accurate "payee" and "category".

CRITICAL RULES AND PRIORITIES:
1. PAYEE MATCHING (HIGHEST PRIORITY):
   - You MUST attempt to match the transaction description to an EXISTING PAYEE from the "EXISTING MASTER PAYEES" list first.
   - Bank descriptions are often noisy, truncated, abbreviated, or contain payment/ACH codes (e.g. "Falcon Pointe Co DES:L584580 ID:OFAL52034 PPD" corresponds to existing payee "Falcon Pointe HOA"; "PROVIDENT FUNDIN DES:ACH PMT ID:... INDN:... P" corresponds to existing payee "Provident Funding"; "AMZN Mktp US*..." corresponds to "Amazon").
   - If the description corresponds to ANY payee in the EXISTING MASTER PAYEES list (regardless of spelling variations, missing words, or bank codes), YOU MUST USE THE EXACT EXISTING PAYEE NAME from the list and set "payee_is_new": false.
   - For internal transfers, deposits, or interest earned where there is no third-party vendor, assign a clean descriptive Payee name (e.g. "Interest Earned", "Automatic Transfer", or the bank name if mentioned); NEVER return "[Empty Payee]", "None", or leave payee blank.
   - Only if the transaction is clearly a merchant, individual, or entity that is NOT in the EXISTING MASTER PAYEES list, generate a concise, human-readable merchant name (removing store numbers, auth codes, dates, and card IDs), and set "payee_is_new": true.

2. CATEGORY ASSIGNMENT & AMOUNT PATTERN MATCHING:
   - PRIORITY 1: If the matched Payee exists in "KNOWN PAYEE CATEGORY HISTORY WITH AMOUNT PATTERNS", YOU MUST SELECT FROM THE ESTABLISHED HISTORICAL CATEGORIES FOR THAT SPECIFIC PAYEE!
   - AMOUNT PATTERN MATCHING FOR MULTI-CATEGORY PAYEES:
     When a Payee has multiple historical categories (e.g. Amazon, Austin Ninjas, Bank of America, Cineplex):
     * COMPARE THE CURRENT TRANSACTION'S "amount" (absolute magnitude) against the historical "typical_range" and "avg_amount" for each candidate category.
     * Identify amount magnitude patterns:
       - Small vs large charges (e.g. at Amazon, an amount around $120-$160 falls right into the "Household: Electronics" range of $75-$165, whereas an amount around $10-$20 aligns with "Household: Cleaning" or "Bills & monthly payments: Membership fee").
       - Recurring/subscription exact amounts (e.g. $10-$20 membership fees).
     * Choose the category whose historical amount range and average best matches the charged amount!
   - PRIORITY 2: Only if the Payee is completely NEW or has no historical category, select the single most appropriate category from the "MASTER CATEGORIES" list.
   - If no category in the list fits or you are uncertain, assign "TBD".
   - CRITICAL CONSTRAINT: NEVER invent or hallucinate a category name! The category MUST be an exact match from MASTER CATEGORIES or "TBD".

3. CONFIDENCE & FLAGS:
   - "payee_is_new": false if matched to an existing master payee, true if a new payee was created.
   - "category_is_new": false if matched to a known master category, true only if not found.
   - "confidence": "high", "medium", or "low".

EXISTING MASTER PAYEES:
{payees_json}

MASTER CATEGORIES:
{categories_json}

KNOWN PAYEE CATEGORY HISTORY WITH AMOUNT PATTERNS:
{history_mappings_json}

TRANSACTIONS TO CLASSIFY:
{json.dumps(chunk, indent=2)}

Respond ONLY with a valid JSON object in this exact format:
{{
  "results": [
    {{
      "id": "item_id_here",
      "payee": "Exact Payee Name",
      "category": "Exact Category from Master List or TBD",
      "payee_is_new": false,
      "category_is_new": false,
      "confidence": "high"
    }}
  ]
}}"""

    def _sanitize_results(
        self,
        raw_results: List[Dict[str, Any]],
        chunk: List[Dict[str, any]],
        valid_categories: Set[str],
        master_payees_set: Set[str],
        master_payees_lower: Dict[str, str]
    ) -> Dict[str, Dict[str, any]]:
        """Validate, sanitize, and map raw AI responses to standard structure."""
        results: Dict[str, Dict[str, any]] = {}
        for res in raw_results:
            item_id = str(res.get('id', ''))
            payee_val = str(res.get('payee', '')).strip()
            cat = str(res.get('category', 'TBD')).strip()

            # Sanitize placeholder payees
            if not payee_val or payee_val.lower() in ('[empty payee]', 'none', 'null', 'empty', '[empty]'):
                orig_desc = next((item.get('description', '') for item in chunk if str(item.get('id')) == item_id), '')
                payee_val = StringNormalizer.clean_description(orig_desc) or orig_desc[:40]

            # Validate category strictly against master categories
            if cat not in valid_categories and cat != 'TBD':
                cat = 'TBD'

            # Validate if payee matches master list
            is_existing_payee = payee_val in master_payees_set
            if not is_existing_payee and payee_val.lower() in master_payees_lower:
                payee_val = master_payees_lower[payee_val.lower()]
                is_existing_payee = True

            results[item_id] = {
                'payee': payee_val,
                'category': cat,
                'payee_is_new': not is_existing_payee,
                'category_is_new': cat not in valid_categories and cat != 'TBD',
                'confidence': res.get('confidence', 'medium')
            }
        return results

    def _extract_json(self, text: str) -> Optional[dict]:
        """Safely parse JSON from LLM output."""
        try:
            return json.loads(text.strip())
        except Exception:
            try:
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0].strip()
                elif '```' in text:
                    text = text.split('```')[1].split('```')[0].strip()
                return json.loads(text)
            except Exception:
                return None

    def close(self):
        """Close the HTTP client."""
        try:
            self.client.close()
        except Exception:
            pass

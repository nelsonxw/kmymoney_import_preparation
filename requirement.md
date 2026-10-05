# AI Transaction Categorization Web App — Requirements

## 1. Objective
Build a web application that allows a user to:
1. **Import a CSV file** containing bank or credit-card transactions.
2. **Automatically assign Payee and Category** to each transaction using:
   - An existing transaction history CSV file containing previous transactions with Payee/Category mappings. A payee may be mapped to one or multiple categories.
   - An existing Category and Payee list CSV file containing all categories used in KMyMoney and all Payee names used in KMyMoney.
   - AI-based interpretation (Google Gemini 2.5/2.0 Flash free tier) when an exact or existing Payee or category cannot be found.
3. **Review and manually correct the results** in an interactive web UI.
4. **Clearly identify newly created Payees and Categories** using prominent visual highlights (red text / red badges).
5. **Export reviewed transactions** as a CSV file with original columns preserved plus the newly determined `Payee` and `Category`.
6. **After successful export, update the Category and Payee list CSV file** with newly approved Payee/Category values.
7. **Keep the Payee and Category list deduplicated and alphabetically sorted (A–Z)**.
8. **Prioritize consistency** with existing CSV data over AI-generated guesses.

---

## 2. Input Files

### 2.1 Transaction CSV
- The application shall allow the user to upload one CSV file at a time.
- The CSV may contain typical bank/credit-card transaction fields such as:
  - Date
  - Description
  - Amount
  - Transaction Type
  - Account
  - Memo
  - Other institution-specific fields
- The application shall not require a fixed column layout.
- During import, the application shall:
  - Detect the CSV delimiter (comma, semicolon, tab).
  - Detect column headers.
  - Display the detected columns to the user.
  - Allow the user to map/identify essential transaction fields (Description/Payee, Amount, Date) if not auto-detected with confidence.
- At minimum, the application requires: Transaction description/payee-related field, Transaction amount, and Date.

### 2.2 Master Transaction History Reference File
- Master CSV containing past transactions with Payee names and associated categories.
- Must support KMyMoney report export format:
  ```
  Report: Transactions by Payee (Customized),,
  1/1/2026 through 10/2/2026,,
  Payee and Date,Category,Amount
  0860_YVR_Coastal_News,,
  8/3/2026,Gifts,-3.14
  Total 0860_YVR_Coastal_News,,-3.14
  ```
  as well as standard tabular formats (`Date, Payee, Category, Amount` or `Payee, Category`).
- Auto-detected from default paths (e.g., `Desktop\Transactions history.csv` or app `data/` folder), with option to upload/re-select in UI.

### 2.3 Category and Payee List Reference File
- An existing CSV file containing two primary columns:
  - `Category name`
  - `Payee name`
- When a match cannot be found in the transaction history, the application looks up this list to reuse existing values.
- Hierarchical category structure (e.g., `Auto:Fuel`, `Bills:Electricity`, `Vacation & Holiday: Tickets`) must be preserved verbatim.
- Auto-detected from default paths or uploaded via UI.

---

## 3. Transaction Processing & Matching Pipeline

```
Transaction
     ↓
Determine Payee
     ↓
Stage 1: Normalization & Matching in Transaction History
     ↓
Matching Payee found in Transaction History?
     ├── YES ──→ Use existing Payee
     │           ↓
     │           Check associated categories:
     │           - Exactly 1 category? → Assign category.
     │           - Multiple categories? (e.g. Amazon -> Shopping / Electronics)
     │             → Flag conflict warning, use AI recommendation, allow user confirmation.
     │
     └── NO  ──→ Stage 2: Matching in Category and Payee List
                 Matching Payee found?
                 ├── YES ──→ Use existing Payee
                 │           ↓
                 │           Use AI / description match to select best category from Master Category List
                 │
                 └── NO  ──→ Stage 3: New Payee via Google Gemini Flash
                             ↓
                             Generate concise, human-readable Payee name
                             (strip IDs, store #, dates, card references)
                             Mark `payee_is_new = true`
                             ↓
Determine Category
     ↓
AI interpretation against Master Category List
     ├── Valid match found in Master Category List ──→ Use existing Category
     └── No confident match ──→ Assign category as "TBD" (Do NOT invent new categories!)
```

---

## 4. Matching Engine & Normalization Rules

1. **High Priority**: Maximum reuse of existing Payees. Never create a new Payee simply because descriptions contain transaction noise.
2. **Multi-tier Matching**:
   - **Exact Matching**: Identical string match.
   - **Normalized Matching**: Lowercased, stripped punctuation, normalized whitespace.
   - **Prefix & Noise Cleaning**:
     - Strips payment prefixes: `SQ *`, `TST* `, `PAYPAL *`, `AMZN Mktp US*`, `APPLE.COM/BILL`, `UBER *TRIP`.
     - Strips store/location suffixes: `#1234`, `STORE 0231`, city/state codes, phone numbers.
     - Strips card references and transaction IDs: `*4A82K7`, `123456`, `REF#...`.
   - **Fuzzy & Substring Matching**: Identifies when a known Payee appears as an isolated token sequence within a noisy bank string.

---

## 5. AI Payee & Category Interpretation (Google Gemini Flash Free Tier)

1. **Role of AI**:
   - Clean merchant normalization when rule-based matching finds no reliable existing Payee.
   - Category selection strictly from the provided Master Category list.
   - Conflict resolution recommendation when a known Payee has multiple historical categories.
2. **Batching Optimization**:
   - Normalizes and groups identical descriptions before calling the LLM.
   - Unresolved transactions sent in batches (up to 20–30 items per prompt) to avoid redundant requests and stay within free-tier rate limits.
3. **Structured JSON Output**:
   Every AI classification must return structured JSON:
   ```json
   {
     "results": [
       {
         "id": "item_1",
         "payee": "Joe's Pizza",
         "category": "Dining",
         "payee_is_new": true,
         "category_is_new": false,
         "confidence": "high"
       }
     ]
   }
   ```
4. **Strict Category Constraint**:
   - The AI must select the category *only* from the provided Master Category list.
   - If no category fits, it must return `"category": "TBD"`.
   - The AI is forbidden from inventing new category names.

---

## 6. Review & Editing Screen (Web UI)

1. **Table Presentation**:
   - Shows all original transaction columns alongside the new `Payee` and `Category` columns.
   - Visual highlighting:
     - **New Payee**: Highlighted in **red text / red badge**.
     - **New Category assignment**: Highlighted in **red text / red badge**.
     - **TBD Category**: Bold warning badge requiring resolution.
     - **Conflict Warning**: Indicator when a Payee has multiple prior categories.
2. **Sorting & Filtering**:
   - Sort by any column (Date, Amount, Payee, Category, Status).
   - Quick Filter Pills: `All`, `Needs Attention (TBD / Low Confidence)`, `New Payees`, `New Categories`, `Conflicts`.
   - Text search across Description, Payee, Category.
3. **Inline Autocomplete & Editing**:
   - **Payee**: Inline editable input with live autocomplete matching known Master Payees.
   - **Category**: Searchable dropdown showing all valid KMyMoney categories + `TBD`.
   - Instant keyboard navigation for swift manual review.

---

## 7. Export Validation & Safety Mechanism

1. **Export Button**:
   - Provides an "Export CSV" action.
2. **Strict Validation**:
   - Verifies all transactions have a valid Payee and Category.
   - **ZERO TBD TOLERANCE**: If any row has `Category = "TBD"` or is blank, the export is **blocked** and a warning dialog displays the exact rows needing manual correction.
3. **Export CSV Structure**:
   - Preserves original columns, column order, date/amount formats, and identifiers untouched.
   - Appends `Payee` and `Category` columns.
   - Default filename: `<original_filename>_categorized.csv`.
   - Triggered via native browser file download.
4. **Master List Update (Post-Export Safety)**:
   - The Category and Payee list CSV is **NEVER modified during preview or AI processing**.
   - It is updated **only after a successful export**.
   - Newly approved Payees are merged with existing Payees, deduplicated, and sorted alphabetically A–Z.
   - Atomic file write ensures no data corruption.

---

## 8. Privacy & Financial Data Security
- In-memory session processing: Transaction data is not permanently stored on disk.
- Minimal payload to LLM: Only sanitized merchant descriptions are sent to Google Gemini (no account numbers, balances, dates, or card numbers).
- API keys kept server-side in `.env` / configuration.

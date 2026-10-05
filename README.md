# AI Transaction Categorization Web App

A web application for automatically categorizing bank/credit-card transactions for KMyMoney using AI (Google Gemini Flash) and existing transaction history.

## Features

- **Import Transaction CSV**: Upload bank/credit-card transaction CSV files with automatic delimiter and column detection
- **KMyMoney Integration**: Supports KMyMoney report export format and standard CSV formats
- **Smart Payee Matching**: Multi-stage matching engine (exact, normalized, fuzzy) to maximize reuse of existing payees
- **AI-Powered Classification**: Uses Google Gemini Flash (free tier) to identify new payees and suggest categories
- **Interactive Review UI**: Edit transactions with autocomplete, filter by status, and sort by any column
- **Visual Highlights**: Red highlighting for new payees and categories requiring attention
- **Export Validation**: Blocks export if any transactions have TBD or missing categories
- **Master List Updates**: Automatically updates the Category & Payee list CSV after successful export (deduplicated & sorted A-Z)

## Architecture

- **Backend**: FastAPI (Python 3.14+)
  - CSV parsers for KMyMoney reports and standard formats
  - Multi-stage matching engine with regex normalization and fuzzy matching
  - Google Gemini Flash AI service with batching
  - In-memory session processing (no sensitive data persisted)
- **Frontend**: React + Vite + Tailwind CSS
  - Interactive transaction review table
  - Real-time filtering and sorting
  - Inline editing with visual feedback

## Prerequisites

- Python 3.14+
- Node.js 18+
- Google Gemini API key (free tier available at https://makersuite.google.com/app/apikey)

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start the Backend

From the `backend` directory:
```bash
python main.py
```

The FastAPI server will start on `http://127.0.0.1:8000`

### Start the Frontend

From the `frontend` directory (in a new terminal):
```bash
npm run dev
```

The React app will open at `http://localhost:5173`

## Usage

1. **Configure API Key**: Click "Show Configuration" and enter your Gemini API key
2. **Load Reference Files**: Upload your Transaction History CSV and Category & Payee List CSV
   - Transaction History: KMyMoney report export or standard CSV with Payee/Category mappings
   - Category & Payee List: CSV with columns "Category name" and "Payee name"
3. **Upload Transactions**: Upload your bank/credit-card transaction CSV
4. **Process**: Click "Process Transactions with AI" to run the classification pipeline
5. **Review**: Review the results in the table:
   - Red highlighting indicates new payees or categories
   - Yellow highlighting indicates TBD categories requiring manual input
   - Orange badges indicate conflicts (payee with multiple historical categories)
   - Use filters to focus on transactions needing attention
6. **Edit**: Manually correct payees and categories as needed
7. **Export**: Click "Export CSV" to download the categorized transactions
   - The master Category & Payee list will be automatically updated with new payees

## File Formats

### Transaction History CSV

Supports KMyMoney report export format:
```
Report: Transactions by Payee (Customized),,
1/1/2026 through 10/2/2026,,
Payee and Date,Category,Amount
0860_YVR_Coastal_News,,
8/3/2026,Gifts,-3.14
Total 0860_YVR_Coastal_News,,-3.14
```

Or standard tabular format (`Date, Payee, Category, Amount`)

### Category & Payee List CSV

Two-column CSV:
```
Category name,Payee name
Auto:Fuel,
Auto:Maintenance,
Dining,
Groceries,
,Amazon
,Netflix
```

### Transaction CSV

Any bank/credit-card export format. The app auto-detects:
- Delimiter (comma, semicolon, tab)
- Column headers (Date, Description, Amount, etc.)

## Privacy & Security

- Transaction data is processed in-memory only
- Only sanitized merchant descriptions are sent to the AI (no account numbers, balances, or card numbers)
- API keys are stored server-side in `.env`
- No data is permanently stored unless explicitly saved via export

## Troubleshooting

**Backend won't start**: Ensure Python 3.14+ is installed and dependencies are installed with `pip install -r requirements.txt`

**Frontend won't connect**: Ensure the FastAPI backend is running on `http://127.0.0.1:8000`

**Gemini API errors**: Verify your API key is valid and has access to the Gemini Flash model

**CORS errors**: The backend includes CORS middleware to allow requests from the frontend

## Development

### Backend Structure
- `backend/parsers/`: CSV parsers for history, master list, and transactions
- `backend/matching/`: String normalizer and payee/category matching engine
- `backend/ai/`: Gemini Flash AI service
- `backend/main.py`: FastAPI application and API endpoints

### Frontend Structure
- `frontend/src/App.jsx`: Main React application
- `frontend/src/index.css`: Tailwind CSS imports
- `frontend/tailwind.config.js`: Tailwind configuration

## License

This project is for personal use with KMyMoney.

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Set, Any
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import shutil
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Import parsers and services
from parsers.history_parser import HistoryParser
from parsers.master_list import MasterListParser
from parsers.transaction_parser import TransactionParser
from matching.normalizer import StringNormalizer
from ai.openrouter_service import OpenRouterService, OpenRouterClassificationError

# Default paths - use .env if set, otherwise fall back to data/ folder
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HISTORY_PATH = os.getenv('DEFAULT_HISTORY_PATH') or str(BASE_DIR / "data" / "Transactions history.csv")
DEFAULT_MASTER_LIST_PATH = os.getenv('DEFAULT_MASTER_LIST_PATH') or str(BASE_DIR / "data" / "Category and Payee list.csv")


class SessionState:
    def __init__(self):
        self.history_data: Optional[Dict] = None
        self.master_list_data: Optional[Dict] = None
        self.transactions: Optional[List[Dict]] = None
        self.transaction_parser: Optional[TransactionParser] = None
        self.processed_transactions: Optional[List[Dict]] = None
        self.original_filename: str = "transactions"
        self.history_path: str = DEFAULT_HISTORY_PATH
        self.master_list_path: str = DEFAULT_MASTER_LIST_PATH
        self.openrouter_api_key: Optional[str] = os.getenv('OPENROUTER_API_KEY')

    def get_all_payees(self) -> List[str]:
        payees = set()
        if self.history_data and 'all_payees' in self.history_data:
            payees.update(self.history_data['all_payees'])
        if self.master_list_data and 'payees' in self.master_list_data:
            payees.update(self.master_list_data['payees'])
        return sorted(list(payees))

    def get_all_categories(self) -> List[str]:
        categories = set()
        if self.history_data and 'all_categories' in self.history_data:
            categories.update(self.history_data['all_categories'])
        if self.master_list_data and 'categories' in self.master_list_data:
            categories.update(self.master_list_data['categories'])
        return sorted(list(categories))


session = SessionState()


def load_defaults_into_session():
    """Auto-load reference files on startup if available."""
    # 1. Transaction History
    hist_path = session.history_path
    if Path(hist_path).exists():
        try:
            session.history_data = HistoryParser(hist_path).parse()
            print(f"Loaded history from {hist_path}: {session.history_data['total_payees']} payees, {session.history_data['total_categories']} categories")
        except Exception as e:
            print(f"Error loading default history from {hist_path}: {e}")
    else:
        print(f"History file not found at: {hist_path}")

    # 2. Category and Payee list
    ml_path = session.master_list_path
    if Path(ml_path).exists():
        try:
            session.master_list_data = MasterListParser(ml_path).parse()
            print(f"Loaded master list from {ml_path}: {session.master_list_data['total_payees']} payees, {session.master_list_data['total_categories']} categories")
        except Exception as e:
            print(f"Error loading default master list from {ml_path}: {e}")
    else:
        print(f"Master list file not found at: {ml_path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_defaults_into_session()
    yield


app = FastAPI(title="AI Transaction Categorization API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ColumnMapping(BaseModel):
    date_col: Optional[str] = None
    description_col: Optional[str] = None
    amount_col: Optional[str] = None


class TransactionUpdate(BaseModel):
    index: int
    payee: Optional[str] = None
    category: Optional[str] = None


# Endpoints
@app.get("/api/config")
async def get_config():
    """Get current configuration status, available payees, and categories."""
    all_payees = session.get_all_payees()
    all_categories = session.get_all_categories()

    return {
        "openrouter_api_key_configured": bool(session.openrouter_api_key and session.openrouter_api_key.strip()),
        "history_loaded": session.history_data is not None,
        "master_list_loaded": session.master_list_data is not None,
        "history_path": session.history_path,
        "master_list_path": session.master_list_path,
        "total_payees": len(all_payees),
        "total_categories": len(all_categories),
        "all_payees": all_payees,
        "all_categories": all_categories,
        "has_transactions": session.transactions is not None and len(session.transactions) > 0,
        "total_transactions": len(session.transactions) if session.transactions else 0,
        "has_processed": session.processed_transactions is not None and len(session.processed_transactions) > 0,
    }


@app.post("/api/config")
async def update_config(
    openrouter_api_key: Optional[str] = Form(None),
    history_path: Optional[str] = Form(None),
    master_list_path: Optional[str] = Form(None)
):
    """Update configuration and reload files if paths changed."""
    if openrouter_api_key is not None:
        session.openrouter_api_key = openrouter_api_key.strip()

    if history_path and history_path != session.history_path:
        session.history_path = history_path
        if Path(history_path).exists():
            session.history_data = HistoryParser(history_path).parse()

    if master_list_path and master_list_path != session.master_list_path:
        session.master_list_path = master_list_path
        if Path(master_list_path).exists():
            session.master_list_data = MasterListParser(master_list_path).parse()

    return {"status": "success"}


@app.post("/api/reference/load")
async def load_reference_files(
    history_file: Optional[UploadFile] = File(None),
    master_list_file: Optional[UploadFile] = File(None)
):
    """Load or re-load reference files (Transaction History and Category/Payee list)."""
    try:
        data_dir = BASE_DIR / "data"
        data_dir.mkdir(exist_ok=True)

        if history_file and history_file.filename:
            save_path = data_dir / history_file.filename
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(history_file.file, f)
            session.history_path = str(save_path)
            session.history_data = HistoryParser(session.history_path).parse()
        elif Path(session.history_path).exists():
            session.history_data = HistoryParser(session.history_path).parse()

        if master_list_file and master_list_file.filename:
            save_path = data_dir / master_list_file.filename
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(master_list_file.file, f)
            session.master_list_path = str(save_path)
            session.master_list_data = MasterListParser(session.master_list_path).parse()
        elif Path(session.master_list_path).exists():
            session.master_list_data = MasterListParser(session.master_list_path).parse()

        return {
            "status": "success",
            "history_loaded": session.history_data is not None,
            "master_list_loaded": session.master_list_data is not None,
            "total_payees": len(session.get_all_payees()),
            "total_categories": len(session.get_all_categories()),
            "all_payees": session.get_all_payees(),
            "all_categories": session.get_all_categories(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions/upload")
async def upload_transactions(file: UploadFile = File(...)):
    """Upload and parse transaction CSV with column detection."""
    try:
        data_dir = BASE_DIR / "data"
        data_dir.mkdir(exist_ok=True)

        session.original_filename = Path(file.filename).stem if file.filename else "transactions"
        save_path = data_dir / file.filename

        with open(save_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        parser = TransactionParser(str(save_path))
        result = parser.parse()

        session.transactions = result['rows']
        session.transaction_parser = parser
        session.processed_transactions = None

        return {
            "status": "success",
            "filename": file.filename,
            "delimiter": result['delimiter'],
            "headers": result['headers'],
            "date_col": result['date_col'],
            "description_col": result['description_col'],
            "amount_col": result['amount_col'],
            "total_rows": result['total_rows'],
            "sample_rows": result['rows'][:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions/map-columns")
async def map_columns(mapping: ColumnMapping):
    """Update column mappings for transactions."""
    if session.transaction_parser:
        session.transaction_parser.update_column_mapping(
            mapping.date_col,
            mapping.description_col,
            mapping.amount_col
        )
        return {
            "status": "success",
            "date_col": session.transaction_parser.date_col,
            "description_col": session.transaction_parser.description_col,
            "amount_col": session.transaction_parser.amount_col
        }
    raise HTTPException(status_code=400, detail="No transaction file uploaded yet")


# Pure helper functions for transaction processing
def _build_exact_match_item(
    idx: int,
    original: Dict[str, Any],
    raw_desc: str,
    amount: str,
    date: str,
    payee: str,
    category: str
) -> Dict[str, Any]:
    return {
        'index': idx,
        'original': original,
        'description': raw_desc,
        'amount': amount,
        'date': date,
        'payee': payee,
        'category': category,
        'payee_is_new': False,
        'category_is_new': False,
        'has_conflict': False,
        'conflict_options': [],
        'confidence': 'high',
        'match_method': 'exact_fast_path'
    }


def _build_pending_item(
    idx: int,
    original: Dict[str, Any],
    raw_desc: str,
    amount: str,
    date: str,
    payee: str,
    is_new: bool,
    conflict_options: List[str]
) -> Dict[str, Any]:
    return {
        'index': idx,
        'original': original,
        'description': raw_desc,
        'amount': amount,
        'date': date,
        'payee': payee,
        'category': 'TBD',
        'payee_is_new': is_new,
        'category_is_new': False,
        'has_conflict': False,
        'conflict_options': conflict_options,
        'confidence': 'low',
        'match_method': 'pending_ai'
    }


def _distribute_ai_results(
    processed: List[Dict[str, Any]],
    ai_candidate_groups: Dict[str, List[int]],
    group_keys: List[str],
    ai_results: Dict[str, Dict[str, Any]],
    payee_to_categories: Dict[str, List[str]]
) -> None:
    """Map AI batch results back to corresponding transaction records."""
    for g_idx_str, ai_data in ai_results.items():
        try:
            g_idx = int(g_idx_str)
            if g_idx >= len(group_keys):
                continue
            target_key = group_keys[g_idx]
            for tx_idx in ai_candidate_groups[target_key]:
                matched_payee = ai_data.get('payee') or processed[tx_idx]['payee']
                assigned_category = ai_data.get('category') or 'TBD'
                payee_is_new = ai_data.get('payee_is_new', True)
                category_is_new = ai_data.get('category_is_new', False)
                confidence = ai_data.get('confidence', 'medium')

                history_cats = payee_to_categories.get(matched_payee, [])
                has_conflict = len(history_cats) > 1

                # If payee has exactly 1 established historical category, guarantee its assignment
                if history_cats and len(history_cats) == 1:
                    assigned_category = history_cats[0]

                processed[tx_idx].update({
                    'payee': matched_payee,
                    'category': assigned_category,
                    'payee_is_new': payee_is_new,
                    'category_is_new': category_is_new,
                    'has_conflict': has_conflict,
                    'conflict_options': history_cats if has_conflict else [],
                    'confidence': confidence,
                    'match_method': 'openrouter_llm'
                })
        except Exception as e:
            print(f"Error distributing AI result for group {g_idx_str}: {e}")


@app.post("/api/transactions/process")
async def process_transactions():
    """
    Process transactions with AI-First Matching and real-time progress streaming:
    Streams SSE events with percent completion (0-100%) and status messages.
    """
    if not session.transactions or not session.transaction_parser:
        raise HTTPException(status_code=400, detail="No transactions loaded. Please upload a transaction CSV first.")

    # Ensure reference data is loaded
    if not session.history_data and not session.master_list_data:
        load_defaults_into_session()

    all_master_payees = session.get_all_payees()
    all_master_categories = session.get_all_categories()
    payee_to_categories = session.history_data.get('payee_to_categories', {}) if session.history_data else {}
    payee_category_stats = session.history_data.get('payee_category_stats', {}) if session.history_data else {}

    master_payees_exact = set(all_master_payees)
    master_payees_lower = {p.lower(): p for p in all_master_payees}

    desc_col = session.transaction_parser.description_col or 'description'
    amount_col = session.transaction_parser.amount_col or 'amount'
    date_col = session.transaction_parser.date_col or 'date'

    has_api_key = bool(session.openrouter_api_key and session.openrouter_api_key.strip())

    async def event_generator():
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()

        def push_event(data):
            loop.call_soon_threadsafe(queue.put_nowait, data)

        def progress_cb(current_chunk, total_chunks, msg):
            pct = 25 + int((current_chunk / total_chunks) * 65)
            push_event({
                "type": "progress",
                "percent": min(pct, 95),
                "message": msg
            })

        def run_sync_processing():
            try:
                push_event({
                    "type": "progress",
                    "percent": 5,
                    "message": "Initializing Master Payees & Categories..."
                })

                processed: List[Dict[str, Any]] = []
                ai_candidate_groups: Dict[str, List[int]] = {}

                for idx, tx in enumerate(session.transactions):
                    raw_desc = tx.get(desc_col, '') if desc_col in tx else ''
                    amount = tx.get(amount_col, '') if amount_col in tx else ''
                    date = tx.get(date_col, '') if date_col in tx else ''
                    trimmed = raw_desc.strip()

                    # Fast-path: single historical category match
                    exact_match = None
                    if trimmed in master_payees_exact:
                        exact_match = trimmed
                    elif trimmed.lower() in master_payees_lower:
                        exact_match = master_payees_lower[trimmed.lower()]

                    if exact_match and exact_match in payee_to_categories and len(payee_to_categories[exact_match]) == 1:
                        single_cat = payee_to_categories[exact_match][0]
                        processed.append(_build_exact_match_item(
                            idx, tx, raw_desc, amount, date, exact_match, single_cat
                        ))
                    else:
                        conflict_options = payee_to_categories.get(exact_match, []) if exact_match else []
                        processed.append(_build_pending_item(
                            idx, tx, raw_desc, amount, date, exact_match or trimmed, exact_match is None, conflict_options
                        ))
                        if trimmed not in ai_candidate_groups:
                            ai_candidate_groups[trimmed] = []
                        ai_candidate_groups[trimmed].append(idx)

                exact_count = len(processed) - sum(len(v) for v in ai_candidate_groups.values())
                push_event({
                    "type": "progress",
                    "percent": 20,
                    "message": f"{exact_count} exact matches found. Preparing {len(ai_candidate_groups)} unique items for AI..."
                })

                # Check API key requirement
                if ai_candidate_groups and not has_api_key:
                    raise OpenRouterClassificationError(
                        "OpenRouter API Key is not configured. Please add your OPENROUTER_API_KEY in Settings or .env file to run AI categorization."
                    )

                # AI-First Classification using OpenRouter
                if has_api_key and ai_candidate_groups:
                    group_keys = list(ai_candidate_groups.keys())
                    batch_items = [
                        {
                            "id": str(g_idx),
                            "description": processed[ai_candidate_groups[g_key][0]]['description'],
                            "amount": processed[ai_candidate_groups[g_key][0]]['amount'],
                            "date": processed[ai_candidate_groups[g_key][0]]['date']
                        }
                        for g_idx, g_key in enumerate(group_keys)
                    ]

                    openrouter = OpenRouterService(session.openrouter_api_key)
                    ai_results = openrouter.classify_batch(
                        batch_items,
                        master_payees=all_master_payees,
                        master_categories=all_master_categories,
                        payee_to_categories=payee_to_categories,
                        payee_category_stats=payee_category_stats,
                        progress_callback=progress_cb
                    )
                    openrouter.close()

                    push_event({
                        "type": "progress",
                        "percent": 95,
                        "message": "Mapping AI classifications and verifying historical categories..."
                    })

                    _distribute_ai_results(
                        processed,
                        ai_candidate_groups,
                        group_keys,
                        ai_results,
                        payee_to_categories
                    )

                session.processed_transactions = processed

                push_event({
                    "type": "complete",
                    "percent": 100,
                    "total_processed": len(processed),
                    "ai_used": has_api_key and len(ai_candidate_groups) > 0,
                    "transactions": processed
                })

            except OpenRouterClassificationError as e:
                push_event({"type": "error", "detail": str(e)})
            except Exception as e:
                push_event({"type": "error", "detail": f"AI categorization failed: {str(e)}"})
            finally:
                push_event(None)

        # Run worker in background thread so it doesn't block FastAPI event loop
        asyncio.create_task(asyncio.to_thread(run_sync_processing))

        # Stream events to client as they arrive
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/transactions/update")
async def update_transaction(update: TransactionUpdate):
    """Manually update a single transaction's payee or category."""
    if not session.processed_transactions:
        raise HTTPException(status_code=400, detail="No processed transactions")

    idx = update.index
    if idx < 0 or idx >= len(session.processed_transactions):
        raise HTTPException(status_code=400, detail="Invalid transaction index")

    all_payees = set(session.get_all_payees())
    all_categories = set(session.get_all_categories())

    if update.payee is not None:
        p_val = update.payee.strip()
        session.processed_transactions[idx]['payee'] = p_val
        session.processed_transactions[idx]['payee_is_new'] = p_val not in all_payees

    if update.category is not None:
        c_val = update.category.strip()
        session.processed_transactions[idx]['category'] = c_val
        session.processed_transactions[idx]['category_is_new'] = c_val not in all_categories and c_val != 'TBD'

    return {
        "status": "success",
        "transaction": session.processed_transactions[idx]
    }


@app.post("/api/transactions/export")
async def export_transactions():
    """
    Export processed transactions as CSV:
    1. Validation: Block export if ANY transaction has Category='TBD' or empty.
    2. Format: Original columns preserved in original order + Payee + Category.
    3. Update master list: Newly approved payees added, deduplicated, sorted A-Z.
    """
    if not session.processed_transactions or not session.transaction_parser:
        raise HTTPException(status_code=400, detail="No processed transactions to export")

    # Strict Validation: Check for TBD or missing categories
    invalid_rows = [
        tx['index'] + 1
        for tx in session.processed_transactions
        if not tx.get('category') or tx.get('category').strip().upper() == 'TBD'
    ]

    if invalid_rows:
        count = len(invalid_rows)
        sample = invalid_rows[:5]
        sample_str = ", ".join(f"#{r}" for r in sample)
        more_str = f" and {count - len(sample)} more" if count > len(sample) else ""
        raise HTTPException(
            status_code=400,
            detail=f"Cannot export: {count} transaction(s) have 'TBD' or missing category (rows: {sample_str}{more_str}). Please assign a valid category to all transactions before exporting."
        )

    try:
        import csv
        from io import StringIO

        output = StringIO()
        # Preserve original column order and append Payee and Category
        headers = list(session.transaction_parser.headers)
        if 'Payee' not in headers:
            headers.append('Payee')
        if 'Category' not in headers:
            headers.append('Category')

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for tx in session.processed_transactions:
            row = dict(tx['original'])
            row['Payee'] = tx['payee']
            row['Category'] = tx['category']
            writer.writerow(row)

        csv_content = output.getvalue()

        master_path = Path(DEFAULT_MASTER_LIST_PATH)
        if master_path.exists():
            master_parser = MasterListParser(str(master_path))
            master_parser.parse()
            used_payees = {tx['payee'] for tx in session.processed_transactions if tx.get('payee') and tx['payee'].upper() != 'TBD'}
            used_categories = {tx['category'] for tx in session.processed_transactions if tx.get('category') and tx['category'].upper() != 'TBD'}
            new_payees = sorted(used_payees - master_parser.payees, key=str.casefold)
            new_categories = sorted(used_categories - master_parser.categories, key=str.casefold)
            if new_payees or new_categories:
                master_parser.update(new_payees, new_categories)
                session.master_list_data = master_parser.parse()
                print(f"Master list updated: {len(new_payees)} new payees, {len(new_categories)} new categories.")

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig', newline='')
        temp_file.write(csv_content)
        temp_file.close()

        export_filename = f"{session.original_filename}_categorized.csv"

        return FileResponse(
            temp_file.name,
            media_type='text/csv',
            filename=export_filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

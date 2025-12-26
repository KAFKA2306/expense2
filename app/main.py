from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import pandas as pd
import os
from pathlib import Path

from app.services.expense_analysis import ExpenseAnalysisService


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)

data_dir = Path(__file__).parent.parent / "data"
app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

analysis_service = ExpenseAnalysisService()


def load_transactions(exclude_transfer_and_income: bool = True):
    csv_path = data_dir / "transactions.csv"
    df = pd.read_csv(csv_path)
    df = df[~((df["category"] == "振替") | (df["type"] == "income"))]
    df = df.sort_values("date", ascending=False)
    df = df.fillna("")
    return df.to_dict("records")


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    transactions = load_transactions()[:10]
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"transactions": transactions}
    )


@app.get("/transactions", response_class=HTMLResponse)
async def get_transactions(request: Request):
    transactions = load_transactions()
    return templates.TemplateResponse(
        request=request,
        name="partials/transaction_list.html",
        context={"transactions": transactions},
    )


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    summary = analysis_service.get_summary()
    return templates.TemplateResponse(
        request=request,
        name="analysis.html",
        context={"analysis": summary},
    )


@app.get("/api/analysis/summary")
async def api_analysis_summary():
    return JSONResponse(content=analysis_service.get_summary())


@app.post("/sync", response_class=HTMLResponse)
async def sync_data(request: Request):
    return """
    <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Success!</strong>
        <span class="block sm:inline">Data synchronization started.</span>
    </div>
    """

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from sqlmodel import Session, select
import os

from app.db import create_db_and_tables, get_session
from app.models import Transaction


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, session: Session = Depends(get_session)):
    transactions = session.exec(
        select(Transaction).order_by(Transaction.date.desc()).limit(10)
    ).all()
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"transactions": transactions}
    )


@app.get("/transactions", response_class=HTMLResponse)
async def get_transactions(request: Request, session: Session = Depends(get_session)):
    transactions = session.exec(
        select(Transaction).order_by(Transaction.date.desc()).limit(50)
    ).all()
    return templates.TemplateResponse(
        request=request,
        name="partials/transaction_list.html",
        context={"transactions": transactions},
    )


@app.post("/sync", response_class=HTMLResponse)
async def sync_data(request: Request):
    return """
    <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Success!</strong>
        <span class="block sm:inline">Data synchronization started.</span>
    </div>
    """

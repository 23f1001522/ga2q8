from fastapi import FastAPI
from pydantic import BaseModel
import re

app = FastAPI()


class InvoiceRequest(BaseModel):
    text: str


class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):

    text = req.text

    vendor = ""
    amount = 0.0
    currency = ""
    date = ""

    # Date: 2026-MM-DD
    m = re.search(r"2026-\d{2}-\d{2}", text)
    if m:
        date = m.group()

    # Currency
    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    if m:
        currency = m.group().upper()

    # Amount
    m = re.search(
        r"(?:Total|Amount|Due|Payable|Total Due)[^\d]*([0-9]+(?:\.[0-9]{1,2})?)",
        text,
        re.I,
    )
    if m:
        amount = float(m.group(1))
    else:
        m = re.search(r"([0-9]+(?:\.[0-9]{1,2})?)", text)
        if m:
            amount = float(m.group(1))

    # Vendor
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if not re.search(
            r"(invoice|date|amount|due|total|currency|bill|payment)",
            line,
            re.I,
        ):
            vendor = line
            break

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date,
    )
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

    text = req.text or ""

    vendor = ""
    amount = 0.0
    currency = ""
    date = ""

    # ---------------- DATE ----------------

    m = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    if m:
        date = m.group()

    # ---------------- CURRENCY ----------------

    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    if m:
        currency = m.group(1).upper()

    # ---------------- AMOUNT ----------------

    amount_patterns = [
        r"(?:Total\s*Due|Amount\s*Due|Grand\s*Total|Total|Amount|Payable)\D*([0-9]+(?:\.[0-9]{1,2})?)",
        r"\b(?:USD|EUR|GBP)\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"([0-9]+(?:\.[0-9]{1,2})?)",
    ]

    for pattern in amount_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            amount = float(m.group(1))
            break

    # ---------------- VENDOR ----------------

    vendor_patterns = [

        r"Vendor\s*:\s*([^\n]+)",

        r"Supplier\s*:\s*([^\n]+)",

        r"From\s*:\s*([^\n]+)",

        r"Invoice\s+from\s+([^\n]+)",

        r"(Acme-[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9&.,'\-]+)*)",

        r"([A-Z][A-Za-z0-9&.,'\- ]+(?:Ltd\.?|Limited|LLC|Inc\.?|Corporation|Corp\.?|Industries|Company|Co\.?))",
    ]

    for pattern in vendor_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            vendor = m.group(1).strip()
            break

    # Fallback: first reasonable line
    if not vendor:
        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            if re.search(
                r"invoice|bill|date|due|total|amount|currency|payment",
                line,
                re.IGNORECASE,
            ):
                continue

            if re.fullmatch(r"[\d\W]+", line):
                continue

            vendor = line
            break

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date,
    )

"""One local worker; PostgreSQL row locks permit safe concurrent consumers.

The transaction stays open during the small PDF write. A crashed process releases
its lock, leaving the job queued for the next attempt. The filename is idempotent.
"""

import logging
import os
import time
from pathlib import Path
from xml.sax.saxutils import escape

from app.db import Base, Client, Job, Session, engine
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
PDF_DIR = Path(os.environ.get("PDF_DIR", "./pdfs"))


def process_one():
    with Session.begin() as db:
        job = db.scalar(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return False
        client = db.get(Client, job.client_id)
        try:
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{job.id}.pdf"
            temp = PDF_DIR / f"{job.id}.tmp"
            styles = getSampleStyleSheet()
            styles["Title"].textColor = colors.HexColor("#137f70")
            doc = SimpleDocTemplate(str(temp))
            doc.build(
                [
                    Paragraph("WealthHub | Welcome", styles["Title"]),
                    Spacer(1, 24),
                    Paragraph(f"Hello {escape(client.name)},", styles["Heading2"]),
                    Paragraph("Your mock onboarding is complete.", styles["Normal"]),
                    Spacer(1, 16),
                    Paragraph(f"Email: {escape(client.email)}", styles["Normal"]),
                    Paragraph(f"Risk profile: {escape(client.risk)}", styles["Normal"]),
                    Spacer(1, 24),
                    Paragraph(
                        "PORTFOLIO DEMONSTRATION ONLY. Synthetic data. This document is not financial advice and does not create an account with a financial institution.",
                        styles["Normal"],
                    ),
                ]
            )
            temp.replace(PDF_DIR / filename)
            job.pdf = filename
            job.status = "completed"
        except Exception:
            logging.exception("PDF generation failed for job %s", job.id)
            job.status = "failed"
            job.error = "PDF generation failed. Check worker logs."
        return True


def main():
    Base.metadata.create_all(engine)
    while True:
        try:
            if not process_one():
                time.sleep(2)
        except Exception:
            logging.exception("Worker database error; retrying")
            time.sleep(3)


if __name__ == "__main__":
    main()

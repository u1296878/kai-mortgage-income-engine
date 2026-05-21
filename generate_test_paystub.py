from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


output_path = Path("test_documents") / "paystub_fake_filled.pdf"
c = canvas.Canvas(str(output_path), pagesize=letter)

c.drawString(50, 740, "Acme Corp Pay Stub")
c.drawString(50, 700, "Pay Date: 2024-05-15")
c.drawString(50, 670, "Pay Frequency: Biweekly")
c.drawString(50, 640, "Income Type: Salary")
c.drawString(50, 590, "Gross Pay:")
c.drawString(300, 590, "$3,269.23")
c.drawString(50, 560, "YTD Gross:")
c.drawString(300, 560, "$42,500.00")
c.drawString(50, 530, "Bonus YTD:")
c.drawString(300, 530, "$2,500.00")

c.save()
print(f"Done: {output_path}")

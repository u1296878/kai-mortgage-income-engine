from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


output_path = Path("test_documents") / "tax_return_fake_filled.pdf"
c = canvas.Canvas(str(output_path), pagesize=letter)

c.drawString(50, 740, "Form 1040 U.S. Individual Income Tax Return 2023")
c.drawString(50, 710, "Filing Status: Single")
c.drawString(50, 650, "1a Total amount from Form(s) W-2, box 1")
c.drawString(500, 650, "85000.00")
c.drawString(50, 610, "9 Total income")
c.drawString(500, 610, "90000.00")
c.drawString(50, 570, "11 Adjusted gross income")
c.drawString(500, 570, "79000.00")

c.showPage()
c.drawString(50, 740, "Schedule C Profit or Loss From Business")
c.drawString(50, 680, "31 Net profit or loss")
c.drawString(500, 680, "5000.00")

c.save()
print(f"Done: {output_path}")

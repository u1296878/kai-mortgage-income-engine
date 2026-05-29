from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


output_path = Path("test_documents") / "rental_fake_filled.pdf"
c = canvas.Canvas(str(output_path), pagesize=letter)

c.drawString(50, 740, "Schedule E Supplemental Income and Loss 2023")
c.drawString(50, 700, "Property Address: 123 Sample Rental Ave")
c.drawString(50, 640, "3 Rents received")
c.drawString(500, 640, "24000.00")
c.drawString(50, 600, "20 Total expenses")
c.drawString(500, 600, "6000.00")
c.drawString(50, 560, "21 Income or loss")
c.drawString(500, 560, "18000.00")

c.save()
print(f"Done: {output_path}")

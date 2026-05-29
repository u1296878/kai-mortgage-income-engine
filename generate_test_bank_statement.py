from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


output_path = Path("test_documents") / "bank_statement_fake_filled.pdf"
c = canvas.Canvas(str(output_path), pagesize=letter)

c.drawString(50, 740, "Sample Bank")
c.drawString(50, 710, "Account Holder: Sample Borrower")
c.drawString(50, 690, "Account Number: ****1234")
c.drawString(50, 660, "Statement Period: 2024-01-01 to 2024-03-31")
c.drawString(50, 620, "Beginning Balance 1200.00")
c.drawString(50, 580, "2024-01-15 Payroll Deposit ACME Corp")
c.drawString(500, 580, "5000.00")
c.drawString(50, 550, "2024-01-20 Debit Card Purchase Grocery Store")
c.drawString(500, 550, "-125.00")
c.drawString(50, 520, "2024-02-01 ATM Withdrawal")
c.drawString(500, 520, "-200.00")
c.drawString(50, 490, "2024-02-15 Direct Deposit ACME Corp")
c.drawString(500, 490, "5000.00")
c.drawString(50, 460, "2024-03-15 ACH Credit Payroll")
c.drawString(500, 460, "5000.00")
c.drawString(50, 420, "Ending Balance 16200.00")
c.drawString(50, 380, "Total Deposits and Credits")
c.drawString(500, 380, "15000.00")

c.save()
print(f"Done: {output_path}")

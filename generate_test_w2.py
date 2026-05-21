from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


c = canvas.Canvas("test_documents/w2_fake_filled.pdf", pagesize=letter)

# Employer info
c.drawString(50, 700, "Employer: Acme Corp")
c.drawString(50, 680, "EIN: 12-3456789")

# Box 1
c.drawString(50, 620, "1 Wages, tips, other compensation")
c.drawString(300, 620, "85000.00")

# Box 2
c.drawString(50, 590, "2 Federal income tax withheld")
c.drawString(300, 590, "12500.00")

# Box 3
c.drawString(50, 560, "3 Social security wages")
c.drawString(300, 560, "85000.00")

# Box 5
c.drawString(50, 530, "5 Medicare wages and tips")
c.drawString(300, 530, "85000.00")

# Tax year
c.drawString(50, 750, "W-2 Wage and Tax Statement 2023")

c.save()
print("Done: test_documents/w2_fake_filled.pdf")

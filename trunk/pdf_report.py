from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

# Create a PDF document
doc = SimpleDocTemplate("output.pdf", pagesize=letter)

# Define styles
styles = getSampleStyleSheet()
style = styles["Normal"]

# Add custom font if needed (e.g., 'Helvetica-Bold')
style.fontName = 'Helvetica-Bold'
style.fontSize = 14

# Create content
content = []
content.append(Paragraph("Hello, World with custom font!", style))

# Build the PDF
doc.build(content)


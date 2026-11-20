import fitz
from pathlib import Path

folder = Path(r"D:\FDA-repo\project_documentation\figures")

for filename in [
    "04_database_er_diagram_preview.pdf",
]:
    path = folder / filename
    doc = fitz.open(path)
    page = doc[0]

    print("\nPDF:", filename)
    print("Page size:", page.rect)
    print("Extracted text:")
    print(repr(page.get_text()[:3000]))
    print("Drawing objects:", len(page.get_drawings()))

    doc.close()

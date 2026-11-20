from pathlib import Path
import fitz

folder = Path(r"D:\FDA-repo\project_documentation\figures")
pdf_path = folder / "04_database_er_diagram_preview.pdf"
png_path = folder / "04_database_er_diagram.png"

doc = fitz.open()
page = doc.new_page(width=1600, height=1000)

navy = (0.09, 0.21, 0.36)
blue = (0.15, 0.35, 0.55)
light = (0.94, 0.97, 0.99)
dark = (0.12, 0.17, 0.23)
grey = (0.35, 0.40, 0.46)

page.draw_rect(page.rect, color=None, fill=(1, 1, 1))

page.insert_text((800, 65), "DATABASE ENTITY-RELATIONSHIP DIAGRAM",
                 fontsize=30, fontname="hebo", color=navy, align=1)
page.insert_text((800, 100),
                 "AI-Based Financial Transaction Fraud Detection and Risk Assessment System",
                 fontsize=16, fontname="helv", color=grey, align=1)

def draw_entity(x, y, w, h, title, fields):
    rect = fitz.Rect(x, y, x+w, y+h)
    page.draw_rect(rect, color=navy, fill=(1, 1, 1), width=2)
    header = fitz.Rect(x, y, x+w, y+55)
    page.draw_rect(header, color=navy, fill=navy, width=1)
    page.insert_text((x+w/2, y+36), title,
                     fontsize=23, fontname="hebo", color=(1,1,1), align=1)

    current_y = y + 92
    for label, value in fields:
        if label:
            page.insert_text((x+28, current_y), label,
                             fontsize=14, fontname="hebo", color=blue)
            page.insert_text((x+100, current_y), value,
                             fontsize=14, fontname="helv", color=dark)
        else:
            page.insert_text((x+28, current_y), value,
                             fontsize=14, fontname="helv", color=dark)
        current_y += 39

    return rect

users = [
    ("PK", "id"),
    ("", "email  VARCHAR(255)  UNIQUE"),
    ("", "full_name  VARCHAR(255)"),
    ("", "password_hash  VARCHAR(255)"),
    ("", "created_at  TIMESTAMP WITH TIME ZONE"),
]

transactions = [
    ("PK", "id"),
    ("FK", "user_id  -> users.id"),
    ("", "transaction_id  VARCHAR(100) UNIQUE"),
    ("", "amount  NUMERIC(15,2)"),
    ("", "transaction_type  VARCHAR(50)"),
    ("", "merchant_category  VARCHAR(100)"),
    ("", "location  VARCHAR(255), nullable"),
    ("", "device  VARCHAR(100), nullable"),
    ("", "transaction_date  TIMESTAMP WITH TIME ZONE"),
    ("", "status  VARCHAR(50)"),
    ("", "fraud_probability  NUMERIC(5,4), nullable"),
    ("", "risk_score  NUMERIC(5,2), nullable"),
    ("", "risk_level  VARCHAR(20), nullable"),
    ("", "created_at  TIMESTAMP WITH TIME ZONE"),
]

draw_entity(90, 230, 570, 370, "USERS", users)
draw_entity(940, 165, 570, 650, "TRANSACTIONS", transactions)

# One-to-many relationship
page.draw_line((660, 465), (940, 465), color=navy, width=3)
page.draw_line((930, 457), (940, 465), color=navy, width=3)
page.draw_line((930, 473), (940, 465), color=navy, width=3)

page.insert_text((675, 445), "1", fontsize=18, fontname="hebo", color=navy)
page.insert_text((905, 445), "N", fontsize=18, fontname="hebo", color=navy)
page.insert_text((800, 505), "One user can own many transactions",
                 fontsize=15, fontname="helv", color=grey, align=1)

page.insert_text((800, 900),
                 "PK = Primary Key     FK = Foreign Key     1:N = One-to-Many",
                 fontsize=17, fontname="hebo", color=navy, align=1)
page.insert_text((800, 935),
                 "Based on the implemented SQLAlchemy User and Transaction models",
                 fontsize=14, fontname="helv", color=grey, align=1)

doc.save(pdf_path)
pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
pix.save(png_path)
doc.close()

print("New PDF:", pdf_path)
print("New PNG:", png_path)
print("PNG dimensions:", pix.width, "x", pix.height)

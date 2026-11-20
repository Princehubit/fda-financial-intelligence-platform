from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(r"D:\FDA-repo\project_documentation")
figures = root / "figures"
sources = root / "diagram_sources"

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#334155"/>
  </marker>
  <style>
    .title{font: bold 34px Arial;fill:#17365D}
    .subtitle{font:18px Arial;fill:#475569}
    .entity{fill:#fff;stroke:#17365D;stroke-width:3;rx:12}
    .header{fill:#17365D}
    .entitytitle{font:bold 25px Arial;fill:#fff}
    .field{font:19px Arial;fill:#1e293b}
    .key{font:bold 18px Arial;fill:#17365D}
    .note{font:17px Arial;fill:#475569}
    .relation{font:bold 20px Arial;fill:#17365D}
  </style>
</defs>
<rect width="1600" height="1000" fill="#ffffff"/>
<text x="800" y="65" text-anchor="middle" class="title">DATABASE ENTITY–RELATIONSHIP DIAGRAM</text>
<text x="800" y="100" text-anchor="middle" class="subtitle">AI-Based Financial Transaction Fraud Detection and Risk Assessment System</text>

<!-- USERS ENTITY -->
<rect x="130" y="190" width="540" height="590" class="entity"/>
<path d="M142 190 H658 Q670 190 670 202 V250 H130 V202 Q130 190 142 190" class="header"/>
<text x="400" y="230" text-anchor="middle" class="entitytitle">USERS</text>

<text x="165" y="300" class="key">PK  id</text>
<text x="165" y="345" class="field">email  VARCHAR(255)  UNIQUE</text>
<text x="165" y="390" class="field">full_name  VARCHAR(255)</text>
<text x="165" y="435" class="field">password_hash  VARCHAR(255)</text>
<text x="165" y="480" class="field">created_at  TIMESTAMP WITH TIME ZONE</text>
<line x1="160" y1="510" x2="640" y2="510" stroke="#cbd5e1" stroke-width="2"/>
<text x="165" y="555" class="note">Primary key: id</text>
<text x="165" y="590" class="note">Unique email address</text>
<text x="165" y="625" class="note">One-to-many relationship with transactions</text>

<!-- TRANSACTIONS ENTITY -->
<rect x="930" y="150" width="540" height="700" class="entity"/>
<path d="M942 150 H1458 Q1470 150 1470 162 V210 H930 V162 Q930 150 942 150" class="header"/>
<text x="1200" y="190" text-anchor="middle" class="entitytitle">TRANSACTIONS</text>

<text x="965" y="255" class="key">PK  id</text>
<text x="965" y="295" class="key">FK  user_id  → users.id</text>
<text x="965" y="340" class="field">transaction_id  VARCHAR(100) UNIQUE</text>
<text x="965" y="380" class="field">amount  NUMERIC(15,2)</text>
<text x="965" y="420" class="field">transaction_type  VARCHAR(50)</text>
<text x="965" y="460" class="field">merchant_category  VARCHAR(100)</text>
<text x="965" y="500" class="field">location  VARCHAR(255), nullable</text>
<text x="965" y="540" class="field">device  VARCHAR(100), nullable</text>
<text x="965" y="580" class="field">transaction_date  TIMESTAMP WITH TIME ZONE</text>
<text x="965" y="620" class="field">status  VARCHAR(50)</text>
<text x="965" y="660" class="field">fraud_probability  NUMERIC(5,4), nullable</text>
<text x="965" y="700" class="field">risk_score  NUMERIC(5,2), nullable</text>
<text x="965" y="740" class="field">risk_level  VARCHAR(20), nullable</text>
<text x="965" y="790" class="field">created_at  TIMESTAMP WITH TIME ZONE</text>

<!-- RELATIONSHIP -->
<path d="M670 470 H930" fill="none" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
<text x="700" y="445" class="relation">1</text>
<text x="890" y="445" class="relation">N</text>
<text x="800" y="510" text-anchor="middle" class="note">owns / belongs to</text>

<!-- FOOTER -->
<text x="800" y="920" text-anchor="middle" class="subtitle">PK = Primary Key   |   FK = Foreign Key   |   1:N = One-to-Many</text>
<text x="800" y="955" text-anchor="middle" class="note">Based on the implemented SQLAlchemy User and Transaction models</text>
</svg>"""

svg_path = figures / "04_database_er_diagram.svg"
svg_path.write_text(svg, encoding="utf-8")

mermaid = """erDiagram
    USERS ||--o{ TRANSACTIONS : owns
    USERS {
        int id PK
        varchar email UK
        varchar full_name
        varchar password_hash
        datetime created_at
    }
    TRANSACTIONS {
        int id PK
        int user_id FK
        varchar transaction_id UK
        decimal amount
        varchar transaction_type
        varchar merchant_category
        varchar location
        varchar device
        datetime transaction_date
        varchar status
        decimal fraud_probability
        decimal risk_score
        varchar risk_level
        datetime created_at
    }
"""
(sources / "04_database_er_diagram.mmd").write_text(mermaid, encoding="utf-8")

ET.parse(svg_path)
print("ER diagram SVG generated and XML validated.")
print("SVG:", svg_path)
print("Mermaid source:", sources / "04_database_er_diagram.mmd")

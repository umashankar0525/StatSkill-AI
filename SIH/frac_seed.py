import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "igot_demo.db")

def create_frac_tables(cursor):
    # Additive, repeatable bootstrap: never reset learner evidence.

    # Roles Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frac_roles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            cadre TEXT NOT NULL,
            description TEXT
        )
    """)

    # Competencies Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frac_competencies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL, -- 'Domain', 'Functional', 'Behavioural'
            description TEXT
        )
    """)

    # Role-Competency Map Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frac_role_competency_map (
            role_id TEXT,
            competency_id TEXT,
            required_level INTEGER, -- 1 to 5
            FOREIGN KEY(role_id) REFERENCES frac_roles(id),
            FOREIGN KEY(competency_id) REFERENCES frac_competencies(id),
            PRIMARY KEY(role_id, competency_id)
        )
    """)

    # User Competency Profile (real scores)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competency_profiles (
            user_id TEXT,
            competency_id TEXT,
            current_level INTEGER, -- L0 assessment status through L6 proficiency
            FOREIGN KEY(competency_id) REFERENCES frac_competencies(id),
            PRIMARY KEY(user_id, competency_id)
        )
    """)

def seed_frac_data(cursor):
    # 1. Insert Competencies
    competencies = [
        ("C_SURVEY", "Survey Design & Questionnaire Formulation", "Domain", "Ability to design sample surveys and format questionnaires."),
        ("C_SAMPLING", "Multi-Stage Probability Sampling & Weighting", "Domain", "Knowledge of statistical sampling frames and methodologies."),
        ("C_NAT_ACC", "National Accounts (SNA 2008) & GVA Compilation", "Domain", "Understanding macroeconomic indicators and GVA."),
        ("C_PRICE", "Price Statistics (CPI & WPI)", "Domain", "Compilation of consumer and wholesale price indices."),
        ("C_PYTHON", "Python Programming (Pandas, NumPy)", "Functional", "Ability to process data using Python."),
        ("C_AI_ML", "Machine Learning & AI", "Functional", "Application of ML models, NLP, and anomaly detection."),
        ("C_DATAVIZ", "Data Visualization (Power BI, Interactive Dashboards)", "Functional", "Presenting data insights visually."),
        ("C_R", "R Programming", "Functional", "Statistical computing and graphics in R."),
        ("C_SQL", "SQL & Database Management", "Functional", "Querying and managing structured databases."),
        ("C_GIS", "GIS & Spatial Data Analysis", "Functional", "Mapping and geospatial statistics."),
        ("C_CYBER", "Cybersecurity & CERT-In Guidelines", "Functional", "Protecting digital assets and maintaining data security."),
        ("C_DPDP", "Data Privacy & DPDP Act", "Functional", "Ensuring compliance with data protection laws."),
        ("C_SDG", "SDG Indicators", "Domain", "Tracking and monitoring Sustainable Development Goals."),
        ("C_ETHICS", "UN Fundamental Principles of Official Statistics & Ethics", "Behavioural", "Maintaining professional integrity in statistics."),
        ("C_LEADERSHIP", "Leadership & Strategic Planning", "Behavioural", "Guiding teams and long-term organizational strategy."),
        ("C_CAPACITY", "Capacity Building & Training", "Behavioural", "Developing skills in others and managing training programs."),
        ("C_PEDAGOGY", "Pedagogy & Assessment Design", "Functional", "Designing effective learning materials and tests."),
    ]
    cursor.executemany("INSERT OR IGNORE INTO frac_competencies VALUES (?, ?, ?, ?)", competencies)

    # 2. Insert Roles
    roles = [
        ("R_SO", "Statistical Officer", "SSS", "Entry-level field and desk data officer."),
        ("R_SSO", "Senior Statistical Officer", "SSS", "Supervisory data officer and intermediate analyst."),
        ("R_DD", "Deputy Director", "ISS", "Mid-level management and advanced analytical role."),
        ("R_JD", "Joint Director", "ISS", "Senior policy and macroeconomic statistical leadership."),
        ("R_DIR", "Director", "ISS", "Top-level administration, strategic planning, and publication control."),
        ("R_DQA", "Data Quality Analyst", "National Data Governance Unit", "Specialist in data integrity and privacy."),
        ("R_FACULTY", "NSSTA Faculty / Trainer", "NSSTA", "Educator specializing in capacity building."),
        ("R_CB_DIR", "Capacity Building Director / Administrator", "MoSPI", "Enterprise learning and skill management."),
        ("R_DSO", "District Statistical Officer", "State DES", "District-level data aggregation and state reporting.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO frac_roles VALUES (?, ?, ?, ?)", roles)

    # 3. Insert Role-Competency Mappings
    # Levels: 1 (Awareness), 2 (Foundation), 3 (Working), 4 (Advanced), 5 (Expert)
    mappings = [
        # Statistical Officer (SO)
        ("R_SO", "C_SURVEY", 2),
        ("R_SO", "C_SAMPLING", 2),
        ("R_SO", "C_PYTHON", 2),
        ("R_SO", "C_DATAVIZ", 2),
        ("R_SO", "C_SQL", 3),
        ("R_SO", "C_ETHICS", 3),
        ("R_SO", "C_DPDP", 2),

        # Senior Statistical Officer (SSO)
        ("R_SSO", "C_SURVEY", 3),
        ("R_SSO", "C_SAMPLING", 3),
        ("R_SSO", "C_PYTHON", 3),
        ("R_SSO", "C_DATAVIZ", 3),
        ("R_SSO", "C_SQL", 3),
        ("R_SSO", "C_NAT_ACC", 2),
        ("R_SSO", "C_PRICE", 3),
        ("R_SSO", "C_ETHICS", 4),
        ("R_SSO", "C_DPDP", 3),
        ("R_SSO", "C_AI_ML", 2),

        # Joint Director (ISS)
        ("R_JD", "C_SURVEY", 4),
        ("R_JD", "C_SAMPLING", 4),
        ("R_JD", "C_NAT_ACC", 5),
        ("R_JD", "C_PRICE", 4),
        ("R_JD", "C_SDG", 4),
        ("R_JD", "C_PYTHON", 3),
        ("R_JD", "C_AI_ML", 3),
        ("R_JD", "C_DATAVIZ", 4),
        ("R_JD", "C_LEADERSHIP", 4),
        ("R_JD", "C_ETHICS", 5),

        # Data Quality Analyst
        ("R_DQA", "C_SQL", 4),
        ("R_DQA", "C_PYTHON", 4),
        ("R_DQA", "C_DPDP", 5),
        ("R_DQA", "C_CYBER", 4),
        ("R_DQA", "C_DATAVIZ", 3),
        ("R_DQA", "C_ETHICS", 4),

        # Trainer / Faculty
        ("R_FACULTY", "C_PEDAGOGY", 5),
        ("R_FACULTY", "C_CAPACITY", 5),
        ("R_FACULTY", "C_SURVEY", 4),
        ("R_FACULTY", "C_PYTHON", 4),
        ("R_FACULTY", "C_AI_ML", 3),
        ("R_FACULTY", "C_ETHICS", 4),

        # Capacity Building Director
        ("R_CB_DIR", "C_CAPACITY", 5),
        ("R_CB_DIR", "C_LEADERSHIP", 5),
        ("R_CB_DIR", "C_DATAVIZ", 4),
        ("R_CB_DIR", "C_ETHICS", 4)
    ]
    # Provisional project mappings, subject to organisational validation.
    mappings += [("R_DD", cid, min(level, 4)) for role, cid, level in mappings if role == "R_JD"]
    mappings += [("R_DIR", cid, level) for role, cid, level in mappings if role == "R_JD"]
    mappings += [("R_DSO", cid, max(level, 3)) for role, cid, level in mappings if role == "R_SO"]
    cursor.executemany("INSERT OR IGNORE INTO frac_role_competency_map VALUES (?, ?, ?)", mappings)

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("Setting up FRAC models...")
    create_frac_tables(cursor)
    seed_frac_data(cursor)
    conn.commit()
    conn.close()
    print("FRAC database tables created and seeded.")

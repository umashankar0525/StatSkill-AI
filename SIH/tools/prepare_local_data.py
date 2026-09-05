"""Create a private working database from the packaged RAG starter data."""
import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STARTER_DB = ROOT / "data" / "starter" / "igot_demo.db"
STARTER_USERS = ROOT / "data" / "starter" / "users.json"
MATERIALS = ROOT / "data" / "study_materials"
MANIFEST = ROOT / "data" / "study_material_manifest.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def prepare(database: Path, uploads: Path, reset: bool = False) -> None:
    if reset or not database.exists():
        if not STARTER_DB.exists():
            raise FileNotFoundError("The packaged starter database is missing.")
        database.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STARTER_DB, database)
        print(f"Created private database: {database}")

    users = ROOT / "users.json"
    if reset or not users.exists():
        shutil.copy2(STARTER_USERS, users)

    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["materials"]
    uploads.mkdir(parents=True, exist_ok=True)
    locations = []
    for entry in entries:
        source = MATERIALS / entry["filename"]
        if not source.exists() or digest(source) != entry["sha256"]:
            raise RuntimeError(f"Study material is missing or changed: {entry['filename']}")
        document_id = "pdf-" + entry["sha256"][:24]
        target = uploads / f"{document_id}.pdf"
        if not target.exists() or digest(target) != entry["sha256"]:
            shutil.copy2(source, target)
        locations.append((str(target.resolve()), document_id))

    connection = sqlite3.connect(database)
    try:
        for location, document_id in locations:
            connection.execute(
                "UPDATE documents SET storage_path=? WHERE id=?", (location, document_id)
            )
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        documents = connection.execute(
            "SELECT COUNT(*) FROM documents WHERE status='ready'"
        ).fetchone()[0]
        chunks = connection.execute("SELECT COUNT(*) FROM doc_chunks").fetchone()[0]
    finally:
        connection.close()
    if integrity != "ok" or documents != len(entries) or chunks < 1:
        raise RuntimeError("The packaged RAG database failed its integrity check.")
    print(f"RAG data ready: {documents} documents and {chunks} indexed chunks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=ROOT / "igot_demo.db")
    parser.add_argument("--uploads", type=Path, default=ROOT / "uploads")
    parser.add_argument("--reset", action="store_true")
    options = parser.parse_args()
    prepare(options.database.resolve(), options.uploads.resolve(), options.reset)

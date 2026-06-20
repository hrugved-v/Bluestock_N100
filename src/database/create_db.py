import sqlite3

conn = sqlite3.connect("nifty100.db")

conn.execute("PRAGMA foreign_keys = ON")

with open("db/schema.sql", "r", encoding="utf-8") as f:
    schema = f.read()

conn.executescript(schema)

conn.commit()
conn.close()

print("Database created successfully.")
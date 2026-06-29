# review_companies.py

import sqlite3

conn = sqlite3.connect("nifty100.db")
cur = conn.cursor()

cur.execute("""
SELECT id
FROM companies
ORDER BY RANDOM()
LIMIT 5
""")

companies = cur.fetchall()

for company in companies:
    print(company[0])

conn.close()
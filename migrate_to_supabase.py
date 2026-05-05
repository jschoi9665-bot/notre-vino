#!/usr/bin/env python3
"""
SQLite(wines.db) → Supabase 마이그레이션 스크립트
실행: python3 migrate_to_supabase.py
"""

import sqlite3
import os

SUPABASE_URL = "https://cuckutompcfzmdhixaje.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1Y2t1dG9tcGNmem1kaGl4YWplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4MzYyMzAsImV4cCI6MjA5MjQxMjIzMH0."
    "nNqYVG_NAJu0yBsjz6SC0opPVQnRgwQcABJPiigHrq4"
)
DB_PATH = os.path.join(os.path.dirname(__file__), "wines.db")

from supabase import create_client

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# 기존 Supabase 데이터 확인
existing = sb.table("wines").select("id").execute()
existing_ids = {r["id"] for r in (existing.data or [])}
print(f"Supabase 기존 레코드 수: {len(existing_ids)}")

# SQLite에서 읽기
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM wines")
rows = cur.fetchall()
conn.close()
print(f"SQLite 레코드 수: {len(rows)}")

inserted = 0
skipped = 0
for row in rows:
    r = dict(row)
    sqlite_id = r.pop("id", None)

    # image_data가 None이면 빈 문자열로
    if r.get("image_data") is None:
        r["image_data"] = ""

    # 이미 동일한 id가 있으면 skip (id를 직접 지정해서 삽입)
    if sqlite_id in existing_ids:
        print(f"  skip id={sqlite_id} (이미 존재)")
        skipped += 1
        continue

    # id를 명시적으로 포함하여 삽입 (같은 id 유지)
    r["id"] = sqlite_id
    try:
        sb.table("wines").insert(r).execute()
        print(f"  inserted id={sqlite_id} name={r.get('name')}")
        inserted += 1
    except Exception as e:
        print(f"  ERROR id={sqlite_id}: {e}")

print(f"\n완료: {inserted}개 삽입, {skipped}개 스킵")

# 최종 확인
final = sb.table("wines").select("id,name,user_name").execute()
print(f"Supabase 최종 레코드 수: {len(final.data or [])}")
for r in (final.data or []):
    print(f"  id={r['id']} name={r['name']} user={r['user_name']}")

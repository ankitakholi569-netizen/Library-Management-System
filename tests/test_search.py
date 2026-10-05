"""
Unit Test Suite for Search & Fast Retrieval Services (Quality Goal 1).
Course: BBAT104 - Total Quality Management.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from database.seed import seed_database
from services.search_service import (
    quick_search,
    search_books,
    search_members,
    search_loans,
    get_search_kpi_summary,
)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()

def test_quick_search_latency_and_matches():
    result = quick_search("Python", limit=5)
    assert "matched_books" in result
    assert "matched_members" in result
    assert "latency_ms" in result
    assert len(result["matched_books"]) > 0
    # TQM SLA Target: Search latency must be fast (< 250ms on cold SQLite)
    assert result["latency_ms"] < 250.0

def test_search_books_filtering():
    # 1. By Query
    res_query = search_books(query="Database", per_page=10)
    assert res_query["total"] > 0
    for b in res_query["books"]:
        assert "database" in b["title"].lower() or "database" in b["author"].lower() or "database" in b["category"].lower()

    # 2. By Category
    res_cat = search_books(category="Management", per_page=50)
    assert res_cat["total"] > 0
    for b in res_cat["books"]:
        assert b["category"] == "Management"

    # 3. By Availability
    res_avail = search_books(available_only=True, per_page=50)
    assert res_avail["total"] > 0
    for b in res_avail["books"]:
        assert b["available_copies"] > 0

    # 4. Pagination
    res_p1 = search_books(page=1, per_page=5)
    res_p2 = search_books(page=2, per_page=5)
    assert len(res_p1["books"]) == 5
    assert len(res_p2["books"]) == 5
    assert res_p1["books"][0]["id"] != res_p2["books"][0]["id"]
    assert res_p1["pages"] >= 10

def test_search_members():
    # 1. Search by USN prefix
    res_usn = search_members(query="1RV", per_page=20)
    assert res_usn["total"] > 0
    for m in res_usn["members"]:
        assert "1rv" in m["usn"].lower() or "1rv" in m["name"].lower() or "1rv" in m["department"].lower()

    # 2. Filter by Department
    res_dept = search_members(department="CSE", per_page=50)
    assert res_dept["total"] > 0
    for m in res_dept["members"]:
        assert m["department"] == "CSE"

def test_search_loans():
    res = search_loans(status="Overdue")
    assert "results" in res
    for l in res["results"]:
        assert l["status"] == "Overdue"

def test_search_kpi_summary():
    summary = get_search_kpi_summary()
    assert "total_searches" in summary
    assert "avg_latency_ms" in summary
    assert summary["sla_pass_rate"] >= 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

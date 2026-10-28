"""
Verification script for Major Part 5: Localhost Web Application & REST APIs.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.app import create_app

def test_web_application():
    print("=" * 70)
    print("VERIFYING MAJOR PART 5: LOCALHOST WEB APPLICATION & REST APIS")
    print("=" * 70)

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. HTML Rendering Test
    print("\n[Step 1/5] Testing Web Portal HTML Dashboard (GET /)...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"CampusLib Pro" in res.data, "Brand missing in index.html"
    assert b"Automated Payroll" in res.data, "Payroll section missing in HTML"
    print(f"  [OK] GET / -> HTTP 200 OK ({len(res.data)} bytes rendered)")

    # 2. REST API: Dashboard KPIs
    print("\n[Step 2/5] Testing REST API: TQM Metrics (GET /api/kpis)...")
    res_kpis = client.get("/api/kpis")
    assert res_kpis.status_code == 200
    k_data = res_kpis.get_json()
    assert k_data["success"] is True
    k = k_data["kpis"]
    print(f"  [OK] KPIs: Total Books={k['total_books']}, Active Loans={k['active_loans']}, On-Time Rate={k['on_time_return_rate']}%")

    # 3. REST API: Book Catalog & Filter
    print("\n[Step 3/5] Testing REST API: Catalog Search (GET /api/books)...")
    res_books = client.get("/api/books")
    assert res_books.status_code == 200
    b_data = res_books.get_json()
    assert b_data["count"] > 0
    print(f"  [OK] Loaded {b_data['count']} textbooks from shared database")

    res_search = client.get("/api/books?q=Algorithms")
    assert res_search.status_code == 200
    s_data = res_search.get_json()
    assert s_data["count"] >= 1
    print(f"  [OK] Instant search filter verified (found {s_data['count']} match for 'Algorithms')")

    # 4. REST API: Staff Shift Logging & Automated Payroll Run
    print("\n[Step 4/5] Testing Shift Logging & Automated Payroll (POST /api/payrolls)...")
    res_shift = client.post("/api/shifts", json={
        "user_id": 1,
        "shift_date": "2026-10-16",
        "regular_hours": 8.0,
        "overtime_hours": 2.5,
        "tasks_completed": "Web portal automated verification shift",
        "is_verified": True
    })
    assert res_shift.status_code == 201
    print("  [OK] Shift logged via Web API (POST /api/shifts)")

    res_pay = client.post("/api/payrolls", json={"month": 10, "year": 2026})
    assert res_pay.status_code == 201
    p_data = res_pay.get_json()
    assert p_data["success"] is True
    print(f"  [OK] Automated payroll triggered via Web API: {p_data['message']}")

    # 5. File Download Export Routes
    print("\n[Step 5/5] Testing PDF & Excel Web Download Routes...")
    res_pdf = client.get("/export/payslip/1")
    assert res_pdf.status_code == 200
    assert len(res_pdf.data) > 1000
    print(f"  [OK] GET /export/payslip/1 -> ReportLab PDF served ({len(res_pdf.data)} bytes)")

    res_cat = client.get("/export/catalog")
    assert res_cat.status_code == 200
    assert len(res_cat.data) > 1000
    print(f"  [OK] GET /export/catalog -> Excel workbook served ({len(res_cat.data)} bytes)")

    res_audit = client.get("/export/quality-audit")
    assert res_audit.status_code == 200
    assert len(res_audit.data) > 1000
    print(f"  [OK] GET /export/quality-audit -> Quality audit Excel served ({len(res_audit.data)} bytes)")

    print("\n" + "=" * 70)
    print(">>> MAJOR PART 5 ALL CHECKS PASSED: WEB APP FULLY OPERATIONAL <<<")
    print("=" * 70)

if __name__ == "__main__":
    test_web_application()

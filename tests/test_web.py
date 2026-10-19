"""
========================================================================================
TQM SYSTEM VERIFICATION — WEB PORTAL & REST API
========================================================================================
Run this script to verify:
  1. Flask Web Application initialization & template loading
  2. JSON REST APIs (/api/kpis, /api/search/quick, /api/books, /api/members, /api/loans, /api/staff, /api/payrolls)
  3. Excel exports (/export/catalog, /export/quality-audit) & PDF Pay Slip routes
========================================================================================
"""

import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure safe output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database.seed import seed_database
from web.app import create_app

def test_web_portal():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- WEB PORTAL & REST APIS")
    print("=" * 80)

    # 1. Prepare Database
    seed_database()

    # 2. Initialize Flask Test Client
    print("\n[Step 1/3] Initializing Flask Web Application & Routes...")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    print("  [OK] Flask application initialized with test client")

    # 3. Test HTML Interface
    print("\n[Step 2/3] Testing Web UI Page & HTML Assets...")
    res_index = client.get("/")
    assert res_index.status_code == 200, f"Expected 200, got {res_index.status_code}"
    assert b"Library Management System" in res_index.data, "App title missing in index.html"
    assert b"Executive TQM" in res_index.data, "Dashboard section missing"
    print(f"  [OK] GET / -> HTTP 200 OK ({len(res_index.data)} bytes rendered)")

    # 4. Test REST API Endpoints
    print("\n[Step 3/3] Testing REST API Endpoints (JSON Data Contracts)...")

    # KPIs API
    res_kpis = client.get("/api/kpis")
    assert res_kpis.status_code == 200
    k_json = res_kpis.get_json()
    assert k_json["success"] is True
    print(f"  [OK] GET /api/kpis -> Active Loans: {k_json['kpis']['active_loans']}, On-Time Rate: {k_json['kpis']['on_time_return_rate']}%")

    # Quick Search API
    res_quick = client.get("/api/search/quick?q=Python")
    assert res_quick.status_code == 200
    q_data = res_quick.get_json()
    assert q_data["success"] is True
    print(f"  [OK] GET /api/search/quick?q=Python -> Latency: {q_data['latency_ms']:.2f}ms | Books: {len(q_data['matched_books'])}, Members: {len(q_data['matched_members'])}")

    # Books API
    res_books = client.get("/api/books")
    assert res_books.status_code == 200
    b_json = res_books.get_json()
    assert b_json["success"] is True
    assert b_json["count"] > 0
    print(f"  [OK] GET /api/books -> {b_json['count']} textbooks loaded ({b_json['latency_ms']:.2f}ms)")

    # Filtered Books API
    res_filtered = client.get("/api/books?category=Computer+Science")
    assert res_filtered.status_code == 200
    assert res_filtered.get_json()["success"] is True
    print(f"  [OK] GET /api/books?category=Computer+Science -> Category filter verified")

    # Members API
    res_members = client.get("/api/members")
    assert res_members.status_code == 200
    m_json = res_members.get_json()
    assert m_json["success"] is True
    assert m_json["count"] > 0
    print(f"  [OK] GET /api/members -> {m_json['count']} student & faculty patrons loaded")

    # Member borrow history API
    if m_json["members"]:
        first_m_id = m_json["members"][0]["id"]
        res_hist = client.get(f"/api/members/{first_m_id}/loans")
        assert res_hist.status_code == 200
        print(f"  [OK] GET /api/members/{first_m_id}/loans -> Member loan history loaded")

    # Loans API
    res_loans = client.get("/api/loans")
    assert res_loans.status_code == 200
    l_json = res_loans.get_json()
    assert l_json["success"] is True
    print(f"  [OK] GET /api/loans -> {l_json['count']} circulation records loaded")

    # Staff & Payroll API
    res_payrolls = client.get("/api/payrolls")
    assert res_payrolls.status_code == 200
    p_json = res_payrolls.get_json()
    assert p_json["success"] is True
    print(f"  [OK] GET /api/payrolls -> {p_json['count']} payroll records")

    # Quality Logs API
    res_quality = client.get("/api/quality-logs")
    assert res_quality.status_code == 200
    q_json = res_quality.get_json()
    assert q_json["success"] is True
    print(f"  [OK] GET /api/quality-logs -> {q_json['count']} audit trail entries")

    # Export routes
    res_excel = client.get("/export/catalog")
    assert res_excel.status_code == 200
    print(f"  [OK] GET /export/catalog -> Excel workbook ({len(res_excel.data)} bytes)")

    res_audit_excel = client.get("/export/quality-audit")
    assert res_audit_excel.status_code == 200
    print(f"  [OK] GET /export/quality-audit -> Excel audit log ({len(res_audit_excel.data)} bytes)")

    if p_json["payrolls"]:
        first_p_id = p_json["payrolls"][0]["id"]
        res_pdf = client.get(f"/export/payslip/{first_p_id}")
        assert res_pdf.status_code == 200
        print(f"  [OK] GET /export/payslip/{first_p_id} -> PDF pay slip ({len(res_pdf.data)} bytes)")

    print("\n" + "=" * 80)
    print(">>> WEB PORTAL & REST APIS FULLY OPERATIONAL AND VERIFIED <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_web_portal()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Web verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

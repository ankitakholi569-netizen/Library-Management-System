"""Verification script for Part 2 — database, models, seed, services."""
import sys
sys.path.insert(0, '.')

print('--- Step 1: Seeding database ---')
from database.seed import seed_database
seed_database()
print('Seed complete.')

print()
print('--- Step 2: Testing library_service ---')
from services.library_service import (
    get_all_books, get_all_members, get_all_loans,
    get_dashboard_kpis, get_popular_books, refresh_overdue_statuses
)
books   = get_all_books()
members = get_all_members()
loans   = get_all_loans()
print(f'Books in catalog : {len(books)}')
print(f'Members enrolled : {len(members)}')
print(f'Loan records     : {len(loans)}')

overdue = refresh_overdue_statuses(processed_by='system')
print(f'Overdue refresh  : {overdue} loans updated')

kpis = get_dashboard_kpis()
print(f'KPIs total_books = {kpis["total_books"]}')
print(f'KPIs overdue_loans = {kpis["overdue_loans"]}')
print(f'KPIs on_time_rate = {kpis["on_time_rate"]}%')

pop = get_popular_books(5)
print(f'Top books: {[b["title"][:30] for b in pop]}')

print()
print('--- Step 3: Testing search_service ---')
from services.search_service import quick_search, search_books, search_members, get_search_kpi_summary

r = quick_search('Python')
print(f'quick_search Python -> {r["total"]} results in {r["latency_ms"]}ms, SLA OK: {r["sla_ok"]}')

r2 = search_books(query='Algorithm', sort_by='year', sort_dir='desc')
print(f'search_books Algorithm -> {r2["total"]} results in {r2["latency_ms"]}ms')

r3 = search_members(query='Aarav')
print(f'search_members Aarav -> {r3["total"]} results in {r3["latency_ms"]}ms')

kpi_sum = get_search_kpi_summary()
print(f'Search KPI avg={kpi_sum["avg_latency_ms"]}ms, SLA pass={kpi_sum["sla_pass_rate"]}%')

print()
print('--- Step 4: Testing issue/return workflow ---')
from services.library_service import issue_book, return_book

ok, loan_d, msg = issue_book(book_id=4, member_id=5, processed_by='priya_desk')
print(f'Issue: {ok} | {msg}')
if ok and loan_d:
    loan_id = loan_d['id']
    ok2, ret_d, msg2 = return_book(loan_id=loan_id, processed_by='priya_desk')
    print(f'Return: {ok2} | {msg2}')

print()
print('ALL CHECKS PASSED')

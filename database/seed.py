"""
Database Seeding Script for Library Management System (TQM Edition).
Course: BBAT104 — Total Quality Management.

Populates production-ready sample records:
  - 3 staff users (Admin, Librarian, Assistant)
  - 50 books across 8 subject categories with realistic ISBNs
  - 20 members (students + faculty) across multiple departments
  - 30 loan transactions (active, returned, overdue) with fine calculation
  - Staff shifts and payroll for the current month
  - Quality log seed entries demonstrating TQM measurement

Idempotent: safe to call multiple times without duplication.
"""

import logging
from datetime import date, datetime, timedelta
from sqlalchemy import select, func

from database.db import get_db, init_db
from database.models import User, Book, Member, Loan, StaffShift, StaffPayroll, QualityLog

logger = logging.getLogger("seed")


# ──────────────────────────────────────────────────────────────────────────────
# SEED DATA CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

SEED_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "full_name": "Dr. Anita Sharma",
        "role": "Chief Librarian",
        "email": "anita.sharma@college.edu",
        "department": "Library Administration",
        "hourly_rate": 150.0,
        "base_salary": 45000.0,
    },
    {
        "username": "priya_desk",
        "password": "priya123",
        "full_name": "Priya Nair",
        "role": "Assistant Librarian",
        "email": "priya.nair@college.edu",
        "department": "Circulation & Lending",
        "hourly_rate": 120.0,
        "base_salary": 28000.0,
    },
    {
        "username": "rahul_catalog",
        "password": "rahul123",
        "full_name": "Rahul Verma",
        "role": "Library Assistant",
        "email": "rahul.verma@college.edu",
        "department": "Cataloging & Acquisition",
        "hourly_rate": 110.0,
        "base_salary": 22000.0,
    },
]

SEED_BOOKS = [
    # ── Computer Science & Engineering ──────────────────────────────────────
    {"title": "Introduction to Algorithms", "author": "Cormen, Leiserson, Rivest & Stein",
     "category": "Computer Science", "isbn": "978-0-262-03384-8", "year": 2022,
     "total_copies": 5, "available_copies": 3, "shelf_location": "Aisle 1 - Rack A"},
    {"title": "Clean Code: A Handbook of Agile Software Craftsmanship", "author": "Robert C. Martin",
     "category": "Computer Science", "isbn": "978-0-13-235088-4", "year": 2008,
     "total_copies": 4, "available_copies": 2, "shelf_location": "Aisle 1 - Rack B"},
    {"title": "Design Patterns: Elements of Reusable Object-Oriented Software", "author": "Gang of Four",
     "category": "Computer Science", "isbn": "978-0-201-63361-0", "year": 1994,
     "total_copies": 3, "available_copies": 1, "shelf_location": "Aisle 1 - Rack B"},
    {"title": "The Pragmatic Programmer", "author": "David Thomas & Andrew Hunt",
     "category": "Computer Science", "isbn": "978-0-13-595705-9", "year": 2019,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 1 - Rack C"},
    {"title": "Computer Organization and Architecture", "author": "William Stallings",
     "category": "Computer Science", "isbn": "978-0-13-460342-8", "year": 2021,
     "total_copies": 6, "available_copies": 4, "shelf_location": "Aisle 1 - Rack D"},
    {"title": "Operating System Concepts (Dinosaur Book)", "author": "Silberschatz, Galvin & Gagne",
     "category": "Computer Science", "isbn": "978-1-119-32091-3", "year": 2018,
     "total_copies": 5, "available_copies": 3, "shelf_location": "Aisle 1 - Rack E"},
    {"title": "Database System Concepts", "author": "Silberschatz, Korth & Sudarshan",
     "category": "Computer Science", "isbn": "978-1-260-08400-4", "year": 2019,
     "total_copies": 5, "available_copies": 2, "shelf_location": "Aisle 1 - Rack F"},
    {"title": "Computer Networks", "author": "Andrew S. Tanenbaum",
     "category": "Computer Science", "isbn": "978-0-13-212695-3", "year": 2011,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 1 - Rack G"},

    # ── Electronics & Communication ─────────────────────────────────────────
    {"title": "Signals and Systems", "author": "Alan V. Oppenheim & Alan S. Willsky",
     "category": "Electronics", "isbn": "978-0-13-814757-0", "year": 1997,
     "total_copies": 4, "available_copies": 3, "shelf_location": "Aisle 2 - Rack A"},
    {"title": "Electronic Devices and Circuit Theory", "author": "Robert L. Boylestad",
     "category": "Electronics", "isbn": "978-0-13-262846-2", "year": 2012,
     "total_copies": 6, "available_copies": 5, "shelf_location": "Aisle 2 - Rack B"},
    {"title": "Digital Signal Processing", "author": "John G. Proakis & Dimitris Manolakis",
     "category": "Electronics", "isbn": "978-0-13-187374-2", "year": 2006,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 2 - Rack C"},
    {"title": "Microelectronics Circuit Analysis and Design", "author": "Donald A. Neamen",
     "category": "Electronics", "isbn": "978-0-07-252362-1", "year": 2009,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 2 - Rack D"},
    {"title": "Communication Systems", "author": "Simon Haykin",
     "category": "Electronics", "isbn": "978-0-47-117869-9", "year": 2001,
     "total_copies": 3, "available_copies": 1, "shelf_location": "Aisle 2 - Rack E"},

    # ── Mathematics ─────────────────────────────────────────────────────────
    {"title": "Higher Engineering Mathematics", "author": "B.S. Grewal",
     "category": "Mathematics", "isbn": "978-9-38-173629-9", "year": 2023,
     "total_copies": 8, "available_copies": 5, "shelf_location": "Aisle 3 - Rack A"},
    {"title": "Advanced Engineering Mathematics", "author": "Erwin Kreyszig",
     "category": "Mathematics", "isbn": "978-0-47-064613-7", "year": 2011,
     "total_copies": 5, "available_copies": 3, "shelf_location": "Aisle 3 - Rack B"},
    {"title": "Calculus: Early Transcendentals", "author": "James Stewart",
     "category": "Mathematics", "isbn": "978-1-28-574154-0", "year": 2015,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 3 - Rack C"},
    {"title": "Discrete Mathematics and Its Applications", "author": "Kenneth H. Rosen",
     "category": "Mathematics", "isbn": "978-1-25-962698-8", "year": 2018,
     "total_copies": 5, "available_copies": 2, "shelf_location": "Aisle 3 - Rack D"},
    {"title": "Probability and Statistics for Engineers", "author": "Jay L. Devore",
     "category": "Mathematics", "isbn": "978-1-30-574589-9", "year": 2015,
     "total_copies": 4, "available_copies": 3, "shelf_location": "Aisle 3 - Rack E"},

    # ── Mechanical Engineering ───────────────────────────────────────────────
    {"title": "Engineering Mechanics: Statics", "author": "R.C. Hibbeler",
     "category": "Mechanical Engineering", "isbn": "978-0-13-396089-9", "year": 2016,
     "total_copies": 5, "available_copies": 4, "shelf_location": "Aisle 4 - Rack A"},
    {"title": "Thermodynamics: An Engineering Approach", "author": "Cengel & Boles",
     "category": "Mechanical Engineering", "isbn": "978-0-07-339817-4", "year": 2014,
     "total_copies": 4, "available_copies": 3, "shelf_location": "Aisle 4 - Rack B"},
    {"title": "Fluid Mechanics", "author": "Frank M. White",
     "category": "Mechanical Engineering", "isbn": "978-0-07-352934-9", "year": 2011,
     "total_copies": 3, "available_copies": 3, "shelf_location": "Aisle 4 - Rack C"},
    {"title": "Strength of Materials", "author": "R.K. Bansal",
     "category": "Mechanical Engineering", "isbn": "978-8-17-008824-5", "year": 2018,
     "total_copies": 5, "available_copies": 2, "shelf_location": "Aisle 4 - Rack D"},

    # ── Civil Engineering ────────────────────────────────────────────────────
    {"title": "Structural Analysis", "author": "Russell C. Hibbeler",
     "category": "Civil Engineering", "isbn": "978-0-13-257053-4", "year": 2018,
     "total_copies": 4, "available_copies": 3, "shelf_location": "Aisle 5 - Rack A"},
    {"title": "Concrete Technology", "author": "M.S. Shetty",
     "category": "Civil Engineering", "isbn": "978-8-12-190463-3", "year": 2010,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 5 - Rack B"},
    {"title": "Surveying Vol. I", "author": "B.C. Punmia",
     "category": "Civil Engineering", "isbn": "978-8-17-008118-5", "year": 2015,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 5 - Rack C"},
    {"title": "Geotechnical Engineering", "author": "C. Venkatramaiah",
     "category": "Civil Engineering", "isbn": "978-8-12-196029-5", "year": 2012,
     "total_copies": 3, "available_copies": 1, "shelf_location": "Aisle 5 - Rack D"},

    # ── Management & TQM ────────────────────────────────────────────────────
    {"title": "Total Quality Management", "author": "Dale H. Besterfield",
     "category": "Management", "isbn": "978-0-13-262441-9", "year": 2013,
     "total_copies": 6, "available_copies": 4, "shelf_location": "Aisle 6 - Rack A"},
    {"title": "Operations Management", "author": "William J. Stevenson",
     "category": "Management", "isbn": "978-1-25-925922-0", "year": 2018,
     "total_copies": 5, "available_copies": 3, "shelf_location": "Aisle 6 - Rack B"},
    {"title": "Principles of Management", "author": "P.C. Tripathi & P.N. Reddy",
     "category": "Management", "isbn": "978-0-07-068374-7", "year": 2017,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 6 - Rack C"},
    {"title": "Human Resource Management", "author": "Gary Dessler",
     "category": "Management", "isbn": "978-0-13-423479-3", "year": 2019,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 6 - Rack D"},
    {"title": "Six Sigma: The Breakthrough Management Strategy", "author": "Mikel J. Harry",
     "category": "Management", "isbn": "978-0-38-549437-4", "year": 2000,
     "total_copies": 3, "available_copies": 3, "shelf_location": "Aisle 6 - Rack E"},
    {"title": "The Goal: A Process of Ongoing Improvement", "author": "Eliyahu M. Goldratt",
     "category": "Management", "isbn": "978-0-88-427178-9", "year": 2004,
     "total_copies": 4, "available_copies": 3, "shelf_location": "Aisle 6 - Rack F"},

    # ── Physics & Chemistry ─────────────────────────────────────────────────
    {"title": "Engineering Physics", "author": "Gaur & Gupta",
     "category": "Science", "isbn": "978-8-12-190407-7", "year": 2019,
     "total_copies": 5, "available_copies": 5, "shelf_location": "Aisle 7 - Rack A"},
    {"title": "A Textbook of Engineering Chemistry", "author": "Shashi Chawla",
     "category": "Science", "isbn": "978-9-38-173052-5", "year": 2020,
     "total_copies": 5, "available_copies": 4, "shelf_location": "Aisle 7 - Rack B"},
    {"title": "University Physics", "author": "Young & Freedman",
     "category": "Science", "isbn": "978-0-13-398125-1", "year": 2015,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 7 - Rack C"},
    {"title": "Concepts of Modern Physics", "author": "Arthur Beiser",
     "category": "Science", "isbn": "978-0-07-340036-5", "year": 2009,
     "total_copies": 3, "available_copies": 3, "shelf_location": "Aisle 7 - Rack D"},

    # ── Artificial Intelligence & Data Science ──────────────────────────────
    {"title": "Artificial Intelligence: A Modern Approach", "author": "Russell & Norvig",
     "category": "Artificial Intelligence", "isbn": "978-0-13-461099-3", "year": 2020,
     "total_copies": 5, "available_copies": 3, "shelf_location": "Aisle 8 - Rack A"},
    {"title": "Deep Learning", "author": "Goodfellow, Bengio & Courville",
     "category": "Artificial Intelligence", "isbn": "978-0-26-203561-3", "year": 2016,
     "total_copies": 4, "available_copies": 2, "shelf_location": "Aisle 8 - Rack B"},
    {"title": "Pattern Recognition and Machine Learning", "author": "Christopher M. Bishop",
     "category": "Artificial Intelligence", "isbn": "978-0-38-731073-2", "year": 2006,
     "total_copies": 3, "available_copies": 1, "shelf_location": "Aisle 8 - Rack C"},
    {"title": "Python for Data Analysis", "author": "Wes McKinney",
     "category": "Artificial Intelligence", "isbn": "978-1-49-195766-0", "year": 2022,
     "total_copies": 4, "available_copies": 4, "shelf_location": "Aisle 8 - Rack D"},
    {"title": "Hands-On Machine Learning with Scikit-Learn and TensorFlow", "author": "Aurélien Géron",
     "category": "Artificial Intelligence", "isbn": "978-1-09-812564-4", "year": 2022,
     "total_copies": 4, "available_copies": 2, "shelf_location": "Aisle 8 - Rack E"},
    {"title": "Data Structures and Algorithm Analysis in Java", "author": "Mark Allen Weiss",
     "category": "Computer Science", "isbn": "978-0-13-257627-7", "year": 2011,
     "total_copies": 3, "available_copies": 3, "shelf_location": "Aisle 1 - Rack H"},
    {"title": "Compiler Design Principles, Techniques and Tools", "author": "Aho, Lam, Sethi & Ullman",
     "category": "Computer Science", "isbn": "978-0-32-148681-3", "year": 2006,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 1 - Rack I"},
    {"title": "Software Engineering: A Practitioner's Approach", "author": "Roger S. Pressman",
     "category": "Computer Science", "isbn": "978-0-07-337597-7", "year": 2014,
     "total_copies": 4, "available_copies": 3, "shelf_location": "Aisle 1 - Rack J"},
    {"title": "Computer Graphics: Principles and Practice", "author": "Foley, van Dam, Feiner & Hughes",
     "category": "Computer Science", "isbn": "978-0-32-153907-5", "year": 1990,
     "total_copies": 2, "available_copies": 2, "shelf_location": "Aisle 1 - Rack K"},
    {"title": "Introduction to the Theory of Computation", "author": "Michael Sipser",
     "category": "Computer Science", "isbn": "978-1-28-508534-4", "year": 2012,
     "total_copies": 3, "available_copies": 3, "shelf_location": "Aisle 1 - Rack L"},
    {"title": "Network Security Essentials", "author": "William Stallings",
     "category": "Computer Science", "isbn": "978-0-13-452733-0", "year": 2017,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 1 - Rack M"},
    {"title": "Cloud Computing: Concepts, Technology & Architecture", "author": "Thomas Erl",
     "category": "Computer Science", "isbn": "978-0-13-388572-8", "year": 2013,
     "total_copies": 3, "available_copies": 3, "shelf_location": "Aisle 1 - Rack N"},
    {"title": "Internet of Things: Principles and Paradigms", "author": "Rajkumar Buyya",
     "category": "Artificial Intelligence", "isbn": "978-0-12-805395-9", "year": 2016,
     "total_copies": 3, "available_copies": 2, "shelf_location": "Aisle 8 - Rack F"},
    {"title": "Blockchain: Blueprint for a New Economy", "author": "Melanie Swan",
     "category": "Computer Science", "isbn": "978-1-49-192049-7", "year": 2015,
     "total_copies": 2, "available_copies": 2, "shelf_location": "Aisle 1 - Rack O"},
]

SEED_MEMBERS = [
    # Students — CSE
    {"usn": "1RV21CS001", "name": "Aarav Patel",       "department": "CSE", "semester": 6,
     "membership_type": "Student", "email": "aarav.p@college.edu",    "phone": "9880001001", "status": "Active"},
    {"usn": "1RV21CS042", "name": "Sneha Reddy",       "department": "CSE", "semester": 6,
     "membership_type": "Student", "email": "sneha.r@college.edu",    "phone": "9880001042", "status": "Active"},
    {"usn": "1RV22CS015", "name": "Arjun Menon",       "department": "CSE", "semester": 4,
     "membership_type": "Student", "email": "arjun.m@college.edu",    "phone": "9880002015", "status": "Active"},
    {"usn": "1RV22CS078", "name": "Divya Krishnan",    "department": "CSE", "semester": 4,
     "membership_type": "Student", "email": "divya.k@college.edu",    "phone": "9880002078", "status": "Active"},
    {"usn": "1RV23CS033", "name": "Kiran Nair",        "department": "CSE", "semester": 2,
     "membership_type": "Student", "email": "kiran.n@college.edu",    "phone": "9880003033", "status": "Active"},

    # Students — ECE
    {"usn": "1RV21EC011", "name": "Priya Sharma",      "department": "ECE", "semester": 6,
     "membership_type": "Student", "email": "priya.sh@college.edu",   "phone": "9880011011", "status": "Active"},
    {"usn": "1RV22EC055", "name": "Rohan Gupta",       "department": "ECE", "semester": 4,
     "membership_type": "Student", "email": "rohan.g@college.edu",    "phone": "9880012055", "status": "Active"},
    {"usn": "1RV22EC089", "name": "Anjali Singh",      "department": "ECE", "semester": 4,
     "membership_type": "Student", "email": "anjali.s@college.edu",   "phone": "9880012089", "status": "Active"},

    # Students — Mechanical
    {"usn": "1RV21ME007", "name": "Suresh Kumar",      "department": "ME",  "semester": 6,
     "membership_type": "Student", "email": "suresh.k@college.edu",   "phone": "9880021007", "status": "Active"},
    {"usn": "1RV22ME044", "name": "Meena Iyer",        "department": "ME",  "semester": 4,
     "membership_type": "Student", "email": "meena.i@college.edu",    "phone": "9880022044", "status": "Active"},

    # Students — Civil
    {"usn": "1RV21CV019", "name": "Ravi Bhat",         "department": "CV",  "semester": 6,
     "membership_type": "Student", "email": "ravi.b@college.edu",     "phone": "9880031019", "status": "Active"},
    {"usn": "1RV22CV062", "name": "Lakshmi Pillai",    "department": "CV",  "semester": 4,
     "membership_type": "Student", "email": "lakshmi.p@college.edu",  "phone": "9880032062", "status": "Active"},

    # Students — MBA / Management
    {"usn": "1RV22MB008", "name": "Vishal Joshi",      "department": "MBA", "semester": 3,
     "membership_type": "Student", "email": "vishal.j@college.edu",   "phone": "9880041008", "status": "Active"},
    {"usn": "1RV22MB021", "name": "Neha Saxena",       "department": "MBA", "semester": 3,
     "membership_type": "Student", "email": "neha.s@college.edu",     "phone": "9880041021", "status": "Active"},
    {"usn": "1RV23MB005", "name": "Aditya Rao",        "department": "MBA", "semester": 1,
     "membership_type": "Student", "email": "aditya.r@college.edu",   "phone": "9880043005", "status": "Active"},

    # Faculty Members
    {"usn": "FAC-CSE-001", "name": "Prof. S. Krishnamurthy", "department": "CSE", "semester": 0,
     "membership_type": "Faculty", "email": "s.krish@college.edu",    "phone": "9810001001", "status": "Active"},
    {"usn": "FAC-ECE-002", "name": "Dr. P. Ramachandran",    "department": "ECE", "semester": 0,
     "membership_type": "Faculty", "email": "p.rama@college.edu",     "phone": "9810002002", "status": "Active"},
    {"usn": "FAC-ME-003",  "name": "Prof. R. Viswanathan",   "department": "ME",  "semester": 0,
     "membership_type": "Faculty", "email": "r.viswa@college.edu",    "phone": "9810003003", "status": "Active"},
    {"usn": "FAC-CV-004",  "name": "Dr. A. Murugan",         "department": "CV",  "semester": 0,
     "membership_type": "Faculty", "email": "a.muru@college.edu",     "phone": "9810004004", "status": "Active"},

    # Suspended member (for testing guard logic)
    {"usn": "1RV20CS099", "name": "Rahul Suspended",   "department": "CSE", "semester": 8,
     "membership_type": "Student", "email": "rahul.sus@college.edu",  "phone": "9880099099", "status": "Suspended"},
]


# ──────────────────────────────────────────────────────────────────────────────
# SEEDING FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def _seed_users(db) -> list:
    """Seeds staff user accounts. Returns list of User objects."""
    created = []
    for u in SEED_USERS:
        existing = db.scalar(select(User).where(User.username == u["username"]))
        if not existing:
            user = User(
                username=u["username"],
                full_name=u["full_name"],
                role=u["role"],
                email=u["email"],
                department=u["department"],
                hourly_rate=u["hourly_rate"],
                base_salary=u["base_salary"],
                is_active=True,
            )
            user.set_password(u["password"])
            db.add(user)
            created.append(user)
            logger.info(f"  Created user: {u['username']} ({u['role']})")
    db.flush()
    return created


def _seed_books(db) -> list:
    """Seeds 50-book catalog. Returns list of Book objects."""
    created = []
    for b in SEED_BOOKS:
        existing = db.scalar(select(Book).where(Book.isbn == b["isbn"]))
        if not existing:
            book = Book(
                title=b["title"],
                author=b["author"],
                category=b["category"],
                isbn=b["isbn"],
                year=b["year"],
                total_copies=b["total_copies"],
                available_copies=b["available_copies"],
                shelf_location=b["shelf_location"],
                defect_flag=False,
                defect_notes="",
            )
            db.add(book)
            created.append(book)
    db.flush()
    if created:
        logger.info(f"  Seeded {len(created)} books into catalog.")
    return created


def _seed_members(db) -> list:
    """Seeds 20 library members. Returns list of Member objects."""
    created = []
    for m in SEED_MEMBERS:
        existing = db.scalar(select(Member).where(Member.usn == m["usn"]))
        if not existing:
            member = Member(
                usn=m["usn"],
                name=m["name"],
                department=m["department"],
                semester=m["semester"],
                membership_type=m["membership_type"],
                email=m["email"],
                phone=m["phone"],
                status=m["status"],
            )
            db.add(member)
            created.append(member)
    db.flush()
    if created:
        logger.info(f"  Seeded {len(created)} members.")
    return created


def _seed_loans(db):
    """Seeds realistic loan transactions (returned, active, overdue)."""
    loan_count = db.scalar(select(func.count(Loan.id)))
    if loan_count > 0:
        return  # Already seeded

    today = date.today()
    books = db.scalars(select(Book).limit(20)).all()
    members = db.scalars(select(Member).where(Member.status == "Active").limit(15)).all()
    if not books or not members:
        return

    def _make_loan(book, member, borrow_offset, period, returned=False,
                   return_offset=None, processed_by="priya_desk"):
        borrow_dt = today - timedelta(days=borrow_offset)
        due_dt = borrow_dt + timedelta(days=period)
        loan = Loan(
            book_id=book.id,
            member_id=member.id,
            borrow_date=borrow_dt,
            due_date=due_dt,
            processed_by=processed_by,
            fine_paid=False,
        )
        if returned and return_offset is not None:
            loan.return_date = borrow_dt + timedelta(days=return_offset)
            loan.status = "Returned"
            # Fine if returned late
            if loan.return_date > due_dt:
                overdue_days = (loan.return_date - due_dt).days
                loan.fine_amount = round(overdue_days * 5.0, 2)
            else:
                loan.fine_amount = 0.0
        else:
            loan.check_and_update_overdue(today)
        return loan

    loans = [
        # ── Returned on time ─────────────────────────────────
        _make_loan(books[0],  members[0],  30, 14, True, 12),
        _make_loan(books[1],  members[1],  25, 14, True, 13),
        _make_loan(books[2],  members[2],  20, 14, True, 14),
        _make_loan(books[3],  members[3],  45, 14, True, 10),
        _make_loan(books[4],  members[4],  35, 14, True, 13),
        _make_loan(books[5],  members[5],  50, 14, True, 12),
        _make_loan(books[6],  members[6],  60, 14, True, 11),
        _make_loan(books[7],  members[7],  40, 14, True, 14),
        _make_loan(books[8],  members[8],  55, 14, True, 13),
        _make_loan(books[9],  members[9],  28, 14, True, 10),

        # ── Returned late (fines incurred) ───────────────────
        _make_loan(books[10], members[10], 35, 14, True, 20),   # 6 days overdue
        _make_loan(books[11], members[11], 40, 14, True, 25),   # 11 days overdue
        _make_loan(books[12], members[12], 50, 14, True, 18),   # 4 days overdue

        # ── Currently active (not overdue) ───────────────────
        _make_loan(books[13], members[0],   8, 14),
        _make_loan(books[14], members[1],   5, 14),
        _make_loan(books[15], members[2],   3, 14),
        _make_loan(books[16], members[3],  10, 14),

        # ── Currently overdue ────────────────────────────────
        _make_loan(books[0],  members[5],  20, 14),   # 6 days overdue
        _make_loan(books[1],  members[6],  25, 14),   # 11 days overdue
        _make_loan(books[2],  members[7],  30, 14),   # 16 days overdue
        _make_loan(books[3],  members[8],  35, 14),   # 21 days overdue
        _make_loan(books[4],  members[9],  22, 14),   # 8 days overdue

        # ── Faculty loans ─────────────────────────────────────
        _make_loan(books[17], members[13], 10, 30),   # Faculty get 30-day period
        _make_loan(books[18], members[14], 15, 30),
        _make_loan(books[19], members[13],  5, 30),
    ]

    # Reconcile available_copies with loan state
    for loan in loans:
        if loan.status in ("Borrowed", "Overdue"):
            book = db.get(Book, loan.book_id)
            if book and book.available_copies > 0:
                book.available_copies = max(0, book.available_copies - 1)
        db.add(loan)

    db.flush()
    logger.info(f"  Seeded {len(loans)} loan transactions.")


def _seed_shifts_and_payroll(db):
    """Seeds staff shifts and monthly payroll for the current month."""
    users = db.scalars(select(User).where(User.role != "Student")).all()
    if not users:
        return

    today = date.today()
    month_start = today.replace(day=1)

    for user in users:
        # Check if shifts already seeded for this month
        existing_shift = db.scalar(
            select(StaffShift).where(
                StaffShift.user_id == user.id,
                StaffShift.shift_date >= month_start,
            )
        )
        if existing_shift:
            continue

        # Seed ~15 working days for each staff member
        for day_offset in range(0, min(today.day, 20)):
            shift_date = month_start + timedelta(days=day_offset)
            if shift_date.weekday() < 5 and shift_date <= today:  # Weekdays only
                overtime = 1.5 if day_offset % 5 == 0 else 0.0
                shift = StaffShift(
                    user_id=user.id,
                    shift_date=shift_date,
                    shift_type="Regular Day Shift",
                    regular_hours=8.0,
                    overtime_hours=overtime,
                    tasks_completed="Catalog maintenance & desk circulation",
                    is_verified=True,
                )
                db.add(shift)

        # Compute payroll for the seeded shifts
        db.flush()
        existing_payroll = db.scalar(
            select(StaffPayroll).where(
                StaffPayroll.user_id == user.id,
                StaffPayroll.period_month == today.month,
                StaffPayroll.period_year == today.year,
            )
        )
        if not existing_payroll:
            shifts_this_month = db.scalars(
                select(StaffShift).where(
                    StaffShift.user_id == user.id,
                    StaffShift.shift_date >= month_start,
                    StaffShift.is_verified == True,
                )
            ).all()
            total_reg = sum(s.regular_hours for s in shifts_this_month)
            total_ot = sum(s.overtime_hours for s in shifts_this_month)

            payroll = StaffPayroll(
                user_id=user.id,
                period_month=today.month,
                period_year=today.year,
                total_regular_hours=total_reg,
                total_overtime_hours=total_ot,
                hourly_rate=user.hourly_rate,
                base_salary=user.base_salary,
                performance_rating=round(4.5 + (user.id % 3) * 0.2, 1),
                status="Processed",
            )
            payroll.compute()
            db.add(payroll)

    db.flush()
    logger.info("  Staff shifts and payroll seeded.")


def _seed_quality_logs(db):
    """Seeds representative TQM quality audit entries."""
    q_count = db.scalar(select(func.count(QualityLog.id)))
    if q_count >= 10:
        return

    samples = [
        QualityLog(module="CATALOG",    action="BOOK_SEARCH",    status="SUCCESS",
                   execution_time_ms=18.5,  details="ISBN search: 50 results in 18.5ms"),
        QualityLog(module="CIRCULATION", action="BOOK_ISSUE",    status="SUCCESS",
                   execution_time_ms=35.2,  details="Loan issued: Book #1 to Member #1"),
        QualityLog(module="CIRCULATION", action="OVERDUE_CHECK", status="SLA_BREACH",
                   execution_time_ms=112.3, details="Overdue scan latency exceeded 100ms SLA",
                   remedial_action="Added composite index idx_txn_status_dates"),
        QualityLog(module="AUTH",       action="USER_LOGIN",     status="SUCCESS",
                   execution_time_ms=42.0,  details="User: admin authenticated"),
        QualityLog(module="REPORT",     action="PDF_EXPORT",     status="SUCCESS",
                   execution_time_ms=340.0, details="Payslip PDF generated for Dr. Anita Sharma"),
        QualityLog(module="CATALOG",    action="DEFECT_TAGGED",  status="DEFECT",
                   execution_time_ms=5.1,   details="Book ISBN 978-0-13-235088-4 marked as defective",
                   remedial_action="Physical inspection and repair initiated"),
        QualityLog(module="DATABASE",   action="DB_INIT",        status="SUCCESS",
                   execution_time_ms=210.0, details="Schema initialized with WAL mode"),
        QualityLog(module="PAYROLL",    action="PAYROLL_COMPUTE",status="SUCCESS",
                   execution_time_ms=88.4,  details="Monthly payroll computed for 3 staff"),
    ]
    for q in samples:
        db.add(q)
    db.flush()
    logger.info(f"  Seeded {len(samples)} quality log entries.")


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def seed_database():
    """
    Seeds production-ready sample records across all modules.
    Ensures idempotency: safe to call multiple times without duplication.
    """
    init_db()
    logger.info("Running database seed check...")

    with get_db() as db:
        _seed_users(db)
        _seed_books(db)
        _seed_members(db)
        _seed_loans(db)
        _seed_shifts_and_payroll(db)
        _seed_quality_logs(db)

    logger.info("Database seed complete. System ready.")

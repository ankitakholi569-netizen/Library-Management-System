from datetime import date, datetime, timedelta
import time
from sqlalchemy import select, func
from app.models.base import Base, engine, get_db
from app.models.user import User
from app.models.member import Member
from app.models.book import Book
from app.models.loan import Loan
from app.models.payroll import StaffShift, StaffPayroll
from app.models.quality_log import QualityLog
from app.core.logger import get_logger

logger = get_logger("db_service")

def init_database():
    """
    Creates all relational tables and indexes using SQLAlchemy metadata.
    Demonstrates TQM Principle: Standardization & Data Structure Integrity.
    """
    logger.info("Initializing database schema with SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema created successfully.")

def seed_sample_data():
    """
    Seeds production-ready sample records across all modules for TQM viva demonstrations.
    Demonstrates TQM Principle: Error Prevention & Ready-State Consistency.
    """
    with get_db() as db:
        # 1. Seed Users / Staff if empty
        admin_exists = db.scalar(select(func.count(User.id))) > 0
        if not admin_exists:
            logger.info("Seeding administrative & staff user accounts...")
            admin_user = User(
                username="admin",
                full_name="Dr. Anita Sharma (Chief Librarian)",
                role="Chief Librarian",
                email="anita.sharma@college.edu",
            )
            admin_user.set_password("admin123")

            staff_user_1 = User(
                username="priya_desk",
                full_name="Priya Nair (Circulation Officer)",
                role="Assistant Librarian",
                email="priya.nair@college.edu",
            )
            staff_user_1.set_password("priya123")

            staff_user_2 = User(
                username="rahul_catalog",
                full_name="Rahul Verma (Catalog Specialist)",
                role="Library Assistant",
                email="rahul.verma@college.edu",
            )
            staff_user_2.set_password("rahul123")

            db.add_all([admin_user, staff_user_1, staff_user_2])
            db.flush()

        # 2. Seed Engineering Textbooks if empty
        books_count = db.scalar(select(func.count(Book.id)))
        if books_count == 0:
            logger.info("Seeding engineering curriculum textbook inventory...")
            curriculum_books = [
                Book(title="Introduction to Algorithms (CLRS)", author="Thomas H. Cormen, Charles Leiserson", category="Computer Science", isbn="9780262033848", year=2022, total_copies=8, available_copies=6),
                Book(title="Operating System Concepts (10th Ed)", author="Abraham Silberschatz, Peter Galvin", category="Computer Science", isbn="9781119800361", year=2021, total_copies=6, available_copies=5),
                Book(title="Database System Concepts", author="Abraham Silberschatz, Henry F. Korth", category="Information Technology", isbn="9780078022159", year=2020, total_copies=7, available_copies=6),
                Book(title="Computer Networks: A Systems Approach", author="Larry L. Peterson, Bruce S. Davie", category="Computer Science", isbn="9780123850591", year=2019, total_copies=5, available_copies=4),
                Book(title="Artificial Intelligence: A Modern Approach", author="Stuart Russell, Peter Norvig", category="AI & Data Science", isbn="9780134610993", year=2020, total_copies=6, available_copies=5),
                Book(title="Clean Code: Agile Software Craftsmanship", author="Robert C. Martin", category="Software Engineering", isbn="9780132350884", year=2018, total_copies=5, available_copies=5),
                Book(title="Digital Design & Computer Architecture", author="David Harris, Sarah Harris", category="Electronics & Comm", isbn="9780123944245", year=2021, total_copies=4, available_copies=3),
                Book(title="Higher Engineering Mathematics", author="Dr. B.S. Grewal", category="Mathematics", isbn="9788174091955", year=2023, total_copies=10, available_copies=9),
                Book(title="Principles of Communication Systems", author="Herbert Taub, Donald L. Schilling", category="Electronics & Comm", isbn="9780070648111", year=2019, total_copies=4, available_copies=3),
                Book(title="Data Structures Using C and C++", author="Yedidyah Langsam, Moshe Augenstein", category="Computer Science", isbn="9780130369970", year=2019, total_copies=7, available_copies=6),
            ]
            db.add_all(curriculum_books)
            db.flush()

        # 3. Seed Students / Members if empty
        members_count = db.scalar(select(func.count(Member.id)))
        if members_count == 0:
            logger.info("Seeding engineering student directory...")
            students = [
                Member(usn="1RV21CS001", name="Aarav Sharma", department="CSE", semester=6, email="aarav.cs21@college.edu", phone="9876543210"),
                Member(usn="1RV21CS042", name="Ananya Iyer", department="CSE", semester=6, email="ananya.cs21@college.edu", phone="9876543211"),
                Member(usn="1RV22EC015", name="Rohan Verma", department="ECE", semester=4, email="rohan.ec22@college.edu", phone="9876543212"),
                Member(usn="1RV22AI030", name="Sneha Patel", department="AI & Data Science", semester=4, email="sneha.ai22@college.edu", phone="9876543213"),
                Member(usn="1RV23IT008", name="Vikramaditya Rao", department="IT", semester=2, email="vikram.it23@college.edu", phone="9876543214"),
                Member(usn="1RV21ME022", name="Karan Malhotra", department="MECH", semester=6, email="karan.me21@college.edu", phone="9876543215"),
                Member(usn="1RV23CV011", name="Divya Hegde", department="CIVIL", semester=2, email="divya.cv23@college.edu", phone="9876543216"),
            ]
            db.add_all(students)
            db.flush()

        # 4. Seed Circulation / Loans if empty
        loans_count = db.scalar(select(func.count(Loan.id)))
        if loans_count == 0:
            logger.info("Seeding circulation loans with overdue and returned SLA records...")
            today = date.today()
            sample_loans = [
                # Overdue Loan (6 days late -> 6 * ₹5 = ₹30 fine)
                Loan(book_id=1, member_id=1, issue_date=today - timedelta(days=20), due_date=today - timedelta(days=6), return_date=None, status="Overdue", fine_amount=30.0, processed_by="Dr. Anita Sharma"),
                # Active On-Time Loan
                Loan(book_id=2, member_id=2, issue_date=today - timedelta(days=5), due_date=today + timedelta(days=9), return_date=None, status="Borrowed", fine_amount=0.0, processed_by="Priya Nair"),
                # Returned On-Time Loan
                Loan(book_id=3, member_id=3, issue_date=today - timedelta(days=25), due_date=today - timedelta(days=11), return_date=today - timedelta(days=12), status="Returned", fine_amount=0.0, processed_by="Priya Nair"),
                # Active Loan for 4th student
                Loan(book_id=4, member_id=4, issue_date=today - timedelta(days=2), due_date=today + timedelta(days=12), return_date=None, status="Borrowed", fine_amount=0.0, processed_by="Dr. Anita Sharma"),
            ]
            db.add_all(sample_loans)
            db.flush()

        # 5. Seed Staff Shifts & Payroll if empty
        shifts_count = db.scalar(select(func.count(StaffShift.id)))
        if shifts_count == 0:
            logger.info("Seeding staff operational shifts & automated payroll runs...")
            user1 = db.scalar(select(User).where(User.username == "priya_desk"))
            user2 = db.scalar(select(User).where(User.username == "rahul_catalog"))
            
            if user1 and user2:
                # Add historical shifts
                today = date.today()
                sample_shifts = [
                    StaffShift(user_id=user1.id, shift_date=today - timedelta(days=1), regular_hours=8.0, overtime_hours=2.0, tasks_completed="Circulation desk SLA monitoring & textbook returns"),
                    StaffShift(user_id=user1.id, shift_date=today - timedelta(days=2), regular_hours=8.0, overtime_hours=1.5, tasks_completed="Library patron registrations & fine reconciliation"),
                    StaffShift(user_id=user1.id, shift_date=today - timedelta(days=3), regular_hours=8.0, overtime_hours=0.0, tasks_completed="Standard desk shift"),
                    StaffShift(user_id=user2.id, shift_date=today - timedelta(days=1), regular_hours=8.0, overtime_hours=0.0, tasks_completed="Barcode labeling and physical quality inspections"),
                    StaffShift(user_id=user2.id, shift_date=today - timedelta(days=2), regular_hours=8.0, overtime_hours=3.0, tasks_completed="Annual textbook shelf stock audit & index verification"),
                ]
                db.add_all(sample_shifts)
                db.flush()

                # Generate sample payroll for Priya
                payroll_p = StaffPayroll(
                    user_id=user1.id,
                    period_month=today.month,
                    period_year=today.year,
                    total_regular_hours=160.0,
                    total_overtime_hours=12.0,
                    hourly_rate=120.0,
                    status="Processed"
                )
                payroll_p.compute()

                # Generate sample payroll for Rahul
                payroll_r = StaffPayroll(
                    user_id=user2.id,
                    period_month=today.month,
                    period_year=today.year,
                    total_regular_hours=152.0,
                    total_overtime_hours=6.0,
                    hourly_rate=110.0,
                    status="Processed"
                )
                payroll_r.compute()

                db.add_all([payroll_p, payroll_r])
                db.flush()

        # 6. Seed Initial TQM Quality Logs
        quality_count = db.scalar(select(func.count(QualityLog.id)))
        if quality_count == 0:
            logger.info("Seeding initial TQM Quality Monitoring benchmarks...")
            initial_logs = [
                QualityLog(module="DATABASE", action="SCHEMA_MIGRATION", status="SUCCESS", execution_time_ms=14.2, details="SQLite tables created with PRAGMA foreign keys and WAL mode"),
                QualityLog(module="SECURITY", action="BCRYPT_INIT", status="SUCCESS", execution_time_ms=8.5, details="Admin credentials salted and hashed with 12 rounds"),
                QualityLog(module="CIRCULATION", action="SLA_VERIFICATION", status="SUCCESS", execution_time_ms=3.1, details="Academic 14-day circulation window rule calibrated"),
                QualityLog(module="PAYROLL", action="AUTOMATION_CALIBRATION", status="SUCCESS", execution_time_ms=5.4, details="OT multiplier (1.5x) and tax withholding formulas standardized"),
            ]
            db.add_all(initial_logs)

    logger.info("Database initialization and sample data seeding complete!")

def ensure_database_ready():
    """Initializes tables and seeds data if not present."""
    init_database()
    seed_sample_data()

"""
========================================================================================
🎓 CAMPUSLIB PRO - B.TECH ENGINEERING LIBRARY MANAGEMENT SYSTEM
========================================================================================
Architecture: Python Tkinter (Modern TTK Styling) + SQLite3
Target Audience: B.Tech / BE Engineering Colleges & Academic Mini/Major Projects
Features:
  - Modern Dashboard with Real-Time KPI Cards & Overdue Alerts
  - Engineering Textbook Catalog (CLRS, Silberschatz, Tanenbaum, etc.)
  - Student Database with USN / Roll No, Branch (CSE, ECE, etc.), and Semester
  - 14-Day Academic Loan Rules with Dynamic Overdue & Fine Calculation (₹5/day)
  - Instant Filter, Multi-criteria Search & Pagination
  - CSV Data Export for Books, Students, and Circulation Records
  - Single-Click Demo Auto-fill for Lab Vivas & Project Demos
========================================================================================
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta
import csv
import os

DB_NAME = "library.db"
PAGE_SIZE = 10
FINE_PER_DAY = 5.0  # ₹5 fine per day overdue
LOAN_PERIOD_DAYS = 14  # Standard academic loan duration


# ================= DATABASE CONNECTION & MIGRATIONS =================

def connect():
    con = sqlite3.connect(DB_NAME)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    with connect() as con:
        # Base tables
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'Librarian'
        );

        CREATE TABLE IF NOT EXISTS books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT DEFAULT '',
            isbn TEXT UNIQUE,
            year INTEGER,
            copies INTEGER NOT NULL DEFAULT 1 CHECK(copies >= 0)
        );

        CREATE TABLE IF NOT EXISTS members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usn TEXT UNIQUE,
            name TEXT NOT NULL,
            department TEXT DEFAULT 'CSE',
            semester INTEGER DEFAULT 1,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS loans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL REFERENCES books(id),
            member_id INTEGER NOT NULL REFERENCES members(id),
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Borrowed',
            fine_amount REAL DEFAULT 0.0
        );

        CREATE INDEX IF NOT EXISTS idx_books_title ON books(title COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_books_author ON books(author COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_books_category ON books(category COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
        CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
        CREATE INDEX IF NOT EXISTS idx_loans_book_member ON loans(book_id, member_id);
        """)

        # Schema migrations for existing databases that had older schema
        member_cols = [row[1] for row in con.execute("PRAGMA table_info(members)").fetchall()]
        if "usn" not in member_cols:
            con.execute("ALTER TABLE members ADD COLUMN usn TEXT UNIQUE")
        if "department" not in member_cols:
            con.execute("ALTER TABLE members ADD COLUMN department TEXT DEFAULT 'CSE'")
        if "semester" not in member_cols:
            con.execute("ALTER TABLE members ADD COLUMN semester INTEGER DEFAULT 1")

        loan_cols = [row[1] for row in con.execute("PRAGMA table_info(loans)").fetchall()]
        if "due_date" not in loan_cols:
            con.execute("ALTER TABLE loans ADD COLUMN due_date TEXT DEFAULT ''")
        if "fine_amount" not in loan_cols:
            con.execute("ALTER TABLE loans ADD COLUMN fine_amount REAL DEFAULT 0.0")

        # Admin user
        con.execute(
            "INSERT OR IGNORE INTO users(username, password, role) VALUES(?, ?, ?)",
            ("admin", "admin123", "Chief Librarian")
        )

        # Seed Engineering Textbooks if books table is empty
        book_count = con.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        if book_count == 0:
            engineering_books = [
                ("Introduction to Algorithms (CLRS)", "Thomas H. Cormen, Charles Leiserson",
                 "Computer Science", "9780262033848", 2022, 6),
                ("Operating System Concepts", "Abraham Silberschatz, Peter Galvin",
                 "Computer Science", "9781119800361", 2021, 5),
                ("Database System Concepts", "Abraham Silberschatz, Henry F. Korth",
                 "Information Technology", "9780078022159", 2020, 5),
                ("Computer Networks: A Systems Approach", "Larry L. Peterson, Bruce S. Davie",
                 "Computer Science", "9780123850591", 2019, 4),
                ("Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig",
                 "AI & Data Science", "9780134610993", 2020, 4),
                ("Clean Code: Agile Software Craftsmanship", "Robert C. Martin",
                 "Software Engineering", "9780132350884", 2018, 5),
                ("Digital Design and Computer Architecture", "David Harris, Sarah Harris",
                 "Electronics & Comm", "9780123944245", 2021, 3),
                ("Higher Engineering Mathematics", "Dr. B.S. Grewal",
                 "Mathematics", "9788174091955", 2023, 8),
                ("Compiler Design: Principles, Techniques, Tools", "Alfred V. Aho, Monica S. Lam",
                 "Computer Science", "9780321486813", 2017, 3),
                ("Principles of Communication Systems", "Herbert Taub, Donald L. Schilling",
                 "Electronics & Comm", "9780070648111", 2019, 4),
                ("Control Systems Engineering", "Norman S. Nise",
                 "Electrical & Electronics", "9781118170519", 2020, 3),
                ("Data Structures Using C and C++", "Yedidyah Langsam, Moshe J. Augenstein",
                 "Computer Science", "9780130369970", 2019, 6),
            ]
            con.executemany(
                """INSERT INTO books (title, author, category, isbn, year, copies)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                engineering_books
            )

        # Seed sample B.Tech students if members table is empty
        member_count = con.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        if member_count == 0:
            sample_students = [
                ("1RV21CS001", "Aarav Sharma", "CSE", 6, "aarav.cs21@college.edu", "9876543210"),
                ("1RV21CS042", "Ananya Iyer", "CSE", 6, "ananya.cs21@college.edu", "9876543211"),
                ("1RV22EC015", "Rohan Verma", "ECE", 4, "rohan.ec22@college.edu", "9876543212"),
                ("1RV22AI030", "Sneha Patel", "AI & Data Science", 4, "sneha.ai22@college.edu", "9876543213"),
                ("1RV23IT008", "Vikramaditya Rao", "IT", 2, "vikram.it23@college.edu", "9876543214"),
                ("1RV21ME022", "Karan Malhotra", "MECH", 6, "karan.me21@college.edu", "9876543215")
            ]
            con.executemany(
                """INSERT INTO members (usn, name, department, semester, email, phone)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                sample_students
            )

        # Seed sample active/overdue loans for realistic demo
        loan_count = con.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
        if loan_count == 0:
            today = date.today()
            overdue_issue = (today - timedelta(days=20)).isoformat()
            overdue_due = (today - timedelta(days=6)).isoformat()
            active_issue = (today - timedelta(days=4)).isoformat()
            active_due = (today + timedelta(days=10)).isoformat()

            sample_loans = [
                (1, 1, overdue_issue, overdue_due, None, "Borrowed", 30.0),
                (3, 2, active_issue, active_due, None, "Borrowed", 0.0),
                (2, 3, (today - timedelta(days=25)).isoformat(), (today - timedelta(days=11)).isoformat(), (today - timedelta(days=12)).isoformat(), "Returned", 0.0)
            ]
            con.executemany(
                """INSERT INTO loans (book_id, member_id, issue_date, due_date, return_date, status, fine_amount)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                sample_loans
            )


# ================= MODERN COLOR PALETTE & STYLES =================

COLORS = {
    "bg_main": "#F8FAFC",          # Ultra-light slate background
    "bg_sidebar": "#0F172A",       # Slate 900 dark sidebar
    "bg_sidebar_hover": "#1E293B", # Slate 800 hover
    "bg_card": "#FFFFFF",          # Pure white cards
    "border": "#E2E8F0",           # Subtle light gray border
    "text_primary": "#0F172A",     # Dark slate readable text
    "text_secondary": "#64748B",   # Slate 500 secondary text
    "text_light": "#F1F5F9",       # Light text for dark backgrounds
    "primary": "#2563EB",          # Royal Blue
    "primary_dark": "#1D4ED8",
    "primary_light": "#DBEAFE",
    "success": "#10B981",          # Emerald Green
    "success_bg": "#D1FAE5",
    "warning": "#F59E0B",          # Amber
    "warning_bg": "#FEF3C7",
    "danger": "#EF4444",           # Crimson Red
    "danger_bg": "#FEE2E2",
    "purple": "#8B5CF6",           # Violet
    "purple_bg": "#EDE9FE",
}

ENGINEERING_DEPTS = [
    "All Departments", "CSE", "ECE", "IT", "AI & Data Science",
    "MECH", "CIVIL", "EEE", "Mathematics", "Humanities"
]


# ================= MAIN APPLICATION CLASS =================

class LibraryApp:

    def __init__(self, root):
        self.root = root
        self.root.title("CampusLib Pro • B.Tech Engineering Library Management System")
        self.root.geometry("1200x760")
        self.root.minsize(1050, 680)

        self.root.configure(bg=COLORS["bg_main"])

        self.user = None
        self.user_role = "Librarian"
        self.page = 0
        self.active_tab = "dashboard"

        self.apply_theme()
        self.login_screen()

    def apply_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Global base styling
        style.configure(".", background=COLORS["bg_main"], foreground=COLORS["text_primary"], font=("Segoe UI", 10))

        # Modern Treeview Styling
        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            fieldbackground="#FFFFFF",
            rowheight=32,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#F1F5F9",
            foreground="#0F172A",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padding=(8, 6)
        )
        style.map("Treeview",
            background=[("selected", COLORS["primary_light"])],
            foreground=[("selected", COLORS["primary_dark"])]
        )
        style.map("Treeview.Heading",
            background=[("active", "#E2E8F0")]
        )

        # Modern Combobox & Entry styling
        style.configure("TCombobox", padding=5, relief="flat")
        style.configure("TEntry", padding=5, relief="flat")

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ================= MODERN LOGIN SCREEN =================

    def login_screen(self):
        self.clear()
        self.root.configure(bg=COLORS["bg_sidebar"])

        # Center card container
        card = tk.Frame(self.root, bg=COLORS["bg_card"], padx=40, pady=36, relief="flat")
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Branding Header
        badge_lbl = tk.Label(
            card,
            text="🎓 B.TECH COLLEGE PORTAL",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary_light"],
            fg=COLORS["primary"],
            padx=10, pady=4
        )
        badge_lbl.pack(pady=(0, 10))

        title_lbl = tk.Label(
            card,
            text="CampusLib Pro",
            font=("Segoe UI", 24, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"]
        )
        title_lbl.pack()

        subtitle = tk.Label(
            card,
            text="Fast Search & Academic Circulation System",
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"]
        )
        subtitle.pack(pady=(2, 22))

        # Input fields frame
        form_frame = tk.Frame(card, bg=COLORS["bg_card"])
        form_frame.pack(fill="x", pady=6)

        # Username
        tk.Label(
            form_frame, text="Username / Staff ID",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(4, 2))

        self.user_entry = tk.Entry(
            form_frame, font=("Segoe UI", 11),
            bg="#F8FAFC", fg="#0F172A",
            relief="solid", bd=1, highlightthickness=1,
            highlightcolor=COLORS["primary"], width=32
        )
        self.user_entry.pack(fill="x", ipady=5, pady=(0, 12))

        # Password
        tk.Label(
            form_frame, text="Password",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(4, 2))

        self.pass_entry = tk.Entry(
            form_frame, font=("Segoe UI", 11), show="•",
            bg="#F8FAFC", fg="#0F172A",
            relief="solid", bd=1, highlightthickness=1,
            highlightcolor=COLORS["primary"], width=32
        )
        self.pass_entry.pack(fill="x", ipady=5, pady=(0, 18))

        # Login button
        login_btn = tk.Button(
            card, text="Sign In to Portal →",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["primary"], fg="#FFFFFF",
            activebackground=COLORS["primary_dark"],
            activeforeground="#FFFFFF",
            relief="flat", cursor="hand2",
            pady=8, command=self.login
        )
        login_btn.pack(fill="x", pady=(4, 14))

        # Demo Credentials Box with 1-click Auto Fill for Lab Viva
        demo_box = tk.Frame(card, bg="#F1F5F9", padx=12, pady=10, relief="flat")
        demo_box.pack(fill="x", pady=(6, 0))

        tk.Label(
            demo_box,
            text="⚡ Lab Viva Demo Access",
            font=("Segoe UI", 8, "bold"),
            bg="#F1F5F9", fg=COLORS["text_secondary"]
        ).pack(anchor="w")

        tk.Label(
            demo_box,
            text="Username: admin  |  Password: admin123",
            font=("Segoe UI", 9),
            bg="#F1F5F9", fg="#334155"
        ).pack(anchor="w", pady=(1, 6))

        autofill_btn = tk.Button(
            demo_box, text="Auto-fill Demo Credentials",
            font=("Segoe UI", 8, "bold"),
            bg="#E2E8F0", fg=COLORS["primary_dark"],
            activebackground="#CBD5E1", relief="flat",
            cursor="hand2", command=self.fill_demo_creds
        )
        autofill_btn.pack(fill="x")

        self.pass_entry.bind("<Return>", lambda e: self.login())
        self.user_entry.bind("<Return>", lambda e: self.pass_entry.focus_set())
        self.user_entry.focus_set()

    def fill_demo_creds(self):
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, "admin")
        self.pass_entry.delete(0, tk.END)
        self.pass_entry.insert(0, "admin123")
        self.pass_entry.focus_set()

    def login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not username or not password:
            messagebox.showwarning("Incomplete", "Please enter your username and password.")
            return

        with connect() as con:
            row = con.execute(
                "SELECT id, username, role FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()

        if row:
            self.user = row["username"]
            self.user_role = row["role"] or "Librarian"
            self.root.configure(bg=COLORS["bg_main"])
            self.dashboard()
        else:
            messagebox.showerror("Access Denied", "Invalid username or password. Check credentials.")

    # ================= PROFESSIONAL APPLICATION SHELL =================

    def shell(self, title, subtitle_text=""):
        self.clear()
        self.root.configure(bg=COLORS["bg_main"])

        container = tk.Frame(self.root, bg=COLORS["bg_main"])
        container.pack(fill="both", expand=True)

        # ----------------- SIDEBAR -----------------
        sidebar = tk.Frame(container, bg=COLORS["bg_sidebar"], width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand_frame = tk.Frame(sidebar, bg=COLORS["bg_sidebar"], padx=18, pady=20)
        brand_frame.pack(fill="x")

        tk.Label(
            brand_frame, text="🎓 CampusLib",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_sidebar"], fg="#FFFFFF"
        ).pack(anchor="w")

        tk.Label(
            brand_frame, text="B.Tech Library Portal",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["bg_sidebar"], fg="#94A3B8"
        ).pack(anchor="w")

        tk.Frame(sidebar, bg="#1E293B", height=1).pack(fill="x", padx=12, pady=(0, 10))

        nav_items = [
            ("dashboard", "📊  Dashboard", self.dashboard),
            ("books", "📚  Book Inventory", lambda: self.books_screen()),
            ("members", "🎓  Students Directory", self.members_screen),
            ("loans", "🔄  Issue & Return", self.loans_screen),
            ("fines", "⚠️  Overdue & Fines", self.fines_screen),
        ]

        self.nav_buttons = {}
        for key, text, func in nav_items:
            is_active = (self.active_tab == key)
            bg_col = COLORS["primary"] if is_active else COLORS["bg_sidebar"]
            fg_col = "#FFFFFF" if is_active else "#CBD5E1"
            font_weight = "bold" if is_active else "normal"

            btn = tk.Button(
                sidebar,
                text=text,
                font=("Segoe UI", 10, font_weight),
                bg=bg_col,
                fg=fg_col,
                activebackground=COLORS["bg_sidebar_hover"],
                activeforeground="#FFFFFF",
                anchor="w",
                padx=18,
                pady=11,
                relief="flat",
                cursor="hand2",
                command=func
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # Spacer
        tk.Label(sidebar, text="", bg=COLORS["bg_sidebar"]).pack(fill="both", expand=True)

        # Quick Viva note
        viva_card = tk.Frame(sidebar, bg="#1E293B", padx=12, pady=10)
        viva_card.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(
            viva_card, text="📌 Engineering Edition",
            font=("Segoe UI", 8, "bold"),
            bg="#1E293B", fg="#60A5FA"
        ).pack(anchor="w")
        tk.Label(
            viva_card, text="CLRS, OS, DBMS & Branch Filtering Ready",
            font=("Segoe UI", 7),
            bg="#1E293B", fg="#94A3B8", wraplength=180, justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # User profile at bottom of sidebar
        user_frame = tk.Frame(sidebar, bg="#1E293B", padx=12, pady=12)
        user_frame.pack(fill="x", padx=10, pady=(0, 12))

        user_info = tk.Frame(user_frame, bg="#1E293B")
        user_info.pack(side="left", fill="x", expand=True)

        tk.Label(
            user_info, text=f"👤 {self.user}",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B", fg="#FFFFFF"
        ).pack(anchor="w")

        tk.Label(
            user_info, text=self.user_role,
            font=("Segoe UI", 8),
            bg="#1E293B", fg="#94A3B8"
        ).pack(anchor="w")

        logout_btn = tk.Button(
            user_frame, text="Logout",
            font=("Segoe UI", 8, "bold"),
            bg="#334155", fg="#F8FAFC",
            activebackground=COLORS["danger"],
            activeforeground="#FFFFFF",
            relief="flat", cursor="hand2",
            padx=8, pady=4,
            command=self.logout
        )
        logout_btn.pack(side="right")

        # ----------------- MAIN CONTENT -----------------
        main_content = tk.Frame(container, bg=COLORS["bg_main"])
        main_content.pack(side="left", fill="both", expand=True)

        # Top Header Bar
        top_bar = tk.Frame(main_content, bg="#FFFFFF", padx=24, pady=16, relief="flat")
        top_bar.pack(fill="x")
        tk.Frame(main_content, bg=COLORS["border"], height=1).pack(fill="x")

        title_box = tk.Frame(top_bar, bg="#FFFFFF")
        title_box.pack(side="left", fill="y")

        tk.Label(
            title_box, text=title,
            font=("Segoe UI", 16, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w")

        if subtitle_text:
            tk.Label(
                title_box, text=subtitle_text,
                font=("Segoe UI", 9),
                bg="#FFFFFF", fg=COLORS["text_secondary"]
            ).pack(anchor="w", pady=(2, 0))

        right_meta = tk.Frame(top_bar, bg="#FFFFFF")
        right_meta.pack(side="right", fill="y")

        curr_date = date.today().strftime("%d %b %Y, %A")
        tk.Label(
            right_meta, text=f"📅 {curr_date}",
            font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9", fg="#334155",
            padx=10, pady=5
        ).pack(side="right", padx=(10, 0))

        body = tk.Frame(main_content, bg=COLORS["bg_main"], padx=20, pady=16)
        body.pack(fill="both", expand=True)

        return body

    def logout(self):
        if messagebox.askyesno("Confirm Sign Out", "Are you sure you want to sign out of CampusLib?"):
            self.user = None
            self.login_screen()

    # ================= DASHBOARD =================

    def dashboard(self):
        self.active_tab = "dashboard"
        body = self.shell(
            "Library Dashboard & Overview",
            "Real-time operational statistics, inventory status, and circulation alerts"
        )

        with connect() as con:
            total_titles = con.execute("SELECT COUNT(*) FROM books").fetchone()[0]
            total_copies = con.execute("SELECT COALESCE(SUM(copies),0) FROM books").fetchone()[0]
            borrowed_count = con.execute("SELECT COUNT(*) FROM loans WHERE status='Borrowed'").fetchone()[0]
            available_copies = max(0, total_copies - borrowed_count)
            total_students = con.execute("SELECT COUNT(*) FROM members").fetchone()[0]

            today_str = date.today().isoformat()
            overdue_count = con.execute(
                """SELECT COUNT(*) FROM loans
                   WHERE status='Borrowed' AND due_date != '' AND due_date < ?""",
                (today_str,)
            ).fetchone()[0]

        # 5 KPI Metric Cards
        cards_frame = tk.Frame(body, bg=COLORS["bg_main"])
        cards_frame.pack(fill="x", pady=(0, 16))

        kpis = [
            ("Total Volumes", f"{total_copies:,}", f"{total_titles} Unique Titles", COLORS["primary"], COLORS["primary_light"], "📚"),
            ("Available Copies", f"{available_copies:,}", "In Shelves / Catalog", COLORS["success"], COLORS["success_bg"], "✅"),
            ("Currently Issued", f"{borrowed_count:,}", "Active Student Loans", COLORS["warning"], COLORS["warning_bg"], "🔄"),
            ("Overdue Loans", f"{overdue_count:,}", f"₹{FINE_PER_DAY:.0f}/day Penalty Rate", COLORS["danger"], COLORS["danger_bg"], "⚠️"),
            ("Enrolled Students", f"{total_students:,}", "B.Tech Registered", COLORS["purple"], COLORS["purple_bg"], "🎓"),
        ]

        for title, value, sub, color, bg_light, icon in kpis:
            card = tk.Frame(cards_frame, bg="#FFFFFF", relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=5)

            accent = tk.Frame(card, bg=color, width=4)
            accent.pack(side="left", fill="y")

            c_content = tk.Frame(card, bg="#FFFFFF", padx=12, pady=12)
            c_content.pack(side="left", fill="both", expand=True)

            c_header = tk.Frame(c_content, bg="#FFFFFF")
            c_header.pack(fill="x")

            tk.Label(c_header, text=title.upper(), font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(side="left")
            tk.Label(c_header, text=icon, font=("Segoe UI", 11), bg="#FFFFFF").pack(side="right")

            tk.Label(c_content, text=value, font=("Segoe UI", 18, "bold"), bg="#FFFFFF", fg=color).pack(anchor="w", pady=(4, 0))
            tk.Label(c_content, text=sub, font=("Segoe UI", 8), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w")

        # Split View
        split_frame = tk.Frame(body, bg=COLORS["bg_main"])
        split_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(split_frame, bg=COLORS["bg_main"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Quick Search Card
        search_card = tk.Frame(left_col, bg="#FFFFFF", padx=18, pady=14, highlightbackground=COLORS["border"], highlightthickness=1)
        search_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            search_card, text="⚡ Quick Book Search & Retrieval",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 8))

        s_bar = tk.Frame(search_card, bg="#FFFFFF")
        s_bar.pack(fill="x")

        self.dash_search_var = tk.StringVar()
        dash_entry = tk.Entry(
            s_bar, textvariable=self.dash_search_var,
            font=("Segoe UI", 10),
            bg="#F8FAFC", fg="#0F172A",
            relief="solid", bd=1, highlightthickness=1,
            highlightcolor=COLORS["primary"]
        )
        dash_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
        dash_entry.bind("<Return>", lambda e: self.books_screen(self.dash_search_var.get()))

        search_btn = tk.Button(
            s_bar, text="Search Catalog",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=lambda: self.books_screen(self.dash_search_var.get())
        )
        search_btn.pack(side="left")

        # High-Demand B.Tech Textbooks
        popular_card = tk.Frame(left_col, bg="#FFFFFF", padx=18, pady=14, highlightbackground=COLORS["border"], highlightthickness=1)
        popular_card.pack(fill="both", expand=True)

        tk.Label(
            popular_card, text="📖 Key B.Tech Engineering Textbooks",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 8))

        pop_tree = ttk.Treeview(popular_card, columns=("title", "category", "avail"), show="headings", height=6)
        pop_tree.heading("title", text="Title & Author")
        pop_tree.heading("category", text="Department / Category")
        pop_tree.heading("avail", text="Stock / Available")
        pop_tree.column("title", width=240)
        pop_tree.column("category", width=140)
        pop_tree.column("avail", width=90, anchor="center")
        pop_tree.pack(fill="both", expand=True)

        with connect() as con:
            rows = con.execute("""
                SELECT b.title, b.author, b.category, b.copies,
                       MAX(0, b.copies - COALESCE((SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'), 0)) as avail
                FROM books b
                ORDER BY b.id ASC LIMIT 6
            """).fetchall()
            for r in rows:
                pop_tree.insert("", "end", values=(f"{r['title']} ({r['author'][:18]}...)", r['category'], f"{r['avail']} of {r['copies']}"))

        # Right Column
        right_col = tk.Frame(split_frame, bg=COLORS["bg_main"], width=340)
        right_col.pack(side="right", fill="both", expand=False)
        right_col.pack_propagate(False)

        # Quick Actions
        qa_card = tk.Frame(right_col, bg="#FFFFFF", padx=18, pady=14, highlightbackground=COLORS["border"], highlightthickness=1)
        qa_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            qa_card, text="🚀 Rapid Circulation Actions",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 10))

        actions = [
            ("➕  Issue Book to Student", COLORS["primary"], self.loans_screen),
            ("📥  Return Book / Collect Fine", COLORS["success"], self.loans_screen),
            ("📚  Register New Book", "#334155", lambda: self.books_screen()),
            ("🎓  Enroll New Student", "#475569", self.members_screen),
        ]

        for text, bg_c, cmd in actions:
            btn = tk.Button(
                qa_card, text=text,
                font=("Segoe UI", 9, "bold"),
                bg=bg_c, fg="#FFFFFF",
                relief="flat", cursor="hand2",
                anchor="w", padx=12, pady=7,
                command=cmd
            )
            btn.pack(fill="x", pady=3)

        # Overdue alerts widget
        alert_card = tk.Frame(right_col, bg="#FFFFFF", padx=18, pady=14, highlightbackground=COLORS["border"], highlightthickness=1)
        alert_card.pack(fill="both", expand=True)

        tk.Label(
            alert_card, text="⚠️ Critical Overdue Notices",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF", fg=COLORS["danger"]
        ).pack(anchor="w", pady=(0, 8))

        with connect() as con:
            overdues = con.execute("""
                SELECT b.title, m.name, m.usn, l.due_date
                FROM loans l
                JOIN books b ON b.id=l.book_id
                JOIN members m ON m.id=l.member_id
                WHERE l.status='Borrowed' AND l.due_date != '' AND l.due_date < ?
                ORDER BY l.due_date ASC LIMIT 4
            """, (today_str,)).fetchall()

        if overdues:
            for o in overdues:
                row_f = tk.Frame(alert_card, bg=COLORS["danger_bg"], padx=8, pady=6)
                row_f.pack(fill="x", pady=3)
                tk.Label(
                    row_f, text=f"📕 {o['title'][:22]}...",
                    font=("Segoe UI", 9, "bold"),
                    bg=COLORS["danger_bg"], fg=COLORS["danger"]
                ).pack(anchor="w")
                tk.Label(
                    row_f, text=f"{o['usn'] or 'No USN'} • Due: {o['due_date']}",
                    font=("Segoe UI", 8),
                    bg=COLORS["danger_bg"], fg="#7F1D1D"
                ).pack(anchor="w")
        else:
            tk.Label(
                alert_card, text="✨ Great! No overdue books today.",
                font=("Segoe UI", 9),
                bg="#FFFFFF", fg=COLORS["success"]
            ).pack(anchor="w", pady=10)

    # ================= BOOK MANAGEMENT & SEARCH =================

    def books_screen(self, quick=""):
        self.active_tab = "books"
        body = self.shell(
            "Book Inventory & Fast Catalog Search",
            "Add, update, filter, and paginate textbooks across B.Tech departments"
        )

        form_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=12, highlightbackground=COLORS["border"], highlightthickness=1)
        form_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            form_card, text="📖 Book Details & Entry Form",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 8))

        self.book_vars = {
            key: tk.StringVar()
            for key in ("title", "author", "category", "isbn", "year", "copies")
        }

        grid_f = tk.Frame(form_card, bg="#FFFFFF")
        grid_f.pack(fill="x")

        labels = [
            ("Book Title *", "title", 28),
            ("Author(s) *", "author", 24),
            ("Department / Category", "category", 20),
            ("ISBN / Barcode", "isbn", 16),
            ("Pub. Year", "year", 10),
            ("Total Copies *", "copies", 10),
        ]

        for label_text, key, width in labels:
            col_f = tk.Frame(grid_f, bg="#FFFFFF")
            col_f.pack(side="left", padx=(0, 10), fill="x", expand=True)

            tk.Label(
                col_f, text=label_text,
                font=("Segoe UI", 8, "bold"),
                bg="#FFFFFF", fg=COLORS["text_secondary"]
            ).pack(anchor="w", pady=(0, 2))

            if key == "category":
                ent = ttk.Combobox(col_f, textvariable=self.book_vars[key], values=ENGINEERING_DEPTS[1:], width=width)
                ent.pack(fill="x", ipady=2)
            else:
                ent = tk.Entry(
                    col_f, textvariable=self.book_vars[key],
                    font=("Segoe UI", 9),
                    bg="#F8FAFC", fg="#0F172A",
                    relief="solid", bd=1, highlightthickness=1,
                    highlightcolor=COLORS["primary"], width=width
                )
                ent.pack(fill="x", ipady=3)

        btn_bar = tk.Frame(form_card, bg="#FFFFFF")
        btn_bar.pack(fill="x", pady=(10, 0))

        tk.Button(
            btn_bar, text="➕ Add Book",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.add_book
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_bar, text="✏️ Update Selected",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7", fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.update_book
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="🗑️ Delete Selected",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["danger"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.delete_book
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="🧹 Clear Fields",
            font=("Segoe UI", 9),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=10, pady=5,
            command=self.clear_book_form
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="📥 Export CSV",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["success"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.export_books_csv
        ).pack(side="right")

        # Filter & Search Bar
        search_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=10, highlightbackground=COLORS["border"], highlightthickness=1)
        search_card.pack(fill="x", pady=(0, 10))

        self.search_var = tk.StringVar(value=quick or "")
        self.filter_category = tk.StringVar(value="All Departments")
        self.filter_avail = tk.StringVar(value="All Availability")
        self.sort_var = tk.StringVar(value="Title A–Z")

        f_left = tk.Frame(search_card, bg="#FFFFFF")
        f_left.pack(side="left", fill="x", expand=True)

        tk.Label(f_left, text="Search (Title / Author / ISBN):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=0, sticky="w", padx=3)
        s_ent = tk.Entry(
            f_left, textvariable=self.search_var,
            font=("Segoe UI", 9),
            bg="#F8FAFC", fg="#0F172A",
            relief="solid", bd=1, highlightthickness=1,
            highlightcolor=COLORS["primary"], width=26
        )
        s_ent.grid(row=1, column=0, padx=3, pady=2, ipady=3)
        s_ent.bind("<KeyRelease>", lambda e: self.load_books(0))

        tk.Label(f_left, text="Department:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=1, sticky="w", padx=5)
        self.cat_box = ttk.Combobox(f_left, textvariable=self.filter_category, state="readonly", values=ENGINEERING_DEPTS, width=17)
        self.cat_box.grid(row=1, column=1, padx=5, pady=2)
        self.cat_box.bind("<<ComboboxSelected>>", lambda e: self.load_books(0))

        tk.Label(f_left, text="Stock Filter:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=2, sticky="w", padx=5)
        avail_box = ttk.Combobox(f_left, textvariable=self.filter_avail, state="readonly", values=["All Availability", "Available Only", "Currently Borrowed"], width=16)
        avail_box.grid(row=1, column=2, padx=5, pady=2)
        avail_box.bind("<<ComboboxSelected>>", lambda e: self.load_books(0))

        tk.Label(f_left, text="Sort By:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=3, sticky="w", padx=5)
        sort_box = ttk.Combobox(f_left, textvariable=self.sort_var, state="readonly", values=["Title A–Z", "Title Z–A", "Author A–Z", "Year newest", "Year oldest"], width=14)
        sort_box.grid(row=1, column=3, padx=5, pady=2)
        sort_box.bind("<<ComboboxSelected>>", lambda e: self.load_books(0))

        reset_btn = tk.Button(
            f_left, text="Reset Filters",
            font=("Segoe UI", 8, "bold"),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=8, pady=3,
            command=self.reset_search
        )
        reset_btn.grid(row=1, column=4, padx=8, pady=2)

        # Results Table
        table_card = tk.Frame(body, bg="#FFFFFF", padx=1, pady=1, highlightbackground=COLORS["border"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)

        cols = ("id", "title", "author", "category", "isbn", "year", "copies", "avail", "status")
        self.book_tree = ttk.Treeview(table_card, columns=cols, show="headings", height=11)

        col_defs = [
            ("id", "ID", 45, "center"),
            ("title", "Book Title", 260, "w"),
            ("author", "Author(s)", 180, "w"),
            ("category", "Department", 140, "w"),
            ("isbn", "ISBN", 120, "center"),
            ("year", "Year", 60, "center"),
            ("copies", "Total", 55, "center"),
            ("avail", "Avail", 55, "center"),
            ("status", "Status", 95, "center")
        ]

        for col, heading, width, anchor in col_defs:
            self.book_tree.heading(col, text=heading)
            self.book_tree.column(col, width=width, anchor=anchor)

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.book_tree.yview)
        self.book_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.book_tree.pack(side="left", fill="both", expand=True)

        self.book_tree.bind("<<TreeviewSelect>>", self.select_book)

        self.book_tree.tag_configure("in_stock", foreground="#065F46", background="#ECFDF5")
        self.book_tree.tag_configure("out_of_stock", foreground="#991B1B", background="#FEF2F2")

        # Pagination Bar
        pag_bar = tk.Frame(body, bg=COLORS["bg_main"])
        pag_bar.pack(fill="x", pady=(8, 0))

        self.result_label = tk.Label(pag_bar, text="", font=("Segoe UI", 9), bg=COLORS["bg_main"], fg=COLORS["text_secondary"])
        self.result_label.pack(side="left")

        pag_controls = tk.Frame(pag_bar, bg=COLORS["bg_main"])
        pag_controls.pack(side="right")

        prev_btn = tk.Button(
            pag_controls, text="◀ Previous",
            font=("Segoe UI", 8, "bold"),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=8, pady=3,
            command=lambda: self.load_books(max(0, self.page - 1))
        )
        prev_btn.pack(side="left", padx=2)

        self.page_label = tk.Label(pag_controls, text="Page 1/1", font=("Segoe UI", 9, "bold"), bg=COLORS["bg_main"], fg=COLORS["text_primary"])
        self.page_label.pack(side="left", padx=8)

        next_btn = tk.Button(
            pag_controls, text="Next ▶",
            font=("Segoe UI", 8, "bold"),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=8, pady=3,
            command=lambda: self.load_books(self.page + 1)
        )
        next_btn.pack(side="left", padx=2)

        self.load_books(0)

    def search_sql(self):
        clauses = []
        params = []

        term = self.search_var.get().strip()
        if term:
            clauses.append("(b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)")
            pat = f"%{term}%"
            params.extend([pat, pat, pat])

        cat = self.filter_category.get()
        if cat and cat != "All Departments":
            clauses.append("b.category=?")
            params.append(cat)

        avail = self.filter_avail.get()
        if avail == "Available Only":
            clauses.append("""(b.copies - (
                SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'
            )) > 0""")
        elif avail == "Currently Borrowed":
            clauses.append("""EXISTS (
                SELECT 1 FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'
            )""")

        where = " WHERE " + " AND ".join(clauses) if clauses else ""

        sort_options = {
            "Title A–Z": "b.title COLLATE NOCASE ASC",
            "Title Z–A": "b.title COLLATE NOCASE DESC",
            "Author A–Z": "b.author COLLATE NOCASE ASC",
            "Year newest": "b.year DESC",
            "Year oldest": "b.year ASC"
        }
        sort = sort_options.get(self.sort_var.get(), "b.title COLLATE NOCASE ASC")

        return where, params, sort

    def load_books(self, page=0):
        self.page = max(0, page)
        where, params, sort = self.search_sql()

        with connect() as con:
            total = con.execute("SELECT COUNT(*) FROM books b" + where, params).fetchone()[0]
            pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            self.page = min(self.page, pages - 1)
            offset = self.page * PAGE_SIZE

            sql = f"""
                SELECT b.id, b.title, b.author, b.category, b.isbn, b.year, b.copies,
                       MAX(0, b.copies - COALESCE((
                           SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'
                       ), 0)) AS available
                FROM books b
                {where}
                ORDER BY {sort}
                LIMIT ? OFFSET ?
            """
            rows = con.execute(sql, params + [PAGE_SIZE, offset]).fetchall()

        self.book_tree.delete(*self.book_tree.get_children())

        for idx, row in enumerate(rows):
            avail = row["available"]
            status_text = "Available" if avail > 0 else "Issued Out"
            tag = "in_stock" if avail > 0 else "out_of_stock"

            self.book_tree.insert(
                "", "end",
                values=(
                    row["id"], row["title"], row["author"], row["category"],
                    row["isbn"] or "-", row["year"] or "-", row["copies"],
                    avail, status_text
                ),
                tags=(tag,)
            )

        self.result_label.config(
            text=f"Showing {len(rows)} of {total} book(s) • Page {self.page + 1} of {pages}"
        )
        self.page_label.config(text=f"Page {self.page + 1}/{pages}")

    def reset_search(self):
        self.search_var.set("")
        self.filter_category.set("All Departments")
        self.filter_avail.set("All Availability")
        self.sort_var.set("Title A–Z")
        self.load_books(0)

    def clear_book_form(self):
        for var in self.book_vars.values():
            var.set("")
        self.book_tree.selection_remove(self.book_tree.selection())

    def select_book(self, event=None):
        sel = self.book_tree.selection()
        if not sel:
            return
        vals = self.book_tree.item(sel[0], "values")
        keys = ("title", "author", "category", "isbn", "year", "copies")
        for k, v in zip(keys, vals[1:7]):
            self.book_vars[k].set(v if v != "-" else "")

    def validate_book(self):
        title = self.book_vars["title"].get().strip()
        author = self.book_vars["author"].get().strip()
        if not title or not author:
            messagebox.showwarning("Required Fields", "Book Title and Author cannot be empty.")
            return None

        try:
            year_val = self.book_vars["year"].get().strip()
            year = int(year_val) if year_val else None
            copies = int(self.book_vars["copies"].get() or "1")
            if copies < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Year must be a valid number and Copies must be >= 0.")
            return None

        return (
            title,
            author,
            self.book_vars["category"].get().strip() or "General Engineering",
            self.book_vars["isbn"].get().strip() or None,
            year,
            copies
        )

    def add_book(self):
        data = self.validate_book()
        if not data:
            return
        try:
            with connect() as con:
                con.execute(
                    """INSERT INTO books (title, author, category, isbn, year, copies)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    data
                )
            messagebox.showinfo("Success", "New book added to library inventory.")
            self.load_books(0)
            self.clear_book_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate ISBN", "A book with this ISBN already exists.")

    def update_book(self):
        sel = self.book_tree.selection()
        if not sel:
            messagebox.showwarning("Select Book", "Please select a book from the table first.")
            return
        book_id = int(self.book_tree.item(sel[0], "values")[0])
        data = self.validate_book()
        if not data:
            return
        try:
            with connect() as con:
                con.execute(
                    """UPDATE books
                       SET title=?, author=?, category=?, isbn=?, year=?, copies=?
                       WHERE id=?""",
                    data + (book_id,)
                )
            messagebox.showinfo("Updated", "Book details successfully updated.")
            self.load_books(self.page)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "ISBN collision or database integrity error.")

    def delete_book(self):
        sel = self.book_tree.selection()
        if not sel:
            messagebox.showwarning("Select Book", "Please select a book to delete.")
            return
        book_id = int(self.book_tree.item(sel[0], "values")[0])
        book_title = self.book_tree.item(sel[0], "values")[1]

        if not messagebox.askyesno("Confirm Deletion", f"Permanently delete '{book_title}'?"):
            return

        with connect() as con:
            active = con.execute(
                "SELECT COUNT(*) FROM loans WHERE book_id=? AND status='Borrowed'",
                (book_id,)
            ).fetchone()[0]

            if active:
                messagebox.showerror(
                    "Blocked",
                    "Cannot delete this book because copies are currently borrowed by students."
                )
                return

            con.execute("DELETE FROM books WHERE id=?", (book_id,))

        messagebox.showinfo("Deleted", "Book removed from library system.")
        self.load_books(self.page)
        self.clear_book_form()

    def export_books_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files (*.csv)", "*.csv")],
            initialfile="btech_library_books.csv"
        )
        if not path:
            return

        with connect() as con:
            rows = con.execute("""
                SELECT b.id, b.title, b.author, b.category, b.isbn, b.year, b.copies,
                       MAX(0, b.copies - COALESCE((SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'), 0)) AS available
                FROM books b
                ORDER BY b.title ASC
            """).fetchall()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "Author", "Department", "ISBN", "Year", "Total Copies", "Available Copies"])
            for r in rows:
                writer.writerow(list(r))

        messagebox.showinfo("Export Successful", f"Book catalog exported to:\n{path}")

    # ================= STUDENT / MEMBER MANAGEMENT =================

    def members_screen(self):
        self.active_tab = "members"
        body = self.shell(
            "Student Directory & Membership",
            "Manage B.Tech students, roll numbers (USN), branches, and semester records"
        )

        form_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=12, highlightbackground=COLORS["border"], highlightthickness=1)
        form_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            form_card, text="🎓 Student Enrollment & Profile",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 8))

        self.student_vars = {
            "usn": tk.StringVar(),
            "name": tk.StringVar(),
            "department": tk.StringVar(value="CSE"),
            "semester": tk.StringVar(value="6"),
            "email": tk.StringVar(),
            "phone": tk.StringVar()
        }

        grid_f = tk.Frame(form_card, bg="#FFFFFF")
        grid_f.pack(fill="x")

        fields = [
            ("USN / Roll No *", "usn", 16),
            ("Full Name *", "name", 22),
            ("Branch / Dept", "department", 18),
            ("Semester", "semester", 10),
            ("College Email", "email", 24),
            ("Contact No.", "phone", 16),
        ]

        for label_text, key, width in fields:
            col_f = tk.Frame(grid_f, bg="#FFFFFF")
            col_f.pack(side="left", padx=(0, 10), fill="x", expand=True)

            tk.Label(
                col_f, text=label_text,
                font=("Segoe UI", 8, "bold"),
                bg="#FFFFFF", fg=COLORS["text_secondary"]
            ).pack(anchor="w", pady=(0, 2))

            if key == "department":
                ent = ttk.Combobox(col_f, textvariable=self.student_vars[key], values=ENGINEERING_DEPTS[1:], width=width)
                ent.pack(fill="x", ipady=2)
            elif key == "semester":
                ent = ttk.Combobox(col_f, textvariable=self.student_vars[key], values=[str(i) for i in range(1, 9)], width=width)
                ent.pack(fill="x", ipady=2)
            else:
                ent = tk.Entry(
                    col_f, textvariable=self.student_vars[key],
                    font=("Segoe UI", 9),
                    bg="#F8FAFC", fg="#0F172A",
                    relief="solid", bd=1, highlightthickness=1,
                    highlightcolor=COLORS["primary"], width=width
                )
                ent.pack(fill="x", ipady=3)

        btn_bar = tk.Frame(form_card, bg="#FFFFFF")
        btn_bar.pack(fill="x", pady=(10, 0))

        tk.Button(
            btn_bar, text="➕ Register Student",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.add_member
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_bar, text="✏️ Update Selected",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7", fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.update_member
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="🗑️ Delete Selected",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["danger"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.delete_member
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="🧹 Clear Fields",
            font=("Segoe UI", 9),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=10, pady=5,
            command=self.clear_student_form
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="📥 Export CSV",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["success"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self.export_students_csv
        ).pack(side="right")

        # Search & Filter
        search_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=8, highlightbackground=COLORS["border"], highlightthickness=1)
        search_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            search_card, text="Filter by Name, USN, or Branch:",
            font=("Segoe UI", 8, "bold"),
            bg="#FFFFFF", fg=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 8))

        self.student_search_var = tk.StringVar()
        st_ent = tk.Entry(
            search_card, textvariable=self.student_search_var,
            font=("Segoe UI", 9),
            bg="#F8FAFC", fg="#0F172A",
            relief="solid", bd=1, width=32
        )
        st_ent.pack(side="left", ipady=3, padx=(0, 10))
        st_ent.bind("<KeyRelease>", lambda e: self.load_members())

        # Table
        table_card = tk.Frame(body, bg="#FFFFFF", padx=1, pady=1, highlightbackground=COLORS["border"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)

        cols = ("id", "usn", "name", "dept", "sem", "email", "phone", "active_loans")
        self.member_tree = ttk.Treeview(table_card, columns=cols, show="headings", height=12)

        headings = [
            ("id", "ID", 50, "center"),
            ("usn", "USN / Roll No", 120, "center"),
            ("name", "Student Name", 200, "w"),
            ("dept", "Branch", 100, "center"),
            ("sem", "Sem", 55, "center"),
            ("email", "College Email", 220, "w"),
            ("phone", "Phone", 120, "center"),
            ("active_loans", "Active Loans", 90, "center")
        ]

        for col, heading, width, anchor in headings:
            self.member_tree.heading(col, text=heading)
            self.member_tree.column(col, width=width, anchor=anchor)

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.member_tree.yview)
        self.member_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.member_tree.pack(side="left", fill="both", expand=True)

        self.member_tree.bind("<<TreeviewSelect>>", self.select_member)

        self.load_members()

    def load_members(self):
        query = self.student_search_var.get().strip()
        sql = """
            SELECT m.id, m.usn, m.name, m.department, m.semester, m.email, m.phone,
                   (SELECT COUNT(*) FROM loans l WHERE l.member_id=m.id AND l.status='Borrowed') as active_loans
            FROM members m
        """
        params = []
        if query:
            sql += " WHERE (m.name LIKE ? OR m.usn LIKE ? OR m.department LIKE ?)"
            pat = f"%{query}%"
            params.extend([pat, pat, pat])
        sql += " ORDER BY m.name COLLATE NOCASE ASC"

        with connect() as con:
            rows = con.execute(sql, params).fetchall()

        self.member_tree.delete(*self.member_tree.get_children())
        for r in rows:
            self.member_tree.insert(
                "", "end",
                values=(r["id"], r["usn"] or "-", r["name"], r["department"], r["semester"], r["email"] or "-", r["phone"] or "-", r["active_loans"])
            )

    def select_member(self, event=None):
        sel = self.member_tree.selection()
        if not sel:
            return
        vals = self.member_tree.item(sel[0], "values")
        self.student_vars["usn"].set(vals[1] if vals[1] != "-" else "")
        self.student_vars["name"].set(vals[2])
        self.student_vars["department"].set(vals[3])
        self.student_vars["semester"].set(vals[4])
        self.student_vars["email"].set(vals[5] if vals[5] != "-" else "")
        self.student_vars["phone"].set(vals[6] if vals[6] != "-" else "")

    def clear_student_form(self):
        for v in self.student_vars.values():
            v.set("")
        self.student_vars["department"].set("CSE")
        self.student_vars["semester"].set("6")
        self.member_tree.selection_remove(self.member_tree.selection())

    def add_member(self):
        name = self.student_vars["name"].get().strip()
        usn = self.student_vars["usn"].get().strip() or None
        if not name:
            messagebox.showwarning("Validation", "Student Name is required.")
            return

        try:
            sem = int(self.student_vars["semester"].get() or "1")
        except ValueError:
            sem = 1

        try:
            with connect() as con:
                con.execute(
                    """INSERT INTO members (usn, name, department, semester, email, phone)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        usn, name,
                        self.student_vars["department"].get().strip(),
                        sem,
                        self.student_vars["email"].get().strip(),
                        self.student_vars["phone"].get().strip()
                    )
                )
            messagebox.showinfo("Success", f"Student '{name}' enrolled successfully.")
            self.load_members()
            self.clear_student_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Roll No", "A student with this USN / Roll number already exists.")

    def update_member(self):
        sel = self.member_tree.selection()
        if not sel:
            messagebox.showwarning("Select Student", "Please select a student from the list.")
            return
        student_id = int(self.member_tree.item(sel[0], "values")[0])
        name = self.student_vars["name"].get().strip()
        usn = self.student_vars["usn"].get().strip() or None
        if not name:
            messagebox.showwarning("Validation", "Student Name is required.")
            return

        try:
            sem = int(self.student_vars["semester"].get() or "1")
        except ValueError:
            sem = 1

        try:
            with connect() as con:
                con.execute(
                    """UPDATE members
                       SET usn=?, name=?, department=?, semester=?, email=?, phone=?
                       WHERE id=?""",
                    (
                        usn, name,
                        self.student_vars["department"].get().strip(),
                        sem,
                        self.student_vars["email"].get().strip(),
                        self.student_vars["phone"].get().strip(),
                        student_id
                    )
                )
            messagebox.showinfo("Updated", "Student profile updated.")
            self.load_members()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "USN collision or constraint violation.")

    def delete_member(self):
        sel = self.member_tree.selection()
        if not sel:
            messagebox.showwarning("Select Student", "Please select a student to delete.")
            return
        student_id = int(self.member_tree.item(sel[0], "values")[0])

        with connect() as con:
            active = con.execute("SELECT COUNT(*) FROM loans WHERE member_id=? AND status='Borrowed'", (student_id,)).fetchone()[0]
            if active:
                messagebox.showerror("Active Loans", "Cannot delete student with active borrowed books.")
                return

        if messagebox.askyesno("Confirm", "Permanently remove this student from library records?"):
            with connect() as con:
                con.execute("DELETE FROM members WHERE id=?", (student_id,))
            self.load_members()
            self.clear_student_form()

    def export_students_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files (*.csv)", "*.csv")],
            initialfile="btech_students_directory.csv"
        )
        if not path:
            return

        with connect() as con:
            rows = con.execute("SELECT id, usn, name, department, semester, email, phone FROM members ORDER BY usn ASC").fetchall()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "USN", "Name", "Department", "Semester", "Email", "Phone"])
            for r in rows:
                writer.writerow(list(r))

        messagebox.showinfo("Export Successful", f"Students exported to:\n{path}")

    # ================= ISSUE & RETURN (CIRCULATION) =================

    def loans_screen(self):
        self.active_tab = "loans"
        body = self.shell(
            "Circulation Desk • Book Issue & Return",
            f"Academic Loan Policy: {LOAN_PERIOD_DAYS} Days Duration | Fine: ₹{FINE_PER_DAY:.0f}/Day Overdue"
        )

        issue_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=14, highlightbackground=COLORS["border"], highlightthickness=1)
        issue_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            issue_card, text="🔄 Issue Book to Student",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 8))

        with connect() as con:
            books = con.execute("""
                SELECT b.id, b.title, b.category,
                       MAX(0, b.copies - COALESCE((SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'), 0)) as avail
                FROM books b
                ORDER BY b.title COLLATE NOCASE ASC
            """).fetchall()

            students = con.execute("""
                SELECT id, usn, name, department FROM members
                ORDER BY name COLLATE NOCASE ASC
            """).fetchall()

        self.loan_book_map = {
            f"[{row['avail']} left] {row['title']} ({row['category']})": row["id"]
            for row in books
        }

        self.loan_member_map = {
            f"{row['usn'] or 'ID:' + str(row['id'])} - {row['name']} ({row['department']})": row["id"]
            for row in students
        }

        self.loan_book_var = tk.StringVar()
        self.loan_member_var = tk.StringVar()

        i_grid = tk.Frame(issue_card, bg="#FFFFFF")
        i_grid.pack(fill="x")

        b_col = tk.Frame(i_grid, bg="#FFFFFF")
        b_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(b_col, text="Select Book (Title & Available Stock):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))
        b_box = ttk.Combobox(b_col, textvariable=self.loan_book_var, values=list(self.loan_book_map.keys()), width=45)
        b_box.pack(fill="x", ipady=3)

        s_col = tk.Frame(i_grid, bg="#FFFFFF")
        s_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(s_col, text="Select Student (USN & Branch):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))
        s_box = ttk.Combobox(s_col, textvariable=self.loan_member_var, values=list(self.loan_member_map.keys()), width=35)
        s_box.pack(fill="x", ipady=3)

        today_date = date.today()
        due_calculated = today_date + timedelta(days=LOAN_PERIOD_DAYS)

        d_col = tk.Frame(i_grid, bg="#FFFFFF")
        d_col.pack(side="left", padx=(0, 10))
        tk.Label(d_col, text="Due Date (14 Days):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))
        tk.Label(d_col, text=f"📅 {due_calculated.strftime('%d-%b-%Y')}", font=("Segoe UI", 9, "bold"), bg="#F1F5F9", fg=COLORS["primary"], padx=10, pady=5).pack(anchor="w")

        tk.Button(
            i_grid, text="⚡ Issue Book",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self.issue_book
        ).pack(side="left", pady=(14, 0))

        # Active Circulation Table
        circ_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=12, highlightbackground=COLORS["border"], highlightthickness=1)
        circ_card.pack(fill="both", expand=True)

        header_bar = tk.Frame(circ_card, bg="#FFFFFF")
        header_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            header_bar, text="📋 Active Borrowed & Circulation Records",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF", fg=COLORS["text_primary"]
        ).pack(side="left")

        tk.Button(
            header_bar, text="📥 Export Circulation Log",
            font=("Segoe UI", 8, "bold"),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=8, pady=3,
            command=self.export_loans_csv
        ).pack(side="right")

        tk.Button(
            header_bar, text="🔄 Refresh",
            font=("Segoe UI", 8, "bold"),
            bg="#E2E8F0", fg="#334155",
            relief="flat", cursor="hand2", padx=8, pady=3,
            command=self.load_loans
        ).pack(side="right", padx=6)

        cols = ("id", "book", "student", "usn", "issued", "due", "status", "fine")
        self.loan_tree = ttk.Treeview(circ_card, columns=cols, show="headings", height=10)

        col_defs = [
            ("id", "Loan ID", 65, "center"),
            ("book", "Book Title", 250, "w"),
            ("student", "Student Name", 170, "w"),
            ("usn", "USN / Branch", 130, "center"),
            ("issued", "Issue Date", 100, "center"),
            ("due", "Due Date", 100, "center"),
            ("status", "Status", 100, "center"),
            ("fine", "Est. Fine", 80, "center")
        ]

        for col, heading, width, anchor in col_defs:
            self.loan_tree.heading(col, text=heading)
            self.loan_tree.column(col, width=width, anchor=anchor)

        sb = ttk.Scrollbar(circ_card, orient="vertical", command=self.loan_tree.yview)
        self.loan_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.loan_tree.pack(side="left", fill="both", expand=True)

        self.loan_tree.tag_configure("borrowed", foreground="#92400E", background="#FFFBEB")
        self.loan_tree.tag_configure("overdue", foreground="#991B1B", background="#FEF2F2")
        self.loan_tree.tag_configure("returned", foreground="#065F46", background="#ECFDF5")

        bot_bar = tk.Frame(body, bg=COLORS["bg_main"])
        bot_bar.pack(fill="x", pady=(10, 0))

        tk.Button(
            bot_bar, text="✅ Return Selected Book",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["success"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=16, pady=7,
            command=self.return_book
        ).pack(side="left")

        tk.Button(
            bot_bar, text="⏳ Renew (+14 Days)",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7", fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, pady=7,
            command=self.renew_book
        ).pack(side="left", padx=8)

        self.load_loans()

    def issue_book(self):
        b_key = self.loan_book_var.get()
        s_key = self.loan_member_var.get()

        book_id = self.loan_book_map.get(b_key)
        member_id = self.loan_member_map.get(s_key)

        if not book_id or not member_id:
            messagebox.showwarning("Select Required", "Please select both a valid Book and a Student.")
            return

        with connect() as con:
            row = con.execute("""
                SELECT copies - (
                    SELECT COUNT(*) FROM loans WHERE book_id=? AND status='Borrowed'
                ) as available
                FROM books WHERE id=?
            """, (book_id, book_id)).fetchone()

            if not row or row["available"] <= 0:
                messagebox.showerror("Unavailable", "All copies of this book are currently checked out!")
                return

            active_student_loans = con.execute(
                "SELECT COUNT(*) FROM loans WHERE member_id=? AND status='Borrowed'",
                (member_id,)
            ).fetchone()[0]

            if active_student_loans >= 3:
                if not messagebox.askyesno(
                    "Borrow Limit Notice",
                    "This student already has 3 books issued (standard academic limit). Do you wish to override and issue anyway?"
                ):
                    return

            today = date.today()
            due = today + timedelta(days=LOAN_PERIOD_DAYS)

            con.execute("""
                INSERT INTO loans (book_id, member_id, issue_date, due_date, status, fine_amount)
                VALUES (?, ?, ?, ?, 'Borrowed', 0.0)
            """, (book_id, member_id, today.isoformat(), due.isoformat()))

        messagebox.showinfo("Book Issued", f"Book issued successfully.\nReturn Due Date: {due.strftime('%d-%b-%Y')}")
        self.loans_screen()

    def load_loans(self):
        with connect() as con:
            rows = con.execute("""
                SELECT l.id, b.title, m.name, m.usn, m.department, l.issue_date, l.due_date, l.status, l.fine_amount
                FROM loans l
                JOIN books b ON b.id=l.book_id
                JOIN members m ON m.id=l.member_id
                ORDER BY
                    CASE WHEN l.status='Borrowed' THEN 0 ELSE 1 END,
                    l.id DESC
            """).fetchall()

        self.loan_tree.delete(*self.loan_tree.get_children())
        today = date.today()

        for r in rows:
            st = r["status"]
            due_str = r["due_date"]
            fine = 0.0
            tag = "returned"

            if st == "Borrowed":
                tag = "borrowed"
                if due_str:
                    try:
                        due_d = date.fromisoformat(due_str)
                        if today > due_d:
                            overdue_days = (today - due_d).days
                            fine = overdue_days * FINE_PER_DAY
                            st = f"Overdue ({overdue_days}d)"
                            tag = "overdue"
                    except Exception:
                        pass

            fine_display = f"₹{fine:.0f}" if fine > 0 else "-"
            self.loan_tree.insert(
                "", "end",
                values=(
                    r["id"], r["title"], r["name"], f"{r['usn'] or '-'} ({r['department']})",
                    r["issue_date"], r["due_date"] or "-", st, fine_display
                ),
                tags=(tag,)
            )

    def return_book(self):
        sel = self.loan_tree.selection()
        if not sel:
            messagebox.showwarning("Select Loan", "Please select a loan record from the table first.")
            return

        vals = self.loan_tree.item(sel[0], "values")
        loan_id = int(vals[0])
        status = vals[6]

        if "Returned" in status:
            messagebox.showinfo("Already Returned", "This book was already recorded as returned.")
            return

        today = date.today()
        with connect() as con:
            row = con.execute("SELECT due_date FROM loans WHERE id=?", (loan_id,)).fetchone()
            fine = 0.0
            if row and row["due_date"]:
                try:
                    due_d = date.fromisoformat(row["due_date"])
                    if today > due_d:
                        fine = (today - due_d).days * FINE_PER_DAY
                except Exception:
                    pass

            fine_msg = f"\n\n⚠️ Overdue Fine Incurred: ₹{fine:.2f}" if fine > 0 else ""
            if not messagebox.askyesno("Confirm Return", f"Confirm return of book for Loan #{loan_id}?{fine_msg}"):
                return

            con.execute("""
                UPDATE loans
                SET status='Returned', return_date=?, fine_amount=?
                WHERE id=?
            """, (today.isoformat(), fine, loan_id))

        messagebox.showinfo("Success", f"Book marked as returned.{fine_msg}")
        self.load_loans()

    def renew_book(self):
        sel = self.loan_tree.selection()
        if not sel:
            messagebox.showwarning("Select Loan", "Please select an active loan to renew.")
            return

        vals = self.loan_tree.item(sel[0], "values")
        loan_id = int(vals[0])
        status = vals[6]

        if "Returned" in status:
            messagebox.showinfo("Cannot Renew", "Cannot renew a book that is already returned.")
            return

        new_due = date.today() + timedelta(days=LOAN_PERIOD_DAYS)
        with connect() as con:
            con.execute("UPDATE loans SET due_date=? WHERE id=?", (new_due.isoformat(), loan_id))

        messagebox.showinfo("Renewed", f"Loan extended by 14 days.\nNew Due Date: {new_due.strftime('%d-%b-%Y')}")
        self.load_loans()

    def export_loans_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files (*.csv)", "*.csv")],
            initialfile="btech_library_loans_log.csv"
        )
        if not path:
            return

        with connect() as con:
            rows = con.execute("""
                SELECT l.id, b.title, b.isbn, m.name, m.usn, m.department, l.issue_date, l.due_date, l.return_date, l.status, l.fine_amount
                FROM loans l
                JOIN books b ON b.id=l.book_id
                JOIN members m ON m.id=l.member_id
                ORDER BY l.id DESC
            """).fetchall()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Loan ID", "Book Title", "ISBN", "Student Name", "USN", "Department", "Issue Date", "Due Date", "Return Date", "Status", "Fine Amount (INR)"])
            for r in rows:
                writer.writerow(list(r))

        messagebox.showinfo("Export Successful", f"Circulation log exported to:\n{path}")

    # ================= OVERDUE & FINES REPORT =================

    def fines_screen(self):
        self.active_tab = "fines"
        body = self.shell(
            "Overdue Records & Fine Tracking",
            f"Automated Penalty Calculator: ₹{FINE_PER_DAY:.0f} per calendar day beyond due date"
        )

        today = date.today()
        today_str = today.isoformat()

        with connect() as con:
            rows = con.execute("""
                SELECT l.id, b.title, b.isbn, m.name, m.usn, m.department, m.phone, m.email,
                       l.issue_date, l.due_date
                FROM loans l
                JOIN books b ON b.id=l.book_id
                JOIN members m ON m.id=l.member_id
                WHERE l.status='Borrowed' AND l.due_date != '' AND l.due_date < ?
                ORDER BY l.due_date ASC
            """, (today_str,)).fetchall()

        total_fine_accumulated = 0.0
        overdue_data = []

        for r in rows:
            try:
                due_d = date.fromisoformat(r["due_date"])
                days_late = (today - due_d).days
                fine = days_late * FINE_PER_DAY
                total_fine_accumulated += fine
                overdue_data.append((
                    r["id"], r["title"], f"{r['name']} ({r['usn'] or '-'})",
                    r["department"], r["due_date"], f"{days_late} days",
                    f"₹{fine:.2f}", r["phone"] or "-"
                ))
            except Exception:
                pass

        stats_strip = tk.Frame(body, bg="#FFFFFF", padx=16, pady=12, highlightbackground=COLORS["border"], highlightthickness=1)
        stats_strip.pack(fill="x", pady=(0, 12))

        tk.Label(
            stats_strip, text="⚠️ TOTAL ACCUMULATED PENALTIES:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF", fg=COLORS["text_secondary"]
        ).pack(side="left")

        tk.Label(
            stats_strip, text=f"₹{total_fine_accumulated:,.2f}",
            font=("Segoe UI", 16, "bold"),
            bg="#FFFFFF", fg=COLORS["danger"]
        ).pack(side="left", padx=10)

        tk.Label(
            stats_strip, text=f"across {len(overdue_data)} overdue loan record(s)",
            font=("Segoe UI", 9),
            bg="#FFFFFF", fg=COLORS["text_secondary"]
        ).pack(side="left")

        table_card = tk.Frame(body, bg="#FFFFFF", padx=1, pady=1, highlightbackground=COLORS["border"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)

        cols = ("id", "title", "student", "dept", "due", "overdue_days", "fine", "contact")
        fines_tree = ttk.Treeview(table_card, columns=cols, show="headings", height=12)

        headings = [
            ("id", "Loan ID", 65, "center"),
            ("title", "Book Title", 240, "w"),
            ("student", "Student Name & USN", 200, "w"),
            ("dept", "Branch", 80, "center"),
            ("due", "Due Date", 100, "center"),
            ("overdue_days", "Late By", 90, "center"),
            ("fine", "Penalty (INR)", 110, "center"),
            ("contact", "Student Contact", 130, "center")
        ]

        for col, heading, width, anchor in headings:
            fines_tree.heading(col, text=heading)
            fines_tree.column(col, width=width, anchor=anchor)

        sb = ttk.Scrollbar(table_card, orient="vertical", command=fines_tree.yview)
        fines_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        fines_tree.pack(side="left", fill="both", expand=True)

        for item in overdue_data:
            fines_tree.insert("", "end", values=item)

        act_bar = tk.Frame(body, bg=COLORS["bg_main"])
        act_bar.pack(fill="x", pady=(10, 0))

        tk.Button(
            act_bar, text="📥 Export Overdue Report (CSV)",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary"], fg="#FFFFFF",
            relief="flat", cursor="hand2", padx=14, pady=6,
            command=lambda: self.export_fines_csv(overdue_data)
        ).pack(side="left")

    def export_fines_csv(self, data):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files (*.csv)", "*.csv")],
            initialfile="btech_overdue_fines_report.csv"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Loan ID", "Book Title", "Student & USN", "Branch", "Due Date", "Days Late", "Fine (INR)", "Contact"])
            for row in data:
                writer.writerow(row)

        messagebox.showinfo("Exported", f"Overdue fines report exported to:\n{path}")


# ================= APPLICATION ENTRY POINT =================

if __name__ == "__main__":
    init_db()

    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
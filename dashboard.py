import tkinter as tk
from tkinter import ttk
from datetime import date
from database import connect, COLORS, FINE_PER_DAY

def show_dashboard(app):
    app.active_tab = "dashboard"
    body = app.shell(
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

    # KPI Metric Cards
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

    dash_search_var = tk.StringVar()
    dash_entry = tk.Entry(
        s_bar, textvariable=dash_search_var,
        font=("Segoe UI", 10),
        bg="#F8FAFC", fg="#0F172A",
        relief="solid", bd=1, highlightthickness=1,
        highlightcolor=COLORS["primary"]
    )
    dash_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
    dash_entry.bind("<Return>", lambda e: app.books_screen(dash_search_var.get()))

    search_btn = tk.Button(
        s_bar, text="Search Catalog",
        font=("Segoe UI", 9, "bold"),
        bg=COLORS["primary"], fg="#FFFFFF",
        relief="flat", cursor="hand2", padx=14, pady=4,
        command=lambda: app.books_screen(dash_search_var.get())
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

    qa_card = tk.Frame(right_col, bg="#FFFFFF", padx=18, pady=14, highlightbackground=COLORS["border"], highlightthickness=1)
    qa_card.pack(fill="x", pady=(0, 14))

    tk.Label(
        qa_card, text="🚀 Rapid Circulation Actions",
        font=("Segoe UI", 11, "bold"),
        bg="#FFFFFF", fg=COLORS["text_primary"]
    ).pack(anchor="w", pady=(0, 10))

    actions = [
        ("➕  Issue Book to Student", COLORS["primary"], app.loans_screen),
        ("📥  Return Book / Collect Fine", COLORS["success"], app.loans_screen),
        ("📚  Register New Book", "#334155", lambda: app.books_screen()),
        ("🎓  Enroll New Student", "#475569", app.members_screen),
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
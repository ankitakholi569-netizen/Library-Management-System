import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
import csv
from database import connect, COLORS, LOAN_PERIOD_DAYS, FINE_PER_DAY

def show_loans_screen(app):
    app.active_tab = "loans"
    body = app.shell(
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

    loan_book_map = {f"[{row['avail']} left] {row['title']} ({row['category']})": row["id"] for row in books}
    loan_member_map = {f"{row['usn'] or 'ID:' + str(row['id'])} - {row['name']} ({row['department']})": row["id"] for row in students}

    loan_book_var = tk.StringVar()
    loan_member_var = tk.StringVar()

    i_grid = tk.Frame(issue_card, bg="#FFFFFF")
    i_grid.pack(fill="x")

    b_col = tk.Frame(i_grid, bg="#FFFFFF")
    b_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
    tk.Label(b_col, text="Select Book (Title & Available Stock):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))
    b_box = ttk.Combobox(b_col, textvariable=loan_book_var, values=list(loan_book_map.keys()), width=45)
    b_box.pack(fill="x", ipady=3)

    s_col = tk.Frame(i_grid, bg="#FFFFFF")
    s_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
    tk.Label(s_col, text="Select Student (USN & Branch):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))
    s_box = ttk.Combobox(s_col, textvariable=loan_member_var, values=list(loan_member_map.keys()), width=35)
    s_box.pack(fill="x", ipady=3)

    due_calculated = date.today() + timedelta(days=LOAN_PERIOD_DAYS)
    d_col = tk.Frame(i_grid, bg="#FFFFFF")
    d_col.pack(side="left", padx=(0, 10))
    tk.Label(d_col, text="Due Date (14 Days):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))
    tk.Label(d_col, text=f"📅 {due_calculated.strftime('%d-%b-%Y')}", font=("Segoe UI", 9, "bold"), bg="#F1F5F9", fg=COLORS["primary"], padx=10, pady=5).pack(anchor="w")

    def issue_book():
        book_id = loan_book_map.get(loan_book_var.get())
        member_id = loan_member_map.get(loan_member_var.get())

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
                if not messagebox.askyesno("Borrow Limit Notice", "This student already has 3 books issued (standard academic limit). Do you wish to override and issue anyway?"):
                    return

            today = date.today()
            due = today + timedelta(days=LOAN_PERIOD_DAYS)

            con.execute("""
                INSERT INTO loans (book_id, member_id, issue_date, due_date, status, fine_amount)
                VALUES (?, ?, ?, ?, 'Borrowed', 0.0)
            """, (book_id, member_id, today.isoformat(), due.isoformat()))

        messagebox.showinfo("Book Issued", f"Book issued successfully.\nReturn Due Date: {due.strftime('%d-%b-%Y')}")
        app.loans_screen()

    tk.Button(i_grid, text="⚡ Issue Book", font=("Segoe UI", 9, "bold"), bg=COLORS["primary"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=16, pady=6, command=issue_book).pack(side="left", pady=(14, 0))

    circ_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=12, highlightbackground=COLORS["border"], highlightthickness=1)
    circ_card.pack(fill="both", expand=True)

    header_bar = tk.Frame(circ_card, bg="#FFFFFF")
    header_bar.pack(fill="x", pady=(0, 8))

    tk.Label(header_bar, text="📋 Active Borrowed & Circulation Records", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg=COLORS["text_primary"]).pack(side="left")

    def export_loans_csv():
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files (*.csv)", "*.csv")], initialfile="btech_library_loans_log.csv")
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

    tk.Button(header_bar, text="📥 Export Circulation Log", font=("Segoe UI", 8, "bold"), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=8, pady=3, command=export_loans_csv).pack(side="right")
    tk.Button(header_bar, text="🔄 Refresh", font=("Segoe UI", 8, "bold"), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=8, pady=3, command=lambda: load_loans()).pack(side="right", padx=6)

    cols = ("id", "book", "student", "usn", "issued", "due", "status", "fine")
    loan_tree = ttk.Treeview(circ_card, columns=cols, show="headings", height=10)

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
        loan_tree.heading(col, text=heading)
        loan_tree.column(col, width=width, anchor=anchor)

    sb = ttk.Scrollbar(circ_card, orient="vertical", command=loan_tree.yview)
    loan_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    loan_tree.pack(side="left", fill="both", expand=True)

    loan_tree.tag_configure("borrowed", foreground="#92400E", background="#FFFBEB")
    loan_tree.tag_configure("overdue", foreground="#991B1B", background="#FEF2F2")
    loan_tree.tag_configure("returned", foreground="#065F46", background="#ECFDF5")

    def load_loans():
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

        loan_tree.delete(*loan_tree.get_children())
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
            loan_tree.insert(
                "", "end",
                values=(
                    r["id"], r["title"], r["name"], f"{r['usn'] or '-'} ({r['department']})",
                    r["issue_date"], r["due_date"] or "-", st, fine_display
                ),
                tags=(tag,)
            )

    def return_book():
        sel = loan_tree.selection()
        if not sel:
            messagebox.showwarning("Select Loan", "Please select a loan record from the table first.")
            return

        vals = loan_tree.item(sel[0], "values")
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

            con.execute("UPDATE loans SET status='Returned', return_date=?, fine_amount=? WHERE id=?", (today.isoformat(), fine, loan_id))

        messagebox.showinfo("Success", f"Book marked as returned.{fine_msg}")
        load_loans()

    def renew_book():
        sel = loan_tree.selection()
        if not sel:
            messagebox.showwarning("Select Loan", "Please select an active loan to renew.")
            return

        vals = loan_tree.item(sel[0], "values")
        loan_id = int(vals[0])
        status = vals[6]

        if "Returned" in status:
            messagebox.showinfo("Cannot Renew", "Cannot renew a book that is already returned.")
            return

        new_due = date.today() + timedelta(days=LOAN_PERIOD_DAYS)
        with connect() as con:
            con.execute("UPDATE loans SET due_date=? WHERE id=?", (new_due.isoformat(), loan_id))

        messagebox.showinfo("Renewed", f"Loan extended by 14 days.\nNew Due Date: {new_due.strftime('%d-%b-%Y')}")
        load_loans()

    bot_bar = tk.Frame(body, bg=COLORS["bg_main"])
    bot_bar.pack(fill="x", pady=(10, 0))

    tk.Button(bot_bar, text="✅ Return Selected Book", font=("Segoe UI", 10, "bold"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=16, pady=7, command=return_book).pack(side="left")
    tk.Button(bot_bar, text="⏳ Renew (+14 Days)", font=("Segoe UI", 9, "bold"), bg="#0284C7", fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=7, command=renew_book).pack(side="left", padx=8)

    load_loans()

def show_fines_screen(app):
    app.active_tab = "fines"
    body = app.shell(
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

    tk.Label(stats_strip, text="⚠️ TOTAL ACCUMULATED PENALTIES:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(side="left")
    tk.Label(stats_strip, text=f"₹{total_fine_accumulated:,.2f}", font=("Segoe UI", 16, "bold"), bg="#FFFFFF", fg=COLORS["danger"]).pack(side="left", padx=10)
    tk.Label(stats_strip, text=f"across {len(overdue_data)} overdue loan record(s)", font=("Segoe UI", 9), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(side="left")

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

    def export_fines_csv():
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files (*.csv)", "*.csv")], initialfile="btech_overdue_fines_report.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Loan ID", "Book Title", "Student & USN", "Branch", "Due Date", "Days Late", "Fine (INR)", "Contact"])
            for row in overdue_data:
                writer.writerow(row)
        messagebox.showinfo("Exported", f"Overdue fines report exported to:\n{path}")

    act_bar = tk.Frame(body, bg=COLORS["bg_main"])
    act_bar.pack(fill="x", pady=(10, 0))

    tk.Button(act_bar, text="📥 Export Overdue Report (CSV)", font=("Segoe UI", 9, "bold"), bg=COLORS["primary"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=14, pady=6, command=export_fines_csv).pack(side="left")
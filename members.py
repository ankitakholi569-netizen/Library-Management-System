import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from database import connect, COLORS, ENGINEERING_DEPTS

def show_members_screen(app):
    app.active_tab = "members"
    body = app.shell(
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

    student_vars = {
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

        tk.Label(col_f, text=label_text, font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 2))

        if key == "department":
            ent = ttk.Combobox(col_f, textvariable=student_vars[key], values=ENGINEERING_DEPTS[1:], width=width)
            ent.pack(fill="x", ipady=2)
        elif key == "semester":
            ent = ttk.Combobox(col_f, textvariable=student_vars[key], values=[str(i) for i in range(1, 9)], width=width)
            ent.pack(fill="x", ipady=2)
        else:
            ent = tk.Entry(col_f, textvariable=student_vars[key], font=("Segoe UI", 9), bg="#F8FAFC", fg="#0F172A", relief="solid", bd=1, width=width)
            ent.pack(fill="x", ipady=3)

    def clear_student_form():
        for v in student_vars.values():
            v.set("")
        student_vars["department"].set("CSE")
        student_vars["semester"].set("6")
        member_tree.selection_remove(member_tree.selection())

    def add_member():
        name = student_vars["name"].get().strip()
        usn = student_vars["usn"].get().strip() or None
        if not name:
            messagebox.showwarning("Validation", "Student Name is required.")
            return

        try:
            sem = int(student_vars["semester"].get() or "1")
        except ValueError:
            sem = 1

        try:
            with connect() as con:
                con.execute(
                    "INSERT INTO members (usn, name, department, semester, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (usn, name, student_vars["department"].get().strip(), sem, student_vars["email"].get().strip(), student_vars["phone"].get().strip())
                )
            messagebox.showinfo("Success", f"Student '{name}' enrolled successfully.")
            load_members()
            clear_student_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Roll No", "A student with this USN / Roll number already exists.")

    def update_member():
        sel = member_tree.selection()
        if not sel:
            messagebox.showwarning("Select Student", "Please select a student from the list.")
            return
        student_id = int(member_tree.item(sel[0], "values")[0])
        name = student_vars["name"].get().strip()
        usn = student_vars["usn"].get().strip() or None
        if not name:
            messagebox.showwarning("Validation", "Student Name is required.")
            return

        try:
            sem = int(student_vars["semester"].get() or "1")
        except ValueError:
            sem = 1

        try:
            with connect() as con:
                con.execute(
                    """UPDATE members
                       SET usn=?, name=?, department=?, semester=?, email=?, phone=?
                       WHERE id=?""",
                    (usn, name, student_vars["department"].get().strip(), sem, student_vars["email"].get().strip(), student_vars["phone"].get().strip(), student_id)
                )
            messagebox.showinfo("Updated", "Student profile updated.")
            load_members()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "USN collision or constraint violation.")

    def delete_member():
        sel = member_tree.selection()
        if not sel:
            messagebox.showwarning("Select Student", "Please select a student to delete.")
            return
        student_id = int(member_tree.item(sel[0], "values")[0])

        with connect() as con:
            active = con.execute("SELECT COUNT(*) FROM loans WHERE member_id=? AND status='Borrowed'", (student_id,)).fetchone()[0]
            if active:
                messagebox.showerror("Active Loans", "Cannot delete student with active borrowed books.")
                return

        if messagebox.askyesno("Confirm", "Permanently remove this student from library records?"):
            with connect() as con:
                con.execute("DELETE FROM members WHERE id=?", (student_id,))
            load_members()
            clear_student_form()

    def export_students_csv():
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files (*.csv)", "*.csv")], initialfile="btech_students_directory.csv")
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

    btn_bar = tk.Frame(form_card, bg="#FFFFFF")
    btn_bar.pack(fill="x", pady=(10, 0))

    tk.Button(btn_bar, text="➕ Register Student", font=("Segoe UI", 9, "bold"), bg=COLORS["primary"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=add_member).pack(side="left", padx=(0, 6))
    tk.Button(btn_bar, text="✏️ Update Selected", font=("Segoe UI", 9, "bold"), bg="#0284C7", fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=update_member).pack(side="left", padx=6)
    tk.Button(btn_bar, text="🗑️ Delete Selected", font=("Segoe UI", 9, "bold"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=delete_member).pack(side="left", padx=6)
    tk.Button(btn_bar, text="🧹 Clear Fields", font=("Segoe UI", 9), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=10, pady=5, command=clear_student_form).pack(side="left", padx=6)
    tk.Button(btn_bar, text="📥 Export CSV", font=("Segoe UI", 9, "bold"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=export_students_csv).pack(side="right")

    search_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=8, highlightbackground=COLORS["border"], highlightthickness=1)
    search_card.pack(fill="x", pady=(0, 10))

    tk.Label(search_card, text="Filter by Name, USN, or Branch:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).pack(side="left", padx=(0, 8))

    student_search_var = tk.StringVar()
    st_ent = tk.Entry(search_card, textvariable=student_search_var, font=("Segoe UI", 9), bg="#F8FAFC", fg="#0F172A", relief="solid", bd=1, width=32)
    st_ent.pack(side="left", ipady=3, padx=(0, 10))
    st_ent.bind("<KeyRelease>", lambda e: load_members())

    table_card = tk.Frame(body, bg="#FFFFFF", padx=1, pady=1, highlightbackground=COLORS["border"], highlightthickness=1)
    table_card.pack(fill="both", expand=True)

    cols = ("id", "usn", "name", "dept", "sem", "email", "phone", "active_loans")
    member_tree = ttk.Treeview(table_card, columns=cols, show="headings", height=12)

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
        member_tree.heading(col, text=heading)
        member_tree.column(col, width=width, anchor=anchor)

    sb = ttk.Scrollbar(table_card, orient="vertical", command=member_tree.yview)
    member_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    member_tree.pack(side="left", fill="both", expand=True)

    def select_member(event=None):
        sel = member_tree.selection()
        if not sel:
            return
        vals = member_tree.item(sel[0], "values")
        student_vars["usn"].set(vals[1] if vals[1] != "-" else "")
        student_vars["name"].set(vals[2])
        student_vars["department"].set(vals[3])
        student_vars["semester"].set(vals[4])
        student_vars["email"].set(vals[5] if vals[5] != "-" else "")
        student_vars["phone"].set(vals[6] if vals[6] != "-" else "")

    member_tree.bind("<<TreeviewSelect>>", select_member)

    def load_members():
        query = student_search_var.get().strip()
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

        member_tree.delete(*member_tree.get_children())
        for r in rows:
            member_tree.insert(
                "", "end",
                values=(r["id"], r["usn"] or "-", r["name"], r["department"], r["semester"], r["email"] or "-", r["phone"] or "-", r["active_loans"])
            )

    load_members()
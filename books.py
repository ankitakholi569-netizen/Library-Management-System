import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import importlib
from database import connect, COLORS, PAGE_SIZE, ENGINEERING_DEPTS

search_mod = importlib.import_module("Fast Search & Retrieval.search")

def show_books_screen(app, quick=""):
    app.active_tab = "books"
    body = app.shell(
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

    app.book_vars = {
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
            ent = ttk.Combobox(col_f, textvariable=app.book_vars[key], values=ENGINEERING_DEPTS[1:], width=width)
            ent.pack(fill="x", ipady=2)
        else:
            ent = tk.Entry(
                col_f, textvariable=app.book_vars[key],
                font=("Segoe UI", 9),
                bg="#F8FAFC", fg="#0F172A",
                relief="solid", bd=1, highlightthickness=1,
                highlightcolor=COLORS["primary"], width=width
            )
            ent.pack(fill="x", ipady=3)

    # Handlers
    def clear_book_form():
        for var in app.book_vars.values():
            var.set("")
        app.book_tree.selection_remove(app.book_tree.selection())

    def validate_book():
        title = app.book_vars["title"].get().strip()
        author = app.book_vars["author"].get().strip()
        if not title or not author:
            messagebox.showwarning("Required Fields", "Book Title and Author cannot be empty.")
            return None

        try:
            year_val = app.book_vars["year"].get().strip()
            year = int(year_val) if year_val else None
            copies = int(app.book_vars["copies"].get() or "1")
            if copies < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Year must be a valid number and Copies must be >= 0.")
            return None

        return (
            title, author,
            app.book_vars["category"].get().strip() or "General Engineering",
            app.book_vars["isbn"].get().strip() or None,
            year, copies
        )

    def add_book():
        data = validate_book()
        if not data:
            return
        try:
            with connect() as con:
                con.execute(
                    "INSERT INTO books (title, author, category, isbn, year, copies) VALUES (?, ?, ?, ?, ?, ?)",
                    data
                )
            messagebox.showinfo("Success", "New book added to library inventory.")
            load_books(0)
            clear_book_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate ISBN", "A book with this ISBN already exists.")

    def update_book():
        sel = app.book_tree.selection()
        if not sel:
            messagebox.showwarning("Select Book", "Please select a book from the table first.")
            return
        book_id = int(app.book_tree.item(sel[0], "values")[0])
        data = validate_book()
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
            load_books(app.page)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "ISBN collision or database integrity error.")

    def delete_book():
        sel = app.book_tree.selection()
        if not sel:
            messagebox.showwarning("Select Book", "Please select a book to delete.")
            return
        book_id = int(app.book_tree.item(sel[0], "values")[0])
        book_title = app.book_tree.item(sel[0], "values")[1]

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
        load_books(app.page)
        clear_book_form()

    def export_books_csv():
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

    # Buttons
    btn_bar = tk.Frame(form_card, bg="#FFFFFF")
    btn_bar.pack(fill="x", pady=(10, 0))

    tk.Button(btn_bar, text="➕ Add Book", font=("Segoe UI", 9, "bold"), bg=COLORS["primary"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=add_book).pack(side="left", padx=(0, 6))
    tk.Button(btn_bar, text="✏️ Update Selected", font=("Segoe UI", 9, "bold"), bg="#0284C7", fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=update_book).pack(side="left", padx=6)
    tk.Button(btn_bar, text="🗑️ Delete Selected", font=("Segoe UI", 9, "bold"), bg=COLORS["danger"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=delete_book).pack(side="left", padx=6)
    tk.Button(btn_bar, text="🧹 Clear Fields", font=("Segoe UI", 9), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=10, pady=5, command=clear_book_form).pack(side="left", padx=6)
    tk.Button(btn_bar, text="📥 Export CSV", font=("Segoe UI", 9, "bold"), bg=COLORS["success"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=5, command=export_books_csv).pack(side="right")

    # Search Card
    search_card = tk.Frame(body, bg="#FFFFFF", padx=16, pady=10, highlightbackground=COLORS["border"], highlightthickness=1)
    search_card.pack(fill="x", pady=(0, 10))

    app.search_var = tk.StringVar(value=quick or "")
    app.filter_category = tk.StringVar(value="All Departments")
    app.filter_avail = tk.StringVar(value="All Availability")
    app.sort_var = tk.StringVar(value="Title A–Z")

    f_left = tk.Frame(search_card, bg="#FFFFFF")
    f_left.pack(side="left", fill="x", expand=True)

    tk.Label(f_left, text="Search (Title / Author / ISBN):", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=0, sticky="w", padx=3)
    s_ent = tk.Entry(f_left, textvariable=app.search_var, font=("Segoe UI", 9), bg="#F8FAFC", fg="#0F172A", relief="solid", bd=1, highlightthickness=1, highlightcolor=COLORS["primary"], width=26)
    s_ent.grid(row=1, column=0, padx=3, pady=2, ipady=3)
    s_ent.bind("<KeyRelease>", lambda e: load_books(0))

    tk.Label(f_left, text="Department:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=1, sticky="w", padx=5)
    cat_box = ttk.Combobox(f_left, textvariable=app.filter_category, state="readonly", values=ENGINEERING_DEPTS, width=17)
    cat_box.grid(row=1, column=1, padx=5, pady=2)
    cat_box.bind("<<ComboboxSelected>>", lambda e: load_books(0))

    tk.Label(f_left, text="Stock Filter:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=2, sticky="w", padx=5)
    avail_box = ttk.Combobox(f_left, textvariable=app.filter_avail, state="readonly", values=["All Availability", "Available Only", "Currently Borrowed"], width=16)
    avail_box.grid(row=1, column=2, padx=5, pady=2)
    avail_box.bind("<<ComboboxSelected>>", lambda e: load_books(0))

    tk.Label(f_left, text="Sort By:", font=("Segoe UI", 8, "bold"), bg="#FFFFFF", fg=COLORS["text_secondary"]).grid(row=0, column=3, sticky="w", padx=5)
    sort_box = ttk.Combobox(f_left, textvariable=app.sort_var, state="readonly", values=["Title A–Z", "Title Z–A", "Author A–Z", "Year newest", "Year oldest"], width=14)
    sort_box.grid(row=1, column=3, padx=5, pady=2)
    sort_box.bind("<<ComboboxSelected>>", lambda e: load_books(0))

    def reset_search():
        app.search_var.set("")
        app.filter_category.set("All Departments")
        app.filter_avail.set("All Availability")
        app.sort_var.set("Title A–Z")
        load_books(0)

    reset_btn = tk.Button(f_left, text="Reset Filters", font=("Segoe UI", 8, "bold"), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=8, pady=3, command=reset_search)
    reset_btn.grid(row=1, column=4, padx=8, pady=2)

    # Table
    table_card = tk.Frame(body, bg="#FFFFFF", padx=1, pady=1, highlightbackground=COLORS["border"], highlightthickness=1)
    table_card.pack(fill="both", expand=True)

    cols = ("id", "title", "author", "category", "isbn", "year", "copies", "avail", "status")
    app.book_tree = ttk.Treeview(table_card, columns=cols, show="headings", height=11)

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
        app.book_tree.heading(col, text=heading)
        app.book_tree.column(col, width=width, anchor=anchor)

    sb = ttk.Scrollbar(table_card, orient="vertical", command=app.book_tree.yview)
    app.book_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    app.book_tree.pack(side="left", fill="both", expand=True)

    def select_book(event=None):
        sel = app.book_tree.selection()
        if not sel:
            return
        vals = app.book_tree.item(sel[0], "values")
        keys = ("title", "author", "category", "isbn", "year", "copies")
        for k, v in zip(keys, vals[1:7]):
            app.book_vars[k].set(v if v != "-" else "")

    app.book_tree.bind("<<TreeviewSelect>>", select_book)
    app.book_tree.tag_configure("in_stock", foreground="#065F46", background="#ECFDF5")
    app.book_tree.tag_configure("out_of_stock", foreground="#991B1B", background="#FEF2F2")

    # Pagination
    pag_bar = tk.Frame(body, bg=COLORS["bg_main"])
    pag_bar.pack(fill="x", pady=(8, 0))

    result_label = tk.Label(pag_bar, text="", font=("Segoe UI", 9), bg=COLORS["bg_main"], fg=COLORS["text_secondary"])
    result_label.pack(side="left")

    pag_controls = tk.Frame(pag_bar, bg=COLORS["bg_main"])
    pag_controls.pack(side="right")

    page_label = tk.Label(pag_controls, text="Page 1/1", font=("Segoe UI", 9, "bold"), bg=COLORS["bg_main"], fg=COLORS["text_primary"])

    def load_books(page=0):
        app.page = max(0, page)
        where, params, sort = search_mod.build_search_query(
            app.search_var.get(), app.filter_category.get(), app.filter_avail.get(), app.sort_var.get()
        )

        with connect() as con:
            total = con.execute("SELECT COUNT(*) FROM books b" + where, params).fetchone()[0]
            pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            app.page = min(app.page, pages - 1)
            offset = app.page * PAGE_SIZE

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

        app.book_tree.delete(*app.book_tree.get_children())
        for row in rows:
            avail = row["available"]
            status_text = "Available" if avail > 0 else "Issued Out"
            tag = "in_stock" if avail > 0 else "out_of_stock"

            app.book_tree.insert(
                "", "end",
                values=(
                    row["id"], row["title"], row["author"], row["category"],
                    row["isbn"] or "-", row["year"] or "-", row["copies"],
                    avail, status_text
                ),
                tags=(tag,)
            )

        result_label.config(text=f"Showing {len(rows)} of {total} book(s) • Page {app.page + 1} of {pages}")
        page_label.config(text=f"Page {app.page + 1}/{pages}")

    prev_btn = tk.Button(pag_controls, text="◀ Previous", font=("Segoe UI", 8, "bold"), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=8, pady=3, command=lambda: load_books(max(0, app.page - 1)))
    prev_btn.pack(side="left", padx=2)
    page_label.pack(side="left", padx=8)
    next_btn = tk.Button(pag_controls, text="Next ▶", font=("Segoe UI", 8, "bold"), bg="#E2E8F0", fg="#334155", relief="flat", cursor="hand2", padx=8, pady=3, command=lambda: load_books(app.page + 1))
    next_btn.pack(side="left", padx=2)

    load_books(0)
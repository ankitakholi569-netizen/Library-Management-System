import tkinter as tk
from tkinter import messagebox
from database import connect, COLORS

def show_login_screen(app):
    app.clear()
    app.root.configure(bg=COLORS["bg_sidebar"])

    card = tk.Frame(app.root, bg=COLORS["bg_card"], padx=40, pady=36, relief="flat")
    card.place(relx=0.5, rely=0.5, anchor="center")

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

    form_frame = tk.Frame(card, bg=COLORS["bg_card"])
    form_frame.pack(fill="x", pady=6)

    tk.Label(
        form_frame, text="Username / Staff ID",
        font=("Segoe UI", 9, "bold"),
        bg=COLORS["bg_card"], fg=COLORS["text_primary"]
    ).pack(anchor="w", pady=(4, 2))

    app.user_entry = tk.Entry(
        form_frame, font=("Segoe UI", 11),
        bg="#F8FAFC", fg="#0F172A",
        relief="solid", bd=1, highlightthickness=1,
        highlightcolor=COLORS["primary"], width=32
    )
    app.user_entry.pack(fill="x", ipady=5, pady=(0, 12))

    tk.Label(
        form_frame, text="Password",
        font=("Segoe UI", 9, "bold"),
        bg=COLORS["bg_card"], fg=COLORS["text_primary"]
    ).pack(anchor="w", pady=(4, 2))

    app.pass_entry = tk.Entry(
        form_frame, font=("Segoe UI", 11), show="•",
        bg="#F8FAFC", fg="#0F172A",
        relief="solid", bd=1, highlightthickness=1,
        highlightcolor=COLORS["primary"], width=32
    )
    app.pass_entry.pack(fill="x", ipady=5, pady=(0, 18))

    def perform_login():
        username = app.user_entry.get().strip()
        password = app.pass_entry.get()

        if not username or not password:
            messagebox.showwarning("Incomplete", "Please enter your username and password.")
            return

        with connect() as con:
            row = con.execute(
                "SELECT id, username, role FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()

        if row:
            app.user = row["username"]
            app.user_role = row["role"] or "Librarian"
            app.root.configure(bg=COLORS["bg_main"])
            app.dashboard()
        else:
            messagebox.showerror("Access Denied", "Invalid username or password. Check credentials.")

    def fill_demo():
        app.user_entry.delete(0, tk.END)
        app.user_entry.insert(0, "admin")
        app.pass_entry.delete(0, tk.END)
        app.pass_entry.insert(0, "admin123")
        app.pass_entry.focus_set()

    login_btn = tk.Button(
        card, text="Sign In to Portal →",
        font=("Segoe UI", 11, "bold"),
        bg=COLORS["primary"], fg="#FFFFFF",
        activebackground=COLORS["primary_dark"],
        activeforeground="#FFFFFF",
        relief="flat", cursor="hand2",
        pady=8, command=perform_login
    )
    login_btn.pack(fill="x", pady=(4, 14))

    demo_box = tk.Frame(card, bg="#F1F5F9", padx=12, pady=10, relief="flat")
    demo_box.pack(fill="x", pady=(6, 0))

    tk.Label(
        demo_box, text="⚡ Lab Viva Demo Access",
        font=("Segoe UI", 8, "bold"),
        bg="#F1F5F9", fg=COLORS["text_secondary"]
    ).pack(anchor="w")

    tk.Label(
        demo_box, text="Username: admin  |  Password: admin123",
        font=("Segoe UI", 9),
        bg="#F1F5F9", fg="#334155"
    ).pack(anchor="w", pady=(1, 6))

    autofill_btn = tk.Button(
        demo_box, text="Auto-fill Demo Credentials",
        font=("Segoe UI", 8, "bold"),
        bg="#E2E8F0", fg=COLORS["primary_dark"],
        activebackground="#CBD5E1", relief="flat",
        cursor="hand2", command=fill_demo
    )
    autofill_btn.pack(fill="x")

    app.pass_entry.bind("<Return>", lambda e: perform_login())
    app.user_entry.bind("<Return>", lambda e: app.pass_entry.focus_set())
    app.user_entry.focus_set()
    print("hello")

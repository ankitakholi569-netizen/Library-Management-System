
import tkinter as tk
from tkinter import ttk, messagebox


class LoginScreen:
    def __init__(self, app):
        self.app = app

    def show(self):
        self.app.clear()

        frame = ttk.Frame(self.app.root, padding=30)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            frame,
            text="Library Management System",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        ttk.Label(frame, text="Username").pack(anchor="w")
        self.username = ttk.Entry(frame, width=35)
        self.username.pack(pady=5)

        ttk.Label(frame, text="Password").pack(anchor="w")
        self.password = ttk.Entry(frame, width=35, show="*")
        self.password.pack(pady=5)

        ttk.Button(
            frame,
            text="Login",
            command=self.login
        ).pack(pady=15, fill="x")

        ttk.Label(
            frame,
            text="Demo: admin / admin123"
        ).pack()

    def login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if username == "admin" and password == "admin123":
            self.app.user = username
            self.app.show_dashboard()
        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password!"
            )
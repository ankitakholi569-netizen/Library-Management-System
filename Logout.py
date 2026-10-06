from tkinter import messagebox

def logout_user(app):
    if messagebox.askyesno("Confirm Sign Out", "Are you sure you want to sign out of CampusLib?"):
        app.user = None
        app.login_screen()
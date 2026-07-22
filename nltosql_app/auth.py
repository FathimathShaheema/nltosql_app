import tkinter as tk
from tkinter import messagebox
import sqlite3
from config import COLORS, DB_FILE, UI

class AuthPage(tk.Frame):
    def __init__(self, master, mode="login"):
        super().__init__(master, bg=COLORS["bg"])
        self.master = master
        self.mode = mode
        
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0); self.canvas.place(relwidth=1, relheight=1)
        self._draw_bg()

        self.card = tk.Frame(self, bg=COLORS["card"], padx=40, pady=40, highlightthickness=1, highlightbackground=COLORS["border"])
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=420)
        
        title = "WELCOME BACK" if mode == "login" else "CREATE ACCOUNT"
        tk.Label(self.card, text=title, bg=COLORS["card"], fg="white", font=("Segoe UI", 20, "bold")).pack(pady=(0, 10))
        tk.Label(self.card, text="Access your Data Intelligence Pro account", bg=COLORS["card"], fg=COLORS["sub"], font=("Segoe UI", 9)).pack(pady=(0, 30))

        self.f_u, self.u = UI.modern_entry(self.card, "USERNAME"); self.f_u.pack(fill="x", pady=10)
        if mode == "signup":
            self.f_e, self.e = UI.modern_entry(self.card, "EMAIL ADDRESS"); self.f_e.pack(fill="x", pady=10)
        self.f_p, self.p = UI.modern_entry(self.card, "PASSWORD", show="•"); self.f_p.pack(fill="x", pady=10)
        if mode == "signup":
            self.f_c, self.c = UI.modern_entry(self.card, "CONFIRM PASSWORD", show="•"); self.f_c.pack(fill="x", pady=10)

        btn_txt = "LOGIN TO DASHBOARD" if mode == "login" else "REGISTER NOW"
        UI.pill_btn(self.card, btn_txt, self.action).pack(fill="x", pady=30)

        footer_f = tk.Frame(self.card, bg=COLORS["card"]); footer_f.pack()
        tk.Label(footer_f, text="New user?" if mode == "login" else "Already have an account?", bg=COLORS["card"], fg=COLORS["sub"], font=("Segoe UI", 9)).pack(side="left")
        btn = tk.Label(footer_f, text=" Create Account" if mode == "login" else " Login here", bg=COLORS["card"], fg=COLORS["glow"], cursor="hand2", font=("Segoe UI", 9, "bold"))
        btn.pack(side="left"); btn.bind("<Button-1>", lambda e: master.show(SignupPage if mode == "login" else LoginPage))

    def _draw_bg(self):
        self.canvas.create_oval(-100, -100, 300, 300, fill="#1a1a4a", outline="")
        self.canvas.create_oval(1100, 700, 1500, 1100, fill="#0f172a", outline="")

    def action(self):
        u, p = self.u.get().strip(), self.p.get().strip()
        if self.mode == "signup":
            if not u or not p or not self.e.get().strip() or not self.c.get().strip():
                messagebox.showwarning("Warning", "All fields must be filled to create an account!"); return
        else:
            if not u or not p: messagebox.showwarning("Warning", "Fields cannot be empty!"); return
            
        try:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                if self.mode == "signup":
                    c.execute("SELECT * FROM users WHERE username=?", (u,))
                    if c.fetchone(): messagebox.showerror("Error", "Username exists!"); return
                    if p != self.c.get().strip(): messagebox.showerror("Error", "Passwords mismatch!"); return
                    import hashlib
                    phash = hashlib.sha256(p.encode()).hexdigest()
                    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (u, self.e.get().strip(), phash))
                    conn.commit()
                    messagebox.showinfo("Success", "Account created!")
                    self.master.current_user = u
                    from pages import MainPage
                    self.master.frames[MainPage].load_user_data()
                    self.master.show(MainPage)
                else:
                    import hashlib
                    phash = hashlib.sha256(p.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, phash))
                    if c.fetchone(): 
                        self.master.current_user = u
                        from pages import MainPage
                        self.master.frames[MainPage].load_user_data()
                        self.master.show(MainPage)
                    else: messagebox.showerror("Error", "Invalid credentials")
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")

class LoginPage(AuthPage): pass
class SignupPage(AuthPage): 
    def __init__(self, master): super().__init__(master, "signup")

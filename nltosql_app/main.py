import tkinter as tk
from config import COLORS
from auth import LoginPage, SignupPage
from pages import MainPage, GraphPage, TablePage

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Text-to-SQL Pro"); self.geometry("1400x950"); self.configure(bg=COLORS["bg"])
        self.df, self.db_conn, self.last_res, self.frames, self.current_user = None, None, None, {}, None
        for F in (LoginPage, SignupPage, MainPage, GraphPage, TablePage): f = F(self); self.frames[F] = f; f.place(relwidth=1, relheight=1)
        self.show(LoginPage)
    def show(self, p): self.frames[p].tkraise()

if __name__ == "__main__": App().mainloop()

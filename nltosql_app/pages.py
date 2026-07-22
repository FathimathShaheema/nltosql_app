import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, threading
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS, DB_FILE, LANG_CHARS, get_style, SQLGenerator

# ─── Full Views ─────────────────────────────────────────────────────────────
class FullViewPage(tk.Frame):
    def __init__(self, master, title):
        super().__init__(master, bg=COLORS["bg"]); self.master = master
        side = tk.Frame(self, bg=COLORS["sidebar"], width=280); side.pack(side="left", fill="y")
        tk.Label(side, text=title, bg=COLORS["sidebar"], fg=COLORS["glow"], font=("Segoe UI", 18, "bold")).pack(pady=40)
        tk.Button(side, text="⬅️ BACK", command=lambda: master.show(MainPage), bg=COLORS["accent"], fg="white", relief="flat", pady=10).pack(fill="x", padx=40)
        self.body = tk.Frame(self, bg=COLORS["bg"]); self.body.place(relx=0.5, rely=0.5, anchor="center", width=900, height=550)

class GraphPage(FullViewPage):
    def __init__(self, master): 
        super().__init__(master, "VISUALS")
        self.control_frame = tk.Frame(self.body, bg=COLORS["bg"]); self.control_frame.pack(fill="x", pady=(0, 10))
        self.graph_frame = tk.Frame(self.body, bg=COLORS["bg"]); self.graph_frame.pack(fill="both", expand=True)
        self.chart_type = tk.StringVar(value="Bar")
        tk.Label(self.control_frame, text="Graph Type:", bg=COLORS["bg"], fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        tk.OptionMenu(self.control_frame, self.chart_type, "Bar", "Line", "Pie", "Area", "Horizontal Bar", command=lambda x: self.render(self.master.last_res, x.lower())).pack(side="left")

    def render(self, df, k="bar"):
        self.chart_type.set("Horizontal Bar" if k == "horizontal bar" else k.title())
        if k == "horizontal bar": k = "barh"
        for w in self.graph_frame.winfo_children(): w.destroy()
        if df is None or df.empty: return
        nums = df.select_dtypes(include=['number']).columns.tolist()
        cats = df.select_dtypes(exclude=['number']).columns.tolist()
        if not nums: return
        plt.close('all')
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100); fig.patch.set_facecolor(COLORS["bg"]); ax.set_facecolor(COLORS["bg"])
        ax.tick_params(colors="white", labelsize=8); [s.set_color(COLORS["border"]) for s in ax.spines.values()]
        d = df.head(10)
        if cats: d = d.set_index(cats[0])
        if k == "pie": d.head(5).plot(kind='pie', y=nums[0], ax=ax, autopct='%1.1f%%', legend=False, textprops={'color':"w", 'fontsize':7})
        else: d.plot(kind=k, y=nums[0], ax=ax, color=COLORS["glow"])
        plt.tight_layout(); FigureCanvasTkAgg(fig, master=self.graph_frame).get_tk_widget().pack(expand=True)

class TablePage(FullViewPage):
    def __init__(self, master): 
        super().__init__(master, "DATA VIEW")
        self.tree = ttk.Treeview(self.body, show="headings"); self.tree.pack(fill="both", expand=True)
    def render(self, df):
        self.tree.delete(*self.tree.get_children()); self.tree["columns"] = list(df.columns)
        for c in df.columns: self.tree.heading(c, text=c); self.tree.column(c, width=150)
        for _, r in df.iterrows(): self.tree.insert("", "end", values=list(r))

# ─── Dashboard ──────────────────────────────────────────────────────────────
class MainPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLORS["bg"]); self.master = master; get_style()
        self.history = []
        side = tk.Frame(self, bg=COLORS["sidebar"], width=260); side.pack(side="left", fill="y")
        tk.Label(side, text="TEXT-to-SQL", bg=COLORS["sidebar"], fg=COLORS["glow"], font=("Segoe UI", 18, "bold")).pack(pady=40)
        self.hist_box = tk.Listbox(side, bg=COLORS["sidebar"], fg=COLORS["sub"], borderwidth=0, font=("Segoe UI", 9)); self.hist_box.pack(fill="both", expand=True, padx=15, pady=5)
        self.hist_box.bind("<<ListboxSelect>>", self.recall_hist)
        tk.Button(side, text="🗑️ CLEAR HISTORY", command=self.clear_history, bg=COLORS["sidebar"], fg=COLORS["err"], relief="flat", font=("Segoe UI", 8)).pack(fill="x", padx=40, pady=10)
        from auth import LoginPage
        tk.Button(side, text="LOGOUT", command=lambda: master.show(LoginPage), bg=COLORS["err"], fg="white", relief="flat", pady=10).pack(fill="x", padx=40, pady=20)

        work = tk.Frame(self, bg=COLORS["bg"]); work.pack(side="left", fill="both", expand=True, padx=30, pady=20)
        header = tk.Frame(work, bg=COLORS["bg"]); header.pack(fill="x", pady=(0, 15))
        tk.Label(header, text="Data Intelligence Dashboard", bg=COLORS["bg"], fg="white", font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Button(header, text="🚀 UPLOAD DATASET", command=self.upload, bg=COLORS["accent"], fg="white", relief="flat", padx=20, pady=8).pack(side="right")
        self.ana_lbl = tk.Label(work, text="Welcome! Upload a dataset to start.", bg=COLORS["card"], fg=COLORS["sub"], font=("Segoe UI", 9), padx=15, pady=8); self.ana_lbl.pack(fill="x", pady=(0, 10))

        card = tk.Frame(work, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"]); card.pack(fill="x", ipady=5)
        self.inp = tk.Text(card, height=2, bg=COLORS["sidebar"], fg="white", font=("Segoe UI", 12), padx=15, pady=8); self.inp.pack(fill="x", padx=20, pady=(10, 5))
        kb_f = tk.Frame(card, bg=COLORS["card"]); kb_f.pack(fill="x", padx=20)
        self.lang_var = tk.StringVar(value="English")
        ttk.OptionMenu(kb_f, self.lang_var, "English", "English", "Hindi", "Tamil", "Kannada", "Malayalam", command=self.draw_kb).pack(side="left")
        self.kb_keys = tk.Frame(kb_f, bg=COLORS["card"]); self.kb_keys.pack(side="left", padx=10); self.draw_kb()

        btn_row = tk.Frame(card, bg=COLORS["card"]); btn_row.pack(fill="x", padx=20, pady=10)
        tk.Button(btn_row, text="GENERATE", command=self.process, bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=40, pady=8).pack(side="left")
        tk.Button(btn_row, text="🔤 TRANSLATE TO ENG", command=self.translate_only, bg=COLORS["glow"], fg="black", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_row, text="CLEAR", command=lambda: self.inp.delete("1.0", "end"), bg=COLORS["sidebar"], fg=COLORS["sub"], relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_row, text="📥 DOWNLOAD", command=self.download, bg=COLORS["success"], fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_row, text="📄 FULL TABLE", command=lambda: [self.master.frames[TablePage].render(self.master.last_res), self.master.show(TablePage)] if self.master.last_res is not None else None, bg=COLORS["sidebar"], fg="white", relief="flat", padx=10).pack(side="right", padx=5)
        tk.Button(btn_row, text="📈 FULL GRAPH", command=lambda: [self.master.frames[GraphPage].render(self.master.last_res, self.chart_type.get().lower()), self.master.show(GraphPage)] if self.master.last_res is not None else None, bg=COLORS["sidebar"], fg="white", relief="flat", padx=10).pack(side="right")

        self.out = tk.Text(work, height=2, bg=COLORS["sidebar"], fg=COLORS["glow"], font=("Consolas", 10), padx=10, pady=10); self.out.pack(fill="x", pady=10)
        res_f = tk.Frame(work, bg=COLORS["bg"], height=250); res_f.pack(fill="x", pady=10); res_f.pack_propagate(False)
        self.t_card = tk.Frame(res_f, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"])
        self.t_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.tree = ttk.Treeview(self.t_card, show="headings"); self.tree.pack(fill="both", expand=True)
        self.c_card = tk.Frame(res_f, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"], width=300)
        self.c_card.pack(side="right", fill="y"); self.c_card.pack_propagate(False)
        self.chart_type = tk.StringVar(value="Bar")
        tk.OptionMenu(self.c_card, self.chart_type, "Bar", "Line", "Pie", "Area", "Horizontal Bar", command=lambda x: self.update_chart(self.master.last_res)).pack(fill="x")
        self.chart_body = tk.Frame(self.c_card, bg=COLORS["card"]); self.chart_body.pack(fill="both", expand=True)

    def draw_kb(self, *args):
        for w in self.kb_keys.winfo_children(): w.destroy()
        if self.lang_var.get() == "English": return
        chars = LANG_CHARS[self.lang_var.get()]
        for i in range(0, len(chars), 15):
            r = tk.Frame(self.kb_keys, bg=COLORS["card"]); r.pack()
            for c in chars[i:i+15]: 
                lbl = "SPACE" if c == " " else c
                tk.Button(r, text=lbl, bg=COLORS["sidebar"], fg="white", relief="flat", font=("Segoe UI", 8), command=lambda x=c: self.inp.insert("insert", x)).pack(side="left", padx=1)

    def upload(self):
        p = filedialog.askopenfilename()
        if p:
            self.master.df = pd.read_csv(p) if p.endswith('.csv') else pd.read_excel(p)
            self.master.db_conn = sqlite3.connect(":memory:", check_same_thread=False); self.master.df.to_sql("uploaded_data", self.master.db_conn, index=False, if_exists="replace")
            cols, rows = list(self.master.df.columns), len(self.master.df)
            txt = (f"✅ DATASET UPLOADED SUCCESSFULLY!\n📊 ANALYZED: {rows} rows found across {len(cols)} columns.\n🔍 Attributes: {', '.join(cols[:5])}...\n💡 SUGGESTED: 'Show me all records from {cols[0]}'")
            self.ana_lbl.config(text=txt, fg=COLORS["glow"]); messagebox.showinfo("Success", "Intelligence Engine Synced")

    def translate_only(self):
        t = self.inp.get("1.0", "end").strip()
        lang = self.lang_var.get()
        if t: threading.Thread(target=self._bg_trans, args=(t, lang), daemon=True).start()

    def _bg_trans(self, t, lang):
        eng_t = SQLGenerator.translate_to_eng(t, lang, force=True)
        self.master.after(0, lambda: self._up_trans(eng_t))

    def _up_trans(self, eng_t):
        self.inp.delete("1.0", "end"); self.inp.insert("1.0", eng_t)
        self.lang_var.set("English"); self.draw_kb()
        messagebox.showinfo("Translated Successfully", f"Your query has been translated to English:\n\n{eng_t}")

    def process(self):
        t = self.inp.get("1.0", "end").strip()
        lang = self.lang_var.get()
        if t: threading.Thread(target=self._bg, args=(t, lang), daemon=True).start()

    def _bg(self, t, lang):
        s = list(self.master.df.columns) if self.master.df is not None else []
        eng_t = SQLGenerator.translate_to_eng(t, lang)
        sql, _ = SQLGenerator.translate(eng_t, s)
        self.master.after(0, lambda: self._up(sql, t))

    def load_user_data(self):
        self.history = []
        try:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("SELECT query, sql FROM history WHERE username=? ORDER BY id DESC", (self.master.current_user,))
                for row in c.fetchall(): self.history.append({"q": row[0], "sql": row[1]})
        except: pass
        self.update_hist_ui()

    def _up(self, sql, t):
        self.out.delete("1.0", "end"); self.out.insert("1.0", sql)
        self.history.insert(0, {"q": t, "sql": sql})
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.cursor().execute("INSERT INTO history (username, query, sql) VALUES (?, ?, ?)", (self.master.current_user, t, sql))
                conn.commit()
        except: pass
        self.update_hist_ui()
        if self.master.db_conn:
            try:
                res = pd.read_sql_query(sql, self.master.db_conn); self.master.last_res = res
                self.tree.delete(*self.tree.get_children()); self.tree["columns"] = list(res.columns)
                for c in res.columns: self.tree.heading(c, text=c); self.tree.column(c, width=100)
                for _, r in res.iterrows(): self.tree.insert("", "end", values=list(r))
                self.update_chart(res)
            except: pass

    def update_chart(self, df):
        for w in self.chart_body.winfo_children(): w.destroy()
        if df is None or df.empty: return
        nums = df.select_dtypes(include=['number']).columns.tolist()
        cats = df.select_dtypes(exclude=['number']).columns.tolist()
        if not nums: return
        plt.close('all')
        fig, ax = plt.subplots(figsize=(2.2, 1.5), dpi=90); fig.patch.set_facecolor(COLORS["card"]); ax.set_facecolor(COLORS["card"])
        ax.tick_params(colors="white", labelsize=6); [s.set_color(COLORS["border"]) for s in ax.spines.values()]
        k, d = self.chart_type.get().lower(), df.head(10)
        if k == "horizontal bar": k = "barh"
        if cats: d = d.set_index(cats[0])
        if k == "pie": d.head(5).plot(kind='pie', y=nums[0], ax=ax, autopct='%1.1f%%', legend=False, textprops={'color':"w", 'fontsize':5})
        else: d.plot(kind=k, y=nums[0], ax=ax, color=COLORS["glow"])
        plt.tight_layout(); FigureCanvasTkAgg(fig, master=self.chart_body).get_tk_widget().pack(expand=True)

    def update_hist_ui(self):
        self.hist_box.delete(0, "end")
        for h in self.history[:20]: self.hist_box.insert("end", h['q'] if isinstance(h, dict) else str(h))

    def recall_hist(self, e):
        sel = self.hist_box.curselection()
        if sel:
            h = self.history[sel[0]]; q = h['q'] if isinstance(h, dict) else str(h)
            self.inp.delete("1.0", "end"); self.inp.insert("1.0", q)

    def clear_history(self):
        self.history = []
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.cursor().execute("DELETE FROM history WHERE username=?", (self.master.current_user,))
                conn.commit()
        except: pass
        self.update_hist_ui()

    def download(self):
        if self.master.last_res is not None:
            p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
            if p:
                try:
                    if p.endswith('.csv'): self.master.last_res.to_csv(p, index=False)
                    else: self.master.last_res.to_excel(p, index=False)
                    messagebox.showinfo("Success", "File saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {e}")

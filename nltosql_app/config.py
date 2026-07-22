import tkinter as tk
from tkinter import ttk
import json, os, re, hashlib, sqlite3, requests, threading

# ─── High-DPI Awareness ────────────────────────────────────────────────────
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except: pass

# ─── Premium Configuration ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "app_data.db")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, email TEXT, password TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, query TEXT, sql TEXT)")
        conn.commit()

init_db()

COLORS = {
    "bg": "#07071c", "sidebar": "#0b0b24", "card": "#121235", "accent": "#6366f1",
    "glow": "#00d2ff", "text": "#ffffff", "sub": "#94a3b8", "border": "#2d2d5f",
    "success": "#10b981", "err": "#ef4444", "input": "#1a1a4a"
}

LANG_CHARS = {
    "English": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
    "Hindi": "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह़ािीुूृेैोौ्0123456789 ",
    "Tamil": "அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநபமயரலவழளறனக்ாிீுூெேைொோௌ0123456789 ",
    "Kannada": "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹ್ರಾಿೀುೂೃೆೇೈೊೋೌ್0123456789 ",
    "Malayalam": "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹഹാിീുൂൃെേൈൊോൌ്0123456789 "
}

def get_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=COLORS["card"], foreground=COLORS["text"], fieldbackground=COLORS["card"], borderwidth=0, rowheight=25)
    style.configure("Treeview.Heading", background=COLORS["sidebar"], foreground=COLORS["text"], relief="flat", font=("Segoe UI", 9, "bold"))
    return style

class UI:
    @staticmethod
    def pill_btn(p, text, cmd, color=COLORS["accent"]):
        return tk.Button(p, text=text, command=cmd, bg=color, fg="white", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", padx=40, pady=12, activebackground=COLORS["glow"])
    
    @staticmethod
    def modern_entry(p, label, show=""):
        f = tk.Frame(p, bg=COLORS["card"])
        tk.Label(f, text=label, bg=COLORS["card"], fg=COLORS["sub"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
        e_f = tk.Frame(f, bg=COLORS["input"], padx=10, pady=8, highlightthickness=1, highlightbackground=COLORS["border"])
        e_f.pack(fill="x", pady=5)
        e = tk.Entry(e_f, bg=COLORS["input"], fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 11), show=show)
        e.pack(fill="x")
        return f, e

# ─── Logic (UNTOUCHED) ────────────────────────────────────────────────────
class SQLGenerator:
    @staticmethod
    def translate_to_eng(text, lang, force=False):
        if not force and (lang == "English" or not lang): return text
        try:
            prompt_lang = lang if lang != "English" else "foreign"
            payload = {
                "model": "qwen2.5:0.5b",
                "messages": [
                    {"role": "system", "content": "You are a professional translator. Translate the given text to English. Return ONLY the translation, no extra text, no greetings."},
                    {"role": "user", "content": f"Translate this {prompt_lang} text to English: {text}"}
                ],
                "stream": False
            }
            r = requests.post("http://localhost:11434/api/chat", timeout=12, json=payload)
            if r.status_code == 200: return r.json().get("message", {}).get("content", "").strip()
        except: pass
        return text

    @staticmethod
    def translate(text, schema=None):
        try:
            sys_prompt = (f"You are an expert AI Data Analyst. Translate the natural language query into SQLite SQL.\n"
                          f"Rules: Only return valid SQL. No explanations. Use table 'uploaded_data'.\n"
                          f"Accuracy Rules:\n"
                          f"- For text comparisons, use 'LIKE' with '%' for flexible matching.\n"
                          f"- Use 'LOWER(column) LIKE LOWER('%value%')' for case-insensitive searches.\n"
                          f"- NEVER replace spaces with underscores in column names or search values.\n"
                          f"- If a column name contains spaces, wrap it in double quotes (e.g., \"First Name\").\n"
                          f"Schema: {schema}")
            
            payload = {
                "model": "deepseek-coder:1.3b",
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"Query: {text}\nSQL:"}
                ],
                "stream": False
            }
            r = requests.post("http://localhost:11434/api/chat", timeout=12, json=payload)
            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "").strip()
                match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
                sql = match.group(1).strip() if match else re.sub(r'```sql|```', '', content).strip()
                if ';' in sql: sql = sql.split(';')[0] + ';'
                if sql.upper().startswith("SELECT"): return sql, True
        except: pass
        return "SELECT * FROM uploaded_data LIMIT 10;", False

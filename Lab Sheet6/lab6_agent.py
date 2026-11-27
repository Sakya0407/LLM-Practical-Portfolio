
import os, re, ast, glob, time, json, sqlite3, platform, subprocess, datetime as dt
import pyautogui
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_ollama import ChatOllama

TZ = "Asia/Colombo"

# --calculator--

def _safe_eval(expr):
    expr = expr.replace("×", "*").replace("x", "*").replace("÷", "/")
    node = ast.parse(expr, mode="eval")
    for n in ast.walk(node):
        if not isinstance(n, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                              ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd)):
            raise ValueError("Unsupported expression")
    return eval(compile(node, "<calc>", "eval"))

@tool
def open_calculator(expression: str) -> str:
    """Open Windows Calculator and type the arithmetic expression (e.g. '25*4'). Returns the result."""
    result = _safe_eval(expression)
    subprocess.Popen("calc.exe"); time.sleep(2)
    pyautogui.write(re.sub(r"\s", "", expression.replace("×", "*")), interval=0.15)
    pyautogui.press("enter")
    return f"Entered {expression} into Calculator. Result = {result}"

@tool
def get_date_time() -> str:
    """Get the current date and time."""
    return dt.datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

@tool
def open_notepad(text: str) -> str:
    """Open Windows Notepad and write the given text."""
    subprocess.Popen("notepad.exe"); time.sleep(1.5)
    pyautogui.write(text, interval=0.05)
    return "Notepad opened and text written."

@tool
def search_files(directory: str, pattern: str) -> str:
    """Search a directory (recursively) for files by name or extension, e.g. pattern='*.pdf'."""
    hits = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
    return "\n".join(hits[:50]) or "No files found."

@tool
def create_text_file(path: str, content: str) -> str:
    """Create a text file at the given path with the given content."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)
    return f"Created {path}"

@tool
def system_info() -> str:
    """Get operating system, processor and memory information."""
    try:
        import psutil; ram = f"{psutil.virtual_memory().total/1e9:.1f} GB"
    except ImportError:
        ram = "install psutil for RAM"
    return f"OS: {platform.platform()}\nCPU: {platform.processor()}\nRAM: {ram}"

# --SQLite long-term memory--
DB = "agent_memory.db"
with sqlite3.connect(DB) as c:
    c.execute("CREATE TABLE IF NOT EXISTS memory(id INTEGER PRIMARY KEY, fact TEXT UNIQUE, ts TEXT)")

def save_memory(fact):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR IGNORE INTO memory(fact, ts) VALUES(?,?)", (fact, dt.datetime.now().isoformat()))

def extract_memories(user_text):
    """Very small rule-based extractor for personal facts (name, studies, likes)."""
    pats = [r"(?:my name is|i am|i'm|im) ([A-Z][a-z]+)", r"i study ([\w\s]+)", r"i like ([\w\s]+)",
            r"my (?:favorite|favourite) ([\w\s]+ is [\w\s]+)"]
    found = []
    for p in pats:
        for m in re.finditer(p, user_text, re.I):
            found.append(m.group(0).strip())
    return found

@tool
def search_student_memory(query: str) -> str:
    """Retrieve previously stored information about the user (name, interests, etc.)."""
    words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
    with sqlite3.connect(DB) as c:
        rows = c.execute("SELECT fact FROM memory").fetchall()
    hits = [r[0] for r in rows if any(w in r[0].lower() for w in words)] or [r[0] for r in rows]
    return "\n".join(hits) or "No matching memories found."

# -- RAG tool --
@tool
def search_university_knowledge(query: str) -> str:
    """Search the university handbook/documents for courses, subjects, policies and programmes."""
    from rag_core import search_text
    return search_text(query)

# -- Part D: Google Calendar --

SCOPES = ["https://www.googleapis.com/auth/calendar"]
def _calendar():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file("token.json", SCOPES) if os.path.exists("token.json") else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES).run_local_server(port=0)
        open("token.json", "w").write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

@tool
def check_todays_schedule() -> str:
    """List today's Google Calendar events."""
    from zoneinfo import ZoneInfo
    now = dt.datetime.now(ZoneInfo(TZ))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    ev = _calendar().events().list(calendarId="primary", timeMin=start.isoformat(),
        timeMax=(start + dt.timedelta(days=1)).isoformat(), singleEvents=True, orderBy="startTime").execute()
    items = ev.get("items", [])
    return "\n".join(f"{e['start'].get('dateTime', e['start'].get('date'))} - {e.get('summary')}" for e in items) \
        or "No events today."

@tool
def create_calendar_event(summary: str, start_iso: str, end_iso: str) -> str:
    """Create a Google Calendar event. start_iso/end_iso like 2026-11-09T10:00:00+05:30 (Asia/Colombo)."""
    body = {"summary": summary, "start": {"dateTime": start_iso, "timeZone": TZ},
            "end": {"dateTime": end_iso, "timeZone": TZ}}
    e = _calendar().events().insert(calendarId="primary", body=body).execute()
    return f"Event created: {e.get('summary')} ({e.get('htmlLink')})"

# -- Agent loop --
TOOLS = [open_calculator, get_date_time, open_notepad, search_files, create_text_file, system_info,
         search_student_memory, search_university_knowledge, check_todays_schedule, create_calendar_event]
TOOL_MAP = {t.name: t for t in TOOLS}
llm = ChatOllama(model="llama3.2:3b", temperature=0).bind_tools(TOOLS)

SYSTEM = f"""You are an intelligent student assistant. Today is {dt.date.today()} (timezone {TZ}).
- Maths -> ALWAYS call open_calculator; never calculate yourself.
- Questions about the user (name, interests) -> search_student_memory.
- University courses/subjects/policies -> search_university_knowledge, answer only from its result.
- Schedule questions -> check_todays_schedule; new events -> create_calendar_event (ISO times with +05:30).
- Otherwise use the other tools when relevant, or answer directly."""

history = [SystemMessage(SYSTEM)]          

def run_agent(user_text):
    for fact in extract_memories(user_text): 
        save_memory(fact); print(f"[SAVED] {fact}")
    history.append(HumanMessage(user_text))
    for _ in range(5):                        
        ai = llm.invoke(history); history.append(ai)
        if not ai.tool_calls:
            return ai.content
        for call in ai.tool_calls:
            print(f"[TOOL SELECTED] {call['name']}\n[TOOL ARGUMENTS] {call['args']}")
            try:
                out = TOOL_MAP[call["name"]].invoke(call["args"])
            except Exception as e:
                out = f"Tool error: {e}"
            print(f"[TOOL RESULT] {str(out)[:300]}")
            history.append(ToolMessage(content=str(out), tool_call_id=call["id"]))
    return "Stopped after too many tool calls."

if __name__ == "__main__":
    print("INTELLIGENT STUDENT AI AGENT | short-term + SQLite memory | RAG | Google Calendar")
    while True:
        u = input("\nYou: ")
        if u.strip().lower() in ("exit", "quit"): break
        print("\nAgent:", run_agent(u))

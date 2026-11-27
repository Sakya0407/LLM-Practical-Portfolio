# Lab 06 – Building a Tool-Using AI Agent with Ollama

**PUSL 3205 – Large Language Models and Generative AI**

A local AI agent built with Python, LangChain and Ollama (Llama 3.2 3B). The agent chooses and runs tools by itself, remembers the user in SQLite, searches university documents with RAG, and manages Google Calendar.

## Tech stack

| Part | Tool |
|---|---|
| LLM | Llama 3.2 3B (Ollama, runs locally) |
| Framework | LangChain, langchain-ollama |
| Desktop control | pyautogui, pygetwindow |
| Memory | Short-term conversation memory + SQLite long-term memory |
| RAG | ChromaDB + Qwen3 Embedding (from Lab 05) |
| Calendar | Google Calendar API (OAuth) |

## Tools the agent can use

| Tool | What it does |
|---|---|
| `open_calculator` | Opens Windows Calculator and types the expression |
| `get_date_time` | Returns the current date and time |
| `search_student_memory` | Looks up facts saved about the user in SQLite |
| `search_university_knowledge` | RAG search over the PDF documents (source file and page shown) |
| `check_todays_schedule` | Reads today's events from Google Calendar |
| `create_calendar_event` | Creates a new Google Calendar event |

## How the agent works

1. The user types a request.
2. New user facts (for example, the name) are saved to SQLite.
3. The LLM picks a tool and its arguments (printed as `[TOOL SELECTED]` and `[TOOL ARGUMENTS]`).
4. The tool runs and returns a result.
5. The LLM writes the final answer from the tool result.

## Test results

| Query | Tool used | Result |
|---|---|---|
| Calculate 25 × 4 | `open_calculator` | Calculator opened and entered `25*4`, result **100** |
| What is the date today? | `get_date_time` | Returned Thursday, 19th November 2026 |
| Hi I'm Sakya, then what is my name? | `search_student_memory` | Saved the name, then answered "You are Sakya" |
| What are the main subjects in the course? | `search_university_knowledge` | Retrieved from `course work.pdf`, page 15 (see observations) |
| What is my schedule today? | `check_todays_schedule` | Google sign-in worked, "No events today" |
| Create an event "Study session" tomorrow 10:00 to 11:00 | `create_calendar_event` | Event created with correct start and end times (+05:30) |

## Key observations

- The 3B local model chose the right tool each time, and the printed tool name and arguments make the agent easy to follow.
- **Memory:** the agent recalled the user's name through the SQLite tool, so it does not treat each message as new.
- **Calendar:** the model turned "tomorrow from 10:00 to 11:00" into correct ISO date-times, and the event was created.
- **RAG weakness:** for "main subjects in the course" the retrieved chunk was unrelated (text about Turnitin), but the model still produced a plausible subject list that was not in the retrieved text. Small models can make up answers when retrieval is weak, so sources must be checked.
- Local models keep data on the machine, but they are slower and less reliable than large hosted models.

## Screenshots

### Calculator agent opening Windows Calculator
![Calculator agent](screenshots/01_calculator_agent.png)

### Calculator and date tools
![Date tool](screenshots/02_date_time_tool.png)

### Memory and RAG search
![Memory and RAG](screenshots/03_memory_and_rag.png)

### Google Calendar: check today's schedule
![Schedule](screenshots/04_calendar_schedule.png)

### Google Calendar: create an event
![Create event](screenshots/05_calendar_create_event.png)

## Setup

```powershell
.\rag_env\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull llama3.2:3b
python lab6_agent.py
```

For Google Calendar, create your own OAuth client in Google Cloud (enable the Calendar API) and save it as `credentials.json` in the project folder. **This file is not included in the repository.**

## Security note

`credentials.json`, `token.json` and `agent_memory.db` are excluded with `.gitignore` because they hold private login details and personal memory data.

## Author

Sakya – Data Science undergraduate, NSBM Green University

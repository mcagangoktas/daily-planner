# 🌅 Daily Growth Planner

An AI-powered daily planning assistant built with **Streamlit** and **Google Gemini**. It generates a detailed, hour-by-hour daily schedule from your goals, learns from your evening reflections, and tracks your productivity trends over time.

---

## ✨ Features

- **🌅 Morning Planner** — Turn a rough list of goals into a comprehensive, hour-by-hour schedule with execution tips for each block. The AI factors in your past performance and flags tasks that match your historical procrastination patterns.
- **🌌 Evening Reflection** — Log which tasks you actually completed, rate your energy/productivity for the day, and leave notes that feed back into future plans.
- **📊 Growth Dashboard** — Visualize your productivity and task-completion trends over time with KPI cards, a time-series chart, and a full historical data table.
- **🧠 Persistent Memory** — Your profile, interests, and full plan history are saved locally so the assistant gets smarter about your habits the more you use it.
- **🌍 Multi-language output** — Generate your plan in any language you specify.
- **🔄 Automatic fallback** — If the structured-output call to Gemini fails, the app automatically falls back to a plain-text generation call so you always get a plan.

---

## 🏗️ How It Works

1. **Sidebar — Profile.** Enter your name, role, and interests. This context is included in every prompt sent to Gemini so the plan feels personalized.
2. **Morning tab.** Enter your wake-up time, end time, and goals (one per line). The app builds a prompt combining your profile, your recent performance history, and today's goals, then asks Gemini to return a structured response (full schedule + an extracted task list) via a Pydantic schema.
3. **Evening tab.** Pick a date, check off which tasks you completed, rate your energy level, and save. This becomes part of the historical context for future morning plans.
4. **Dashboard tab.** Once you have at least one evening reflection logged, this tab renders your average productivity score, average success rate, and a line chart comparing energy vs. task completion over time.

All data is stored in a local `user_profile.json` file — no external database required.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key for Gemini

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
pip install -r requirements.txt
```

### Configuration

Create a `.streamlit/secrets.toml` file in the project root with your Gemini API key:

```toml
GEMINI_API_KEY = "your-api-key-here"
```

> ⚠️ **Never commit `secrets.toml` to GitHub.** It's already excluded via `.gitignore`.

### Run the app

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
.
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── secrets.toml             # Your local API key (not committed)
├── user_profile.json            # Auto-created — stores profile + plan history
├── .gitignore
└── README.md
```

---

## 🧰 Tech Stack

- [Streamlit](https://streamlit.io/) — web UI
- [Google Gen AI SDK](https://ai.google.dev/) — Gemini 2.5 / 2.0 Flash models
- [Pandas](https://pandas.pydata.org/) — analytics dashboard
- [Pydantic](https://docs.pydantic.dev/) — structured LLM output schema

---

## 📌 Notes

- Models used: `gemini-2.5-flash` (primary, with structured output) and `gemini-2.0-flash` (fallback).
- `user_profile.json` is created automatically on first run — no setup needed beyond your API key.

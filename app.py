import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
from google import genai

# --- 1. CONFIGURATION & SECURITY ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Please define GEMINI_API_KEY in your .streamlit/secrets.toml file.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
PROFILE_FILE = "user_profile.json"

# --- 2. DATA MANAGEMENT ---
def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "past_plans" not in data or data["past_plans"] is None:
                data["past_plans"] = []
            return data
    return {"name": "", "role": "", "interests": [], "past_plans": []}

def save_profile(profile_data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=4)

profile = load_profile()

# --- 3. LLM ORCHESTRATION ---
def generate_plan_with_fallback(prompt_text: str) -> str:
    """Manages model transitions with a robust fallback mechanism."""
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    for model in models:
        try:
            response = client.models.generate_content(model=model, contents=prompt_text)
            return response.text
        except Exception as e:
            st.warning(f"Call to {model} failed, trying the next available model...")
    st.error("No LLM models responded. Please check your connection or API key.")
    st.stop()

# --- 4. INTERFACE ---
tab_morning, tab_evening, tab_dashboard = st.tabs(
    ["🌅 Morning Planner", "🌌 Evening Reflection", "📊 Growth Dashboard"]
)

# Sidebar - User Profiling
st.sidebar.header("🤖 About Me")
new_name = st.sidebar.text_input("Name:", value=profile.get("name", ""))
new_role = st.sidebar.text_input("Role / Profession:", value=profile.get("role", ""))
interests_text = st.sidebar.text_area(
    "Interests (Comma-separated):", 
    value=", ".join(profile.get("interests", []))
)

if st.sidebar.button("Update Profile"):
    profile["name"] = new_name
    profile["role"] = new_role
    profile["interests"] = [i.strip() for i in interests_text.split(",") if i.strip()]
    save_profile(profile)
    st.sidebar.success("Profile updated successfully!")

# --- 5. MORNING PLANNER ---
with tab_morning:
    st.header("Generate Today's Schedule")
    today_str = datetime.now().strftime("%Y-%m-%d")
    st.date_input("Plan Date", value=datetime.now(), disabled=True)
    
    wake_time = st.text_input("What time did you wake up? (e.g., 08:00)", placeholder="08:00")
    end_time = st.text_input("Until what time should the plan run? (e.g., 23:00)", placeholder="23:00")
    goals = st.text_area(
        "What do you want to accomplish today? (Write each goal on a new line)", 
        placeholder="Write report\nGym workout\nSolve chess puzzles"
    )
    language = st.text_input("Output Language Preference:", value="English")

    if st.button("Generate Plan", type="primary"):
        if wake_time and goals:
            with st.spinner("Analyzing historical performance trends..."):
                
                profile["past_plans"] = [p for p in profile["past_plans"] if p.get("date") != today_str]
                
                historical_analysis = ""
                if profile["past_plans"]:
                    historical_analysis = "\nUser's Recent Performance Analysis:\n"
                    for p in profile["past_plans"][-3:]:
                        historical_analysis += f"- Date: {p.get('date')} | Planned Goals: {p.get('goals')}\n"
                        if "evening_feedback" in p:
                            fb = p["evening_feedback"]
                            historical_analysis += f"  [Feedback] Productivity Score: {fb.get('energy')}/5 | Deferred/Skipped Tasks: {fb.get('deferred')}\n"

                from pydantic import BaseModel, Field
                from typing import List

                class StudyPlannerResponse(BaseModel):
                    daily_schedule: str = Field(description="The complete hour-by-hour detailed schedule formatted beautifully with clear newlines between hours.")
                    extracted_tasks: List[str] = Field(description="A clean list of individual, atomic task names extracted from the raw user text for the evening checklist.")

                prompt = f"""
                You are an elite, highly sophisticated daily productivity coach and planning assistant. 
                Your core strength is breaking down vague goals into an extremely comprehensive, rigorous, and highly detailed hour-by-hour operational blueprint.
                
                Analyze the user profile and their past habits:
                User: {profile['name']} ({profile['role']})
                Interests: {', '.join(profile['interests'])}
                {historical_analysis}
                
                Today's Context:
                - Wake-up Time: {wake_time}
                - Raw Tasks/Goals Input: {goals}
                
                Strict Output Architecture Requirements:
                1. Provide an exhaustive, hour-by-hour granular breakdown starting from {wake_time} directly until {end_time}.
                2. Every single time block MUST be on its own line and separated by a blank line (double return). Do not use manual escape characters like '\\n' or weird delimiters. Use standard Markdown text formatting.
                3. DO NOT just list the task names. For EVERY single time block, provide 2-3 sentences of deep contextual explanation: why this task is placed here, execution strategy, micro-steps, and cognitive tips to maintain focus.
                4. CRITICAL: Identify if any raw tasks match the user's historical procrastination patterns. If so, inject a bold 'PROCRASTINATION WARNING' note next to that block.
                5. The entire comprehensive schedule must be written in {language}.
                """

                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config={"response_mime_type": "application/json", "response_schema": StudyPlannerResponse}
                    )
                    result = json.loads(response.text)
                    plan_text = result.get("daily_schedule", "")
                    parsed_goals_list = result.get("extracted_tasks", [])
                except Exception as e:
                    st.warning("Structured output failed, falling back to standard text generation...")
                    fallback_response = generate_plan_with_fallback(prompt)
                    plan_text = fallback_response
                    parsed_goals_list = [g.strip() for g in goals.split("\n") if g.strip()]
                
                new_entry = {
                    "date": today_str,
                    "wake_time": wake_time,
                    "goals": goals, 
                    "parsed_goals_list": parsed_goals_list, 
                    "generated_plan": plan_text
                }
                profile["past_plans"].append(new_entry)
                save_profile(profile)
                
                st.success("Plan successfully optimized!")
                st.markdown(plan_text)
        else:
            st.warning("Please fill in the required fields.")

# --- 6. EVENING REFLECTION ---
with tab_evening:
    st.header("Close & Reflect on the Day")
    
    past_list = profile.get("past_plans", [])
    
    if not past_list or len(past_list) == 0:
        st.info("No plans found to evaluate. Please generate a morning plan first.")
    else:
        dates = [p["date"] for p in past_list if "date" in p]
        
        if not dates:
            st.warning("No date entries found in historical logs.")
        else:
            selected_date = st.selectbox("Select the day to evaluate:", dates, index=len(dates)-1)
            target_plan = next((p for p in past_list if p.get("date") == selected_date), None)
            
            if target_plan:
                st.subheader("Goals Set for This Day:")
                st.info(target_plan["goals"])
                
                goals_list = target_plan.get("parsed_goals_list", [g.strip() for g in target_plan["goals"].split("\n") if g.strip()])

                st.markdown("### Feedback Form")
                completed = st.multiselect("Select tasks you successfully completed:", options=goals_list)
                deferred = [g for g in goals_list if g not in completed]
                
                if deferred:
                    st.warning(f"Deferred Tasks: {', '.join(deferred)}")
                    
                energy_level = st.slider("Rate your overall productivity/energy level today (1-5):", 1, 5, 3)
                notes = st.text_input("Any specific notes for your assistant?")

                if st.button("Save Log & Update Memory"):
                    target_plan["evening_feedback"] = {
                        "completed": completed,
                        "deferred": deferred,
                        "total_tasks_count": len(goals_list),
                        "completed_tasks_count": len(completed),
                        "energy": energy_level,
                        "notes": notes
                    }
                    save_profile(profile)
                    st.success(f"Data for {selected_date} has been committed to memory.")

# --- 7. DASHBOARD / METRICS ANALYTICS ---
with tab_dashboard:
    st.header("Personal Growth Analytics")
    plans = profile.get("past_plans", [])
    
    analytics_data = []
    for p in plans:
        if "evening_feedback" in p:
            fb = p["evening_feedback"]
            success_rate = (fb["completed_tasks_count"] / fb["total_tasks_count"]) * 100 if fb["total_tasks_count"] > 0 else 0
            
            analytics_data.append({
                "Date": p["date"],
                "Wake-up Time": p["wake_time"],
                "Energy/Productivity": fb["energy"],
                "Total Tasks": fb["total_tasks_count"],
                "Completed Tasks": fb["completed_tasks_count"],
                "Success Rate (%)": round(success_rate, 2)
            })

    if not analytics_data:
        st.info("Please submit at least one 'Evening Reflection' to render analytics charts.")
    else:
        df = pd.DataFrame(analytics_data).sort_values(by="Date")
        
        # KPI Cards
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total Days Tracked", value=len(df))
        col2.metric(label="Avg Productivity Score", value=f"{df['Energy/Productivity'].mean():.2f} / 5")
        col3.metric(label="Avg Success Rate", value=f"%{df['Success Rate (%)'].mean():.1f}")
        
        st.write("---")
        
        # Advanced Time-Series Chart
        st.subheader("📈 Time-Series Analysis: Energy vs. Success Rate")
        df_chart = df.set_index("Date")
        st.line_chart(df_chart[["Energy/Productivity", "Success Rate (%)"]])
        
        st.subheader("📋 Historical Data Matrix")
        st.dataframe(df)
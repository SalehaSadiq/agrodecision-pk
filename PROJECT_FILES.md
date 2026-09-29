# AGRODECISION PK — Complete Project File Contents
Generated from the runnable project.

## `app.py`

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone

from data.pakistan_data import PROVINCES, DISTRICTS, CROPS, PROBLEM_OPTIONS, DISTRICT_COORDS
from agents.context_agent import run_context_agent
from agents.weather_agent import run_weather_agent
from agents.crop_agent import run_crop_agent
from agents.intervention_agent import run_intervention_agent
from agents.cost_agent import run_cost_agent
from agents.feasibility_agent import run_feasibility_agent
from agents.critic_agent import run_critic_agent
from utils.llm import has_live_llm
from utils.report import build_report

st.set_page_config(page_title="AgroDecision PK", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {max-width: 1250px; padding-top: 2rem; padding-bottom: 3rem;}
.hero {padding: 1.3rem 1.5rem; border-radius: 18px; background: linear-gradient(135deg,#f4f8f1,#eef5e8); border: 1px solid #dbe8d3; margin-bottom: 1.2rem;}
.hero h1 {margin:0; font-size:2.35rem; color:#17351f;}
.hero p {margin:.35rem 0 0; color:#49624e; font-size:1.05rem;}
.gate {padding: 1.2rem; border: 2px solid #d64545; border-radius: 16px; background:#fff7f7;}
.decision {padding:1rem 1.2rem; border-radius:14px; border:1px solid #cfe1cf; background:#f7fbf6;}
.small-muted {color:#66756a; font-size:.9rem;}
.badge {display:inline-block; padding:.25rem .55rem; border-radius:999px; background:#edf4ea; font-size:.8rem; margin-right:.3rem;}
</style>
""", unsafe_allow_html=True)

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "decision" not in st.session_state:
    st.session_state.decision = None
if "more_info" not in st.session_state:
    st.session_state.more_info = None

st.markdown('<div class="hero"><h1>🌾 AGRODECISION PK</h1><p>Human-in-the-Loop Multi-Agent AI Decision Support for Pakistani Agriculture</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("System status")
    if has_live_llm():
        st.success("Live AI Mode")
    else:
        st.info("Demo Mode — using demonstration data")
    st.caption("AI investigates and compares. Humans decide.")
    st.divider()
    st.caption("Prototype for hackathon demonstration. Important agricultural decisions should be verified with qualified local agricultural or extension expertise.")

st.subheader("1 · Tell us about your farm")
col1, col2, col3 = st.columns(3)
with col1:
    province = st.selectbox("Province", PROVINCES, index=0)
    district_options = DISTRICTS[province]
    district_default = district_options.index("Lahore") if province == "Punjab" else 0
    district = st.selectbox("District", district_options, index=district_default)
with col2:
    crop = st.selectbox("Crop", CROPS, index=CROPS.index("Wheat"))
    farm_size = st.number_input("Farm size (acres)", min_value=0.1, max_value=10000.0, value=10.0, step=1.0)
with col3:
    problem = st.selectbox("What problem are you seeing?", PROBLEM_OPTIONS, index=PROBLEM_OPTIONS.index("Water may be insufficient"))
    water = st.selectbox("Water situation", ["Good", "Moderate", "Limited", "Not sure"], index=1)

col4, col5 = st.columns(2)
with col4:
    description = st.text_area("Describe what you are seeing (optional)", placeholder="For example: leaves are curling and the field has not been irrigated for several days.", height=100)
with col5:
    budget = st.number_input("Approximate budget (PKR)", min_value=0.0, max_value=100_000_000.0, value=50_000.0, step=5_000.0)
    labor = st.selectbox("Labor available", ["Low", "Moderate", "Good", "Not sure"], index=1)

run = st.button("🔎 Run Analysis", type="primary", use_container_width=True)

if run:
    coords = DISTRICT_COORDS.get(district, DISTRICT_COORDS["Lahore"])
    farm = {
        "province": province, "district": district, "crop": crop, "farm_size": farm_size,
        "problem": problem, "description": description.strip(), "water": water,
        "budget": budget, "labor": labor, "coords": coords,
    }
    progress = st.progress(0, text="Starting AgroDecision investigation...")
    try:
        context = run_context_agent(farm)
        progress.progress(15, text="✓ Farm Context Agent")
        weather = run_weather_agent(farm)
        progress.progress(30, text="✓ Weather & Climate Agent")
        crop_reasoning = run_crop_agent(farm, context, weather)
        progress.progress(45, text="✓ Crop & Biological Reasoning Agent")
        interventions = run_intervention_agent(farm, context, weather, crop_reasoning)
        progress.progress(60, text="✓ Intervention Agent")
        costed = run_cost_agent(farm, interventions)
        progress.progress(72, text="✓ Cost Agent")
        feasibility = run_feasibility_agent(farm, costed)
        progress.progress(86, text="✓ Feasibility Agent")
        critic = run_critic_agent(farm, context, weather, crop_reasoning, costed, feasibility)
        progress.progress(100, text="✓ AI Critic — investigation complete")
        st.session_state.analysis = {
            "farm": farm, "context": context, "weather": weather, "crop_reasoning": crop_reasoning,
            "interventions": costed, "feasibility": feasibility, "critic": critic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        st.session_state.decision = None
        st.session_state.more_info = None
    except Exception as exc:
        st.error("The analysis could not be completed. The app is designed to continue safely, but an unexpected error occurred.")
        st.caption(f"Technical detail: {exc}")

analysis = st.session_state.analysis
if analysis:
    farm = analysis["farm"]
    st.divider()
    st.subheader("2 · AgroDecision investigation")
    metrics = st.columns(4)
    metrics[0].metric("Crop", farm["crop"])
    metrics[1].metric("Farm", f'{farm["farm_size"]:g} acres')
    metrics[2].metric("Budget", f'PKR {farm["budget"]:,.0f}')
    metrics[3].metric("Mode", "Live AI" if has_live_llm() else "Demo")

    with st.expander("Farm Context", expanded=True):
        st.write(analysis["context"]["summary"])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Important factors**")
            for x in analysis["context"]["important_factors"]: st.write("• " + x)
        with c2:
            st.markdown("**Missing information / assumptions**")
            for x in analysis["context"]["missing_information"]: st.write("• " + x)

    with st.expander("Weather & Climate", expanded=True):
        w = analysis["weather"]
        st.caption(f'{w["label"]} · {w["source_type"]}')
        wc = st.columns(4)
        wc[0].metric("Temperature", f'{w["temperature_c"]:.1f} °C')
        wc[1].metric("Humidity", f'{w["humidity_pct"]:.0f}%')
        wc[2].metric("Recent rain", f'{w["recent_rain_mm"]:.1f} mm')
        wc[3].metric("Rain next 24h", f'{w["next_24h_rain_mm"]:.1f} mm')
        st.write(w["interpretation"])
        if w.get("daily"):
            df = pd.DataFrame(w["daily"])
            fig = px.bar(df, x="date", y="rain_mm", title="Recent / forecast precipitation (mm)")
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Crop & Biological Reasoning", expanded=True):
        cr = analysis["crop_reasoning"]
        st.write(cr["summary"])
        for i, cause in enumerate(cr["possible_causes"], 1):
            st.markdown(f"**Possible cause {i}: {cause['name']}** · Confidence: {cause['confidence']}")
            st.write(cause["why"])
        st.warning("This is not a definitive diagnosis. The system identifies possible explanations that should be verified in the field.")

    with st.expander("AI Critic", expanded=False):
        critic = analysis["critic"]
        st.markdown("**Key uncertainty**")
        st.write(critic["key_uncertainty"])
        st.markdown("**Missing information**")
        for x in critic["missing_information"]: st.write("• " + x)
        st.markdown("**Alternative explanation**")
        st.write(critic["alternative_explanation"])
        st.markdown("**What should be verified?**")
        for x in critic["verify"]: st.write("• " + x)
        st.markdown(f'**Confidence:** {critic["confidence"]}')

    st.subheader("3 · Options, costs & feasibility")
    options = analysis["interventions"]
    feas = analysis["feasibility"]
    tabs = st.tabs([f"Option {chr(65+i)}" for i in range(len(options))])
    for i, (tab, option) in enumerate(zip(tabs, options)):
        with tab:
            f = feas[i]
            a, b, c = st.columns(3)
            a.metric("Estimated cost", f'PKR {option["costs"]["total"]:,.0f}')
            b.metric("Feasibility", f["overall"])
            c.metric("Budget", f["budget_status"])
            st.markdown(f'### {option["name"]}')
            st.write(option["what_to_do"])
            st.markdown("**Why it may help**")
            st.write(option["why_it_may_help"])
            x, y = st.columns(2)
            with x:
                st.markdown("**Resources & timing**")
                st.write(option["resources"])
                st.write("Timing: " + option["timing"])
                st.markdown("**Potential benefit**")
                st.write(option["potential_benefit"])
            with y:
                st.markdown("**Risks & uncertainty**")
                st.write(option["risks"])
                st.write(option["uncertainty"])
            cost_df = pd.DataFrame({"Cost component": ["Material", "Labor", "Energy/fuel", "Equipment/operation", "Other"], "PKR": [option["costs"]["material"], option["costs"]["labor"], option["costs"]["energy"], option["costs"]["equipment"], option["costs"]["other"]]})
            st.dataframe(cost_df, hide_index=True, use_container_width=True)
            st.caption("Cost label: demonstration estimate unless explicitly identified as public/external data. Python performs the arithmetic.")

    st.subheader("Economic exposure")
    e = analysis["critic"].get("economic_exposure", {})
    ec1, ec2, ec3 = st.columns(3)
    ec1.metric("Estimated crop value", f'PKR {e.get("crop_value",0):,.0f}')
    ec2.metric("Expected crop loss", f'PKR {e.get("expected_loss",0):,.0f}')
    ec3.metric("Reference loss probability", f'{e.get("loss_probability",0)*100:.0f}%')
    st.caption("AI-generated estimates for decision support; not a yield or financial prediction.")

    st.markdown('<div class="gate">', unsafe_allow_html=True)
    st.header("🔴 HUMAN DECISION GATE")
    st.write("The AI has completed its analysis. **No intervention has been selected automatically.**")
    choices = [f'Approve Option {chr(65+i)}' for i in range(len(options))] + ["Modify an Option", "Reject All Options", "Request More Information"]
    selected = st.radio("What do you want to do?", choices, key="decision_choice")
    modification = ""
    if selected == "Modify an Option":
        opt_names = [f'Option {chr(65+i)} — {o["name"]}' for i,o in enumerate(options)]
        selected_opt = st.selectbox("Which option?", opt_names)
        modification = st.text_area("What would you change?", placeholder="Describe the change you want the human decision record to capture.")
    human_reasoning = st.text_area("Human reasoning (recommended)", placeholder="Why are you choosing, modifying, rejecting, or deferring these options?", key="human_reasoning")
    confirm_label = "CONFIRM HUMAN DECISION" if selected != "Modify an Option" else "CONFIRM MODIFIED DECISION"
    if st.button(confirm_label, type="primary", use_container_width=True, key="confirm_decision"):
        if selected == "Modify an Option" and not modification.strip():
            st.warning("Please describe the modification before confirming.")
        else:
            if selected == "Request More Information":
                info = analysis["critic"]["verify"]
                st.session_state.more_info = info
                st.session_state.decision = {"action": selected, "reasoning": human_reasoning, "human_modification": "", "timestamp": datetime.now(timezone.utc).isoformat()}
            else:
                st.session_state.decision = {"action": selected, "reasoning": human_reasoning, "human_modification": modification, "timestamp": datetime.now(timezone.utc).isoformat()}
                st.session_state.more_info = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.more_info:
    st.info("### INFORMATION NEEDED BEFORE DECISION\n\n" + "\n".join([f"• {x}" for x in st.session_state.more_info]))
    st.caption("Use the options above to review the evidence again, then return to the Human Decision Gate.")

if st.session_state.decision and st.session_state.decision["action"] != "Request More Information":
    d = st.session_state.decision
    st.divider()
    st.subheader("4 · DECISION RECORDED")
    st.markdown('<div class="decision">', unsafe_allow_html=True)
    st.write(f'**Farm:** {farm["district"]}, {farm["province"]} · {farm["farm_size"]:g} acres')
    st.write(f'**Crop:** {farm["crop"]}')
    st.write(f'**Reported problem:** {farm["problem"]}')
    st.write(f'**AI assessment:** {analysis["crop_reasoning"]["summary"]}')
    st.write("**Options considered:** " + ", ".join([f'Option {chr(65+i)} — {o["name"]}' for i,o in enumerate(options)]))
    st.write("**Estimated costs:** " + "; ".join([f'Option {chr(65+i)}: PKR {o["costs"]["total"]:,.0f}' for i,o in enumerate(options)]))
    st.write(f'**AI critic findings:** {analysis["critic"]["key_uncertainty"]}')
    st.write(f'**Human decision:** {d["action"]}')
    if d["human_modification"]:
        st.write(f'**Human modification:** {d["human_modification"]}')
    st.write(f'**Human reasoning:** {d["reasoning"] or "Not provided."}')
    st.write("**Decision source:** HUMAN USER")
    st.write(f'**Timestamp:** {d["timestamp"]}')
    st.markdown("### Final decision made by human user.")
    st.write("The AI only provided decision support.")
    st.markdown('</div>', unsafe_allow_html=True)
    report = build_report(analysis, d)
    st.download_button("⬇️ Download Decision Report", data=report, file_name="agrodecision_pk_decision_report.md", mime="text/markdown", use_container_width=True)

st.divider()
with st.expander("Sources & Assumptions"):
    st.markdown("**Public/external data**")
    st.write("Weather: Open-Meteo public weather API when available. District coordinates are approximate lookup values used only to query public weather data.")
    st.markdown("**Public-source context layer**")
    st.write("Pakistan Bureau of Statistics, Pakistan Meteorological Department, Ministry of National Food Security & Research, Pakistan Agricultural Research Council, and provincial agriculture departments are listed as potential public reference sources. The MVP does not claim to retrieve live content from all of them.")
    st.markdown("**Demonstration assumptions**")
    st.write("Intervention costs, crop-value assumptions, and loss assumptions are demonstration estimates unless explicitly marked as external data. They are not official market prices or predictions.")
    st.markdown("**Safety**")
    st.write("This prototype does not diagnose disease, prescribe chemical use, purchase inputs, control irrigation, or execute farm actions. Verify important decisions with qualified local agricultural or extension expertise.")

```

## `requirements.txt`

```text
streamlit==1.50.0
pandas==2.3.3
numpy==2.3.3
plotly==6.3.0
requests==2.32.5

```

## `README.md`

```markdown
# AGRODECISION PK

**Human-in-the-Loop Multi-Agent AI Decision Support for Pakistani Agriculture**

## Problem
Pakistani farmers and agricultural decision-makers often have to act under uncertainty around crop health, water, weather and intervention costs. This prototype turns a simple farm description into a structured investigation rather than an automatic prescription.

## Solution
AgroDecision PK uses lightweight Python agent modules to investigate farm context, retrieve public weather information, reason about possible crop risks, generate three alternatives, calculate transparent PKR costs, check feasibility, and challenge its own assumptions with an AI critic. The workflow then stops at a mandatory **Human Decision Gate**.

> **AI investigates and compares. Humans decide.**

## Architecture
```text
Simple farm inputs
      ↓
Farm Context Agent
      ↓
Weather & Climate Agent → Open-Meteo when available
      ↓
Crop & Biological Reasoning Agent
      ↓
Intervention Agent → 3 alternatives
      ↓
Cost Agent → Python arithmetic in PKR
      ↓
Feasibility Agent
      ↓
AI Critic
      ↓
🔴 HUMAN DECISION GATE
      ↓
Human approve / modify / reject / request information
      ↓
Decision record + downloadable Markdown report
```

Each agent is a real Python module. LangGraph is intentionally not required for this one-day MVP because ordinary modules are easier to deploy and debug on Streamlit Community Cloud.

## Pakistan relevance
- Provinces: Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan
- Representative Pakistani districts with an `Other district` fallback
- Crops: wheat, rice, maize, cotton, sugarcane, citrus, mango
- Currency: PKR
- District-based approximate coordinates for public weather lookup
- Public-source references to Pakistani agriculture institutions

## Demo and Live AI modes
If `OPENAI_API_KEY` is not available, the app runs in **Demo Mode** with deterministic demonstration reasoning and fallback weather. This is intentional: a judge can run the complete workflow without an API key.

If the key is present, the agent reasoning modules can use the configured OpenAI model. The arithmetic is still performed by Python, not the LLM.

### Secrets
Create `.streamlit/secrets.toml` locally or add the same values in Streamlit Community Cloud Secrets. Never commit the real file.

```toml
OPENAI_API_KEY = "your-key"
OPENAI_MODEL = "gpt-5.6-luna"
```

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud deployment
1. Create a GitHub repository and push this project.
2. Open Streamlit Community Cloud.
3. Create a new app and select the GitHub repository, branch and `app.py`.
4. In **Advanced settings / Secrets**, add `OPENAI_API_KEY` and optionally `OPENAI_MODEL`.
5. Deploy and copy the generated `streamlit.app` URL for the judges.

The app does not require a local server, Docker, database, hardware, IoT devices or files stored on your laptop after deployment.

## Limitations
- Weather is public API data when available and demo data when unavailable.
- Intervention prices are demonstration assumptions, not official live Pakistani market prices.
- Economic exposure is an illustrative calculation, not a yield forecast or financial prediction.
- The system does not diagnose disease or prescribe chemicals.
- The MVP does not retrieve live content from every Pakistani institution listed in its source layer.
- Field verification remains important.

## Future work
Satellite data, Urdu voice interaction, image-based crop assessment, provincial extension integration, live market prices, farm history, IoT and personalized farm records could be added later.

## Safety principle
The application does not autonomously buy inputs, control irrigation, contact suppliers, or execute a farm intervention. The final recorded decision is explicitly attributed to the human user.

```

## `HACKATHON_DEMO.md`

```markdown
# 3-Minute Hackathon Demo — AgroDecision PK

## 0:00 — Problem
"Agricultural decisions are often made with incomplete information. AgroDecision PK does not try to replace the farmer or extension worker. It investigates the situation, compares alternatives, makes uncertainty visible, and then stops for a human decision."

## 0:20 — Simple input
Use the pre-populated demo:
- Punjab
- Lahore
- Wheat
- 10 acres
- Water may be insufficient
- Moderate water
- PKR 50,000 budget
- Moderate labor

Say: "These are deliberately simple inputs. A farmer does not need to provide coordinates, soil chemistry or technical API parameters."

## 0:40 — Run analysis
Click **Run Analysis**.

Point to the progress sequence:
1. Farm Context
2. Weather
3. Crop Risk
4. Interventions
5. Cost Analysis
6. Feasibility
7. AI Critic

## 1:00 — Multi-agent investigation
Show the Farm Context and Weather sections. Explain that public weather is used when available and that the app clearly switches to demo weather if the public API fails.

Then open Crop & Biological Reasoning. Emphasize: "It says possible causes, not a diagnosis."

## 1:30 — Three alternatives
Show the three option tabs.

Explain that the third option can be a verification-first / monitor-and-learn path. The system does not assume that spending money is always necessary.

## 2:00 — Costs and economic exposure
Point to the transparent cost table and PKR totals.

Say: "The LLM does not do the arithmetic. Python calculates material, labor, energy, equipment and other costs. The assumptions are labelled as demonstration estimates."

## 2:20 — AI critic
Open the AI Critic.

Say: "A separate critic challenges assumptions, asks what evidence is missing, and can explicitly say that more information should be collected before intervention."

## 2:35 — HUMAN DECISION GATE
Scroll to the red section.

Say clearly:

> "This is the most important part. The AI has completed its analysis. No intervention has been selected automatically."

Select an option, or demonstrate **Modify an Option**. Enter human reasoning and click **CONFIRM HUMAN DECISION**.

## 2:55 — Final record
Show **DECISION RECORDED** and click **Download Decision Report**.

Finish with:

> **"AI investigates and compares. Humans decide."**

```

## `agents/__init__.py`

```python
"""Lightweight multi-agent modules for AgroDecision PK."""

```

## `agents/context_agent.py`

```python
from utils.llm import ask_llm_json


def run_context_agent(farm):
    fallback = {
        "summary": f"A {farm['farm_size']:g}-acre {farm['crop']} farm in {farm['district']}, {farm['province']} is reporting: {farm['problem']}. Water is {farm['water'].lower()} and the stated budget is PKR {farm['budget']:,.0f}.",
        "important_factors": [f"Reported issue: {farm['problem']}", f"Water availability: {farm['water']}", f"Available budget: PKR {farm['budget']:,.0f}", f"Labor availability: {farm['labor']}", "Crop stage and field-level measurements were not provided."],
        "missing_information": ["Crop growth stage", "Recent irrigation timing and amount", "Field inspection of symptoms", "Soil moisture or root-zone condition"],
    }
    prompt = f"""You are the Farm Context Agent for a Pakistani agriculture decision-support prototype. Return JSON only with keys summary, important_factors (array), missing_information (array). Do not diagnose. Farm: {farm}"""
    return ask_llm_json(prompt, fallback)

```

## `agents/weather_agent.py`

```python
from utils.weather import get_weather
from utils.llm import ask_llm_json


def run_weather_agent(farm):
    weather = get_weather(farm["district"], farm["coords"])
    fallback_interpretation = "The available weather context may contribute to the reported crop problem, but weather alone does not establish its cause. Field verification remains important."
    prompt = f"""You are the Weather & Climate Agent. Given this farm and weather record, write one concise interpretation explaining how the conditions may relate to the reported problem. Never claim weather proves causation. Return JSON with key interpretation. Farm={farm}; Weather={weather}"""
    out = ask_llm_json(prompt, {"interpretation": fallback_interpretation})
    weather["interpretation"] = out.get("interpretation", fallback_interpretation)
    return weather

```

## `agents/crop_agent.py`

```python
from utils.llm import ask_llm_json


def run_crop_agent(farm, context, weather):
    fallback = {
        "summary": "The symptoms are compatible with more than one explanation. The system therefore treats these as hypotheses rather than a diagnosis.",
        "possible_causes": [
            {"name": "Water stress or root-zone limitation", "confidence": "Moderate", "why": "The reported water situation and symptoms can be consistent with inadequate water availability."},
            {"name": "Weather-related stress", "confidence": "Low", "why": "Recent temperature, rainfall and atmospheric conditions can alter crop water demand."},
            {"name": "Pest, disease or nutrient-related stress", "confidence": "Low", "why": "Similar visible symptoms can arise from biological or nutritional causes and need field verification."},
        ],
    }
    prompt = f"""You are the Crop & Biological Reasoning Agent for Pakistani agriculture. Return JSON only with keys summary and possible_causes. possible_causes must contain exactly 3 objects with name, confidence (Low/Moderate/High), why. Do not diagnose or prescribe. Farm={farm}; Context={context}; Weather={weather}"""
    return ask_llm_json(prompt, fallback)

```

## `agents/intervention_agent.py`

```python
from utils.llm import ask_llm_json


def run_intervention_agent(farm, context, weather, crop_reasoning):
    fallback = [
        {"name": "Targeted irrigation check and adjustment", "what_to_do": "Verify soil/root-zone moisture and, if the field is genuinely dry, adjust irrigation to the crop's current need rather than irrigating uniformly without verification.", "why_it_may_help": "Addresses the reported water-risk hypothesis while using verification before spending heavily.", "resources": "Water access, basic field inspection, available labor.", "timing": "As soon as practical after verification.", "potential_benefit": "May reduce water-stress risk if insufficient water is confirmed.", "risks": "Unnecessary irrigation can waste water or worsen waterlogging.", "uncertainty": "Actual crop water need and soil moisture are unknown."},
        {"name": "Field inspection plus localized corrective action", "what_to_do": "Inspect representative plants and soil, identify whether symptoms are uniform or localized, then apply only the locally justified corrective action.", "why_it_may_help": "Separates water, pest, disease and nutrient hypotheses before committing resources.", "resources": "Labor and basic field inspection; local extension support if available.", "timing": "Within 24–48 hours where practical.", "potential_benefit": "May reduce the chance of treating the wrong cause.", "risks": "Requires time and may delay intervention.", "uncertainty": "Cause is not confirmed without field evidence."},
        {"name": "Monitor and collect more information", "what_to_do": "Record symptom distribution, inspect soil moisture, check irrigation history and monitor the field before purchasing inputs.", "why_it_may_help": "Creates evidence before spending money when the cause is uncertain.", "resources": "Farmer/labor time and simple observations.", "timing": "Monitor over the next 24–72 hours, depending on crop condition.", "potential_benefit": "Can reduce unnecessary expenditure and improve later decisions.", "risks": "Delay could be costly if severe stress is already developing.", "uncertainty": "Outcome depends on symptom progression and field observations."},
    ]
    prompt = f"""You are the Intervention Agent. Return a JSON array of exactly 3 alternatives for this Pakistani farm. Option 3 should be verification-first or monitor-and-learn when uncertainty is material. Each object must have name, what_to_do, why_it_may_help, resources, timing, potential_benefit, risks, uncertainty. Do not rank the options and do not prescribe chemicals. Farm={farm}; Reasoning={crop_reasoning}; Weather={weather}"""
    out = ask_llm_json(prompt, fallback)
    if isinstance(out, dict) and "options" in out: out = out["options"]
    return out if isinstance(out, list) and len(out) == 3 else fallback

```

## `agents/cost_agent.py`

```python
from utils.calculations import calculate_option_costs
from data.demo_data import COST_ASSUMPTIONS


def run_cost_agent(farm, interventions):
    results = []
    for i, option in enumerate(interventions):
        results.append({**option, "costs": calculate_option_costs(farm, i, COST_ASSUMPTIONS)})
    return results

```

## `agents/feasibility_agent.py`

```python

def run_feasibility_agent(farm, options):
    out = []
    for o in options:
        total = o["costs"]["total"]
        if total <= farm["budget"]: budget_status = "Within"
        elif total <= farm["budget"] * 1.25: budget_status = "Near"
        else: budget_status = "Above"
        if farm["water"] == "Limited" and "irrigation" in o["name"].lower(): water_status = "Constrained"
        elif farm["water"] == "Not sure": water_status = "Unknown"
        else: water_status = "Suitable"
        if farm["labor"] == "Low" and ("inspection" in o["name"].lower() or "monitor" in o["name"].lower()): labor_status = "Constrained"
        elif farm["labor"] == "Not sure": labor_status = "Unknown"
        else: labor_status = "Suitable"
        overall = "High" if budget_status == "Within" and water_status != "Constrained" and labor_status != "Constrained" else ("Moderate" if budget_status != "Above" else "Limited")
        out.append({"budget_status": budget_status, "water_status": water_status, "labor_status": labor_status, "overall": overall})
    return out

```

## `agents/critic_agent.py`

```python
from utils.llm import ask_llm_json
from utils.calculations import economic_exposure


def run_critic_agent(farm, context, weather, crop_reasoning, options, feasibility):
    exposure = economic_exposure(farm)
    fallback = {
        "key_uncertainty": "The reported symptoms have not been verified through a field inspection, and crop stage, soil moisture and irrigation history are incomplete.",
        "missing_information": ["Crop growth stage", "Soil/root-zone moisture", "Irrigation history", "Pattern of symptoms across the field"],
        "alternative_explanation": "Pest, disease or nutrient-related stress could produce overlapping visible symptoms.",
        "verify": ["Inspect representative plants and roots", "Check soil/root-zone moisture", "Review recent irrigation and rainfall", "Seek local extension or crop-specialist input if symptoms persist or worsen"],
        "confidence": "Moderate",
        "economic_exposure": exposure,
    }
    prompt = f"""You are a skeptical AI Critic. Challenge the analysis without selecting an option. Return JSON with key_uncertainty, missing_information array, alternative_explanation, verify array, confidence, economic_exposure. Farm={farm}; Context={context}; Weather={weather}; Crop={crop_reasoning}; Options={options}; Feasibility={feasibility}"""
    out = ask_llm_json(prompt, fallback)
    if not isinstance(out, dict): return fallback
    out["economic_exposure"] = exposure
    return out

```

## `data/__init__.py`

```python
"""Data configuration for AgroDecision PK."""

```

## `data/pakistan_data.py`

```python
PROVINCES = ["Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"]
DISTRICTS = {
    "Punjab": ["Lahore", "Faisalabad", "Multan", "Sahiwal", "Bahawalpur", "Rawalpindi", "Other district"],
    "Sindh": ["Hyderabad", "Sukkur", "Larkana", "Mirpur Khas", "Karachi", "Other district"],
    "Khyber Pakhtunkhwa": ["Peshawar", "Mardan", "Swat", "Dera Ismail Khan", "Other district"],
    "Balochistan": ["Quetta", "Sibi", "Turbat", "Khuzdar", "Other district"],
}
CROPS = ["Wheat", "Rice", "Maize", "Cotton", "Sugarcane", "Citrus", "Mango"]
PROBLEM_OPTIONS = [
    "Plants look weak", "Leaves are yellowing", "Leaves are wilting", "Growth is slower than expected",
    "Possible pest damage", "Possible disease symptoms", "Water may be insufficient", "Too much water / waterlogging", "I am not sure",
]
DISTRICT_COORDS = {
    "Lahore": (31.5204, 74.3587), "Faisalabad": (31.4504, 73.1350), "Multan": (30.1575, 71.5249), "Sahiwal": (30.6682, 73.1114), "Bahawalpur": (29.3956, 71.6836), "Rawalpindi": (33.5651, 73.0169),
    "Hyderabad": (25.3960, 68.3578), "Sukkur": (27.7244, 68.8228), "Larkana": (27.5600, 68.2264), "Mirpur Khas": (25.5251, 69.0159), "Karachi": (24.8607, 67.0011),
    "Peshawar": (34.0151, 71.5249), "Mardan": (34.1980, 72.0401), "Swat": (35.2227, 72.4258), "Dera Ismail Khan": (31.8626, 70.9019),
    "Quetta": (30.1798, 66.9750), "Sibi": (29.5430, 67.8773), "Turbat": (26.0023, 63.0434), "Khuzdar": (27.8000, 66.6167),
    "Other district": (31.5204, 74.3587),
}

```

## `data/demo_data.py`

```python
DEMO_WEATHER = {
    "temperature_c": 31.0, "humidity_pct": 45.0, "recent_rain_mm": 2.5, "next_24h_rain_mm": 0.8,
    "label": "DEMO WEATHER DATA", "source_type": "DEMO ASSUMPTION", "daily": [
        {"date": "Day -2", "rain_mm": 0.0}, {"date": "Day -1", "rain_mm": 2.5}, {"date": "Today", "rain_mm": 0.0}, {"date": "Day +1", "rain_mm": 0.8},
    ],
}
COST_ASSUMPTIONS = {
    "irrigation": {"material_per_acre": 500, "labor_per_acre": 900, "energy_per_acre": 650, "equipment_per_acre": 250, "other_per_acre": 100},
    "inspection": {"material_per_acre": 150, "labor_per_acre": 650, "energy_per_acre": 100, "equipment_per_acre": 150, "other_per_acre": 100},
    "monitor": {"material_per_acre": 50, "labor_per_acre": 350, "energy_per_acre": 50, "equipment_per_acre": 50, "other_per_acre": 50},
}

```

## `utils/__init__.py`

```python
"""Shared utilities for AgroDecision PK."""

```

## `utils/calculations.py`

```python
def calculate_option_costs(farm, option_index, assumptions):
    key = ["irrigation", "inspection", "monitor"][option_index]
    a = assumptions[key]
    acres = float(farm["farm_size"])
    material = round(acres * a["material_per_acre"])
    labor = round(acres * a["labor_per_acre"])
    energy = round(acres * a["energy_per_acre"])
    equipment = round(acres * a["equipment_per_acre"])
    other = round(acres * a["other_per_acre"])
    total = material + labor + energy + equipment + other
    return {"material": material, "labor": labor, "energy": energy, "equipment": equipment, "other": other, "total": total, "label": "Demonstration estimate"}


def economic_exposure(farm):
    # Transparent demonstration assumptions; intentionally conservative and clearly labelled.
    value_per_acre = {"Wheat": 120000, "Rice": 180000, "Maize": 140000, "Cotton": 170000, "Sugarcane": 220000, "Citrus": 300000, "Mango": 350000}.get(farm["crop"], 150000)
    crop_value = farm["farm_size"] * value_per_acre
    loss_probability = 0.30 if farm["problem"] in ["Water may be insufficient", "Leaves are wilting"] else 0.20
    expected_yield_loss_fraction = 0.15
    expected_loss = crop_value * loss_probability * expected_yield_loss_fraction
    return {"crop_value": round(crop_value), "loss_probability": loss_probability, "yield_loss_fraction": expected_yield_loss_fraction, "expected_loss": round(expected_loss), "label": "Demonstration estimate"}

```

## `utils/weather.py`

```python
import requests
from data.demo_data import DEMO_WEATHER


def get_weather(district, coords):
    lat, lon = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,precipitation", "hourly": "temperature_2m,relative_humidity_2m,precipitation", "past_days": 2, "forecast_days": 2, "timezone": "auto"}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        rain = hourly.get("precipitation", [])
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        current_precip = current.get("precipitation", 0) or 0
        recent = sum(float(x or 0) for x in rain[-24:]) if rain else current_precip
        next24 = sum(float(x or 0) for x in rain[-24:]) if rain else current_precip
        # Keep chart small and robust.
        daily = []
        for i in range(min(4, len(rain) // 24)):
            chunk = rain[i*24:(i+1)*24]
            daily.append({"date": times[i*24][:10] if i*24 < len(times) else f"Period {i+1}", "rain_mm": round(sum(float(x or 0) for x in chunk), 2)})
        return {"temperature_c": float(temp or 0), "humidity_pct": float(humidity or 0), "recent_rain_mm": round(recent, 2), "next_24h_rain_mm": round(next24, 2), "label": "LIVE WEATHER DATA", "source_type": "PUBLIC SOURCE — Open-Meteo", "daily": daily}
    except Exception:
        return {**DEMO_WEATHER, "label": "DEMO WEATHER DATA", "source_type": "DEMO ASSUMPTION — live weather unavailable"}

```

## `utils/llm.py`

```python
import json
import os
import requests
import streamlit as st


def get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def has_live_llm():
    return bool(get_secret("OPENAI_API_KEY"))


def _responses_text(data):
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]
    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if isinstance(content, dict) and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks)


def ask_llm_json(prompt, fallback):
    key = get_secret("OPENAI_API_KEY")
    if not key:
        return fallback
    model = get_secret("OPENAI_MODEL", "gpt-5.6-luna")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        payload = {"model": model, "input": prompt, "temperature": 0.2}
        r = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload, timeout=25)
        r.raise_for_status()
        text = _responses_text(r.json()).strip()
        if text.startswith("```"):
            text = text.replace("```json", "", 1).replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return fallback

```

## `utils/report.py`

```python
from datetime import datetime, timezone


def build_report(analysis, decision):
    f = analysis["farm"]
    lines = [
        "# AGRODECISION PK — Decision Report", "",
        "## Farm situation", f"- Location: {f['district']}, {f['province']}, Pakistan", f"- Crop: {f['crop']}", f"- Farm size: {f['farm_size']:g} acres", f"- Reported problem: {f['problem']}", f"- Water: {f['water']}", f"- Budget: PKR {f['budget']:,.0f}", f"- Labor: {f['labor']}", "",
        "## AI assessment", analysis["crop_reasoning"]["summary"], "",
        "## Weather", f"- Status: {analysis['weather']['label']}", f"- Temperature: {analysis['weather']['temperature_c']:.1f} °C", f"- Humidity: {analysis['weather']['humidity_pct']:.0f}%", f"- Recent rain: {analysis['weather']['recent_rain_mm']:.1f} mm", analysis["weather"]["interpretation"], "",
        "## Possible causes",
    ]
    for c in analysis["crop_reasoning"]["possible_causes"]:
        lines += [f"- {c['name']} — {c['confidence']}: {c['why']}"]
    lines += ["", "## Intervention alternatives"]
    for i, o in enumerate(analysis["interventions"]):
        lines += [f"### Option {chr(65+i)} — {o['name']}", o["what_to_do"], f"- Estimated cost: PKR {o['costs']['total']:,.0f} ({o['costs']['label']})", f"- Potential benefit: {o['potential_benefit']}", f"- Risks: {o['risks']}", f"- Uncertainty: {o['uncertainty']}"]
    lines += ["", "## AI critic", f"- Key uncertainty: {analysis['critic']['key_uncertainty']}", f"- Alternative explanation: {analysis['critic']['alternative_explanation']}", "- Verify:"]
    lines += [f"  - {x}" for x in analysis["critic"]["verify"]]
    lines += ["", "## Human decision", f"- Decision source: HUMAN USER", f"- Human decision: {decision['action']}", f"- Human modification: {decision.get('human_modification') or 'None'}", f"- Human reasoning: {decision.get('reasoning') or 'Not provided.'}", f"- Timestamp: {decision['timestamp']}", "", "## Assumptions & sources", "- Weather: Open-Meteo public weather API when available; otherwise demo data.", "- Cost figures and economic exposure are demonstration estimates, not official market prices or predictions.", "- District coordinates are approximate lookup values.", "- AI-generated decision support should be verified with qualified local agricultural or extension expertise.", "", "**Final decision made by human user. The AI only provided decision support.**"]
    return "\n".join(lines)

```

## `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#2f6b3f"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f4f8f1"
textColor = "#1f2d22"
font = "sans serif"

[server]
headless = true
maxUploadSize = 10

```

## `.streamlit/secrets.toml.example`

```example
OPENAI_API_KEY = "paste-your-key-in-Streamlit-Secrets"
OPENAI_MODEL = "gpt-5.6-luna"

```

## `.gitignore`

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
env/
.env
.streamlit/secrets.toml
.DS_Store

```

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

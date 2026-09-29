import streamlit as st

from data.pakistan import (
    PROVINCES,
    CROPS,
    SOIL_TYPES,
    WATER_SOURCES,
    WATER_AVAILABILITY,
    SEVERITY,
    AFFECTED_AREA,
    DURATION,
)
from data.demo_data import DEMO_SCENARIO

from agents.context_agent import run_context_agent
from agents.weather_agent import run_weather_agent
from agents.crop_agent import run_crop_agent
from agents.intervention_agent import run_intervention_agent
from agents.critic_agent import run_critic_agent
from agents.cost_agent import run_cost_agent
from agents.feasibility_agent import run_feasibility_agent

from utils.calculations import (
    calculate_intervention_cost,
    calculate_expected_crop_loss,
    calculate_economic_exposure,
    calculate_feasibility,
)
from utils.evidence import EvidenceTracker
from utils.report import generate_pdf_report

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AGRODECISION PK",
    page_icon="🌾",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "demo_loaded": False,
    "analysis_complete": False,
    "decision_confirmed": False,
    "decision": None,
    "human_modification": "",
    "human_reasoning": "",
    "evidence": [],
    "analysis": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def reset_analysis():
    st.session_state.analysis_complete = False
    st.session_state.decision_confirmed = False
    st.session_state.decision = None
    st.session_state.human_modification = ""
    st.session_state.human_reasoning = ""
    st.session_state.analysis = None
    st.session_state.evidence = []


def load_demo_values():
    st.session_state.demo_loaded = True


# =========================================================
# HEADER
# =========================================================

st.title("🌾 AGRODECISION PK")

st.subheader(
    "Human-in-the-Loop Multi-Agent AI Decision Support for Pakistani Agriculture"
)

st.markdown(
    """
### AI INVESTIGATES. AI COMPARES. HUMAN DECIDES.

This application provides agricultural decision support.
It does **not** automatically make or execute farm decisions.
"""
)


# =========================================================
# STATUS BAR
# =========================================================

status1, status2, status3 = st.columns(3)

with status1:
    ai_mode = "Demo Mode"
    if st.secrets.get("OPENAI_API_KEY", None):
        ai_mode = "Live AI"
    st.metric("AI Mode", ai_mode)

with status2:
    st.metric("Weather", "Live / Demo")

with status3:
    decision_status = (
        "Decision Recorded"
        if st.session_state.decision_confirmed
        else "Awaiting Human Decision"
    )
    st.metric("Decision", decision_status)


st.divider()


# =========================================================
# LANGUAGE
# =========================================================

st.header("🌐 Step 1 — Choose Your Language")

language = st.selectbox(
    "Farmer language",
    ["English", "اردو", "ਪੰਜਾਬੀ", "سنڌي"],
)

if language != "English":
    st.info(
        "Farmer-facing translation support is available for the interface. "
        "Scientific reasoning remains available in English under "
        "'View AI Reasoning'."
    )


# =========================================================
# DEMO
# =========================================================

with st.expander("🧪 Load Demonstration Scenario"):

    st.write(
        "Use this deterministic scenario to test the complete application "
        "without an OpenAI API key."
    )

    st.write(
        "**Punjab → Lahore → Wheat → Possible water stress**"
    )

    if st.button("Load Demo Scenario"):
        load_demo_values()
        st.success("Demo scenario loaded.")

    if st.session_state.demo_loaded:
        st.caption(
            "DEMONSTRATION DATA — NOT VERIFIED FOR REAL-WORLD "
            "AGRICULTURAL DECISIONS"
        )


# =========================================================
# FARM INFORMATION
# =========================================================

st.header("🌱 Step 2 — Your Farm")

default_province = (
    DEMO_SCENARIO["province"]
    if st.session_state.demo_loaded
    else "Punjab"
)

province = st.selectbox(
    "Province",
    list(PROVINCES.keys()),
    index=list(PROVINCES.keys()).index(default_province),
)

district_options = PROVINCES[province]

default_district = (
    DEMO_SCENARIO["district"]
    if st.session_state.demo_loaded
    and DEMO_SCENARIO["district"] in district_options
    else district_options[0]
)

district = st.selectbox(
    "District",
    district_options,
    index=district_options.index(default_district),
)

default_crop = (
    DEMO_SCENARIO["crop"]
    if st.session_state.demo_loaded
    else "Wheat"
)

crop = st.selectbox(
    "Crop",
    CROPS,
    index=CROPS.index(default_crop),
)

default_farm_size = (
    DEMO_SCENARIO["farm_size"]
    if st.session_state.demo_loaded
    else 10.0
)

farm_size = st.number_input(
    "Farm size (acres)",
    min_value=0.1,
    value=float(default_farm_size),
    step=0.5,
)

default_budget = (
    DEMO_SCENARIO["budget"]
    if st.session_state.demo_loaded
    else 50000.0
)

budget = st.number_input(
    "Available budget (PKR)",
    min_value=0.0,
    value=float(default_budget),
    step=1000.0,
)


# =========================================================
# PROBLEM
# =========================================================

st.header("🔎 Step 3 — Describe the Problem")

problem_text = st.text_area(
    "Describe what you are seeing",
    value=(
        DEMO_SCENARIO["problem"]
        if st.session_state.demo_loaded
        else ""
    ),
    height=120,
    placeholder=(
        "Example: The wheat leaves have been turning yellow "
        "for about one week."
    ),
)


# =========================================================
# STRUCTURED QUESTIONS
# =========================================================

with st.expander("Answer simple questions (optional)"):

    col1, col2 = st.columns(2)

    with col1:

        main_symptom = st.text_input(
            "Main symptom",
            value=(
                DEMO_SCENARIO["main_symptom"]
                if st.session_state.demo_loaded
                else ""
            ),
            placeholder="e.g. yellowing, wilting, spots",
        )

        duration = st.selectbox(
            "Duration",
            DURATION,
        )

        affected_area = st.selectbox(
            "Approximate affected area",
            AFFECTED_AREA,
        )

        severity = st.selectbox(
            "Severity",
            SEVERITY,
        )

        soil_type = st.selectbox(
            "Soil type",
            SOIL_TYPES,
        )

    with col2:

        water_source = st.selectbox(
            "Water source",
            WATER_SOURCES,
        )

        water_availability = st.selectbox(
            "Water availability",
            WATER_AVAILABILITY,
        )

        recent_irrigation = st.selectbox(
            "Recent irrigation?",
            ["Yes", "No", "Not sure"],
        )

        recent_fertilizer = st.selectbox(
            "Recent fertilizer application?",
            ["Yes", "No", "Not sure"],
        )

        recent_pesticide = st.selectbox(
            "Recent pesticide/fungicide application?",
            ["Yes", "No", "Not sure"],
        )


# =========================================================
# IMAGE
# =========================================================

st.header("📷 Optional Plant Image")

uploaded_image = st.file_uploader(
    "Upload JPG, JPEG or PNG",
    type=["jpg", "jpeg", "png"],
)

if uploaded_image:
    st.image(
        uploaded_image,
        caption="Uploaded plant image",
        width=400,
    )

    st.warning(
        "Image received for reference. "
        "The image alone is not treated as a confirmed diagnosis."
    )


# =========================================================
# ANALYSIS
# =========================================================

st.divider()

analyze = st.button(
    "🔬 ANALYZE FARM SITUATION",
    type="primary",
    use_container_width=True,
)

if analyze:

    reset_analysis()

    with st.status("Running agricultural analysis...", expanded=True) as status:

        st.write("✓ Farm Context Agent")

        farm_context = build_farm_context(
            province=province,
            district=district,
            crop=crop,
            farm_size=farm_size,
            budget=budget,
            problem=problem_text,
            main_symptom=main_symptom,
            duration=duration,
            affected_area=affected_area,
            severity=severity,
            soil_type=soil_type,
            water_source=water_source,
            water_availability=water_availability,
            recent_irrigation=recent_irrigation,
            recent_fertilizer=recent_fertilizer,
            recent_pesticide=recent_pesticide,
        )

        evidence_tracker = EvidenceTracker()

        evidence_tracker.add(
            source_type="Farmer-provided evidence",
            source_name="Farmer input",
            title="Farm and problem information",
            url="",
            claim_supported="Information reported by the farmer",
            information_used=problem_text or "No free-text problem supplied",
        )

        st.write("✓ Weather & Climate Agent")

        weather = get_weather_context(
            district=district,
            province=province,
        )

        if weather.get("source"):
            evidence_tracker.add(
                source_type=weather.get(
                    "source_type",
                    "External evidence",
                ),
                source_name=weather.get("source"),
                title=weather.get("title", "Weather information"),
                url=weather.get("url", ""),
                claim_supported="Weather/context information",
                information_used=str(weather),
                data_timestamp=weather.get("timestamp", ""),
            )

        st.write("✓ Crop & Biological Reasoning Agent")

        reasoning = generate_reasoning(
            farm_context=farm_context,
            weather=weather,
            demo_mode=st.session_state.demo_loaded,
        )

        st.write("✓ Intervention Generation")

        interventions = generate_interventions(
            farm_context=farm_context,
            reasoning=reasoning,
            budget=budget,
            demo_mode=st.session_state.demo_loaded,
        )

        st.write("✓ Cost Analysis")

        for intervention in interventions:

            intervention["costs"] = calculate_intervention_cost(
                material_unit_cost=intervention["cost_inputs"][
                    "material_unit_cost"
                ],
                material_quantity=intervention["cost_inputs"][
                    "material_quantity"
                ],
                labor_cost=intervention["cost_inputs"]["labor_cost"],
                energy_cost=intervention["cost_inputs"]["energy_cost"],
                other_cost=intervention["cost_inputs"]["other_cost"],
            )

            intervention["expected_crop_loss"] = (
                calculate_expected_crop_loss(
                    probability_of_loss=intervention[
                        "economic_inputs"
                    ]["probability_of_loss"],
                    expected_yield_loss=intervention[
                        "economic_inputs"
                    ]["expected_yield_loss"],
                    crop_value=intervention[
                        "economic_inputs"
                    ]["crop_value"],
                )
            )

            intervention["economic_exposure"] = (
                calculate_economic_exposure(
                    intervention_cost=intervention["costs"]["total"],
                    expected_crop_loss=intervention[
                        "expected_crop_loss"
                    ],
                )
            )

            intervention["feasibility"] = calculate_feasibility(
                budget=budget,
                total_cost=intervention["costs"]["total"],
                water_availability=water_availability,
                labor_level="Moderate",
            )

        st.write("✓ Critic Review")

        critic = generate_critic(
            farm_context=farm_context,
            reasoning=reasoning,
            interventions=interventions,
            weather=weather,
        )

        status.update(
            label="Analysis complete",
            state="complete",
        )

    st.session_state.analysis = {
        "farm_context": farm_context,
        "weather": weather,
        "reasoning": reasoning,
        "interventions": interventions,
        "critic": critic,
        "language": language,
        "uploaded_image": bool(uploaded_image),
    }

    st.session_state.evidence = evidence_tracker.items
    st.session_state.analysis_complete = True


# =========================================================
# RESULTS
# =========================================================

if st.session_state.analysis_complete:

    analysis = st.session_state.analysis

    st.divider()

    st.header("🌦️ Weather & Agricultural Context")

    weather = analysis["weather"]

    if weather.get("demo"):
        st.warning(
            "DEMO WEATHER DATA — NOT VERIFIED FOR REAL-WORLD DECISIONS"
        )

    st.write(weather.get("summary", "Weather information unavailable."))

    st.divider()

    st.header("🧬 Possible Causes")

    st.caption(
        "These are hypotheses, not confirmed diagnoses."
    )

    for cause in analysis["reasoning"]["possible_causes"]:

        with st.container(border=True):

            st.subheader(cause["name"])

            st.write(cause["explanation"])

            st.write(
                f"**Confidence:** {cause['confidence']}"
            )

            st.write(
                f"**Supporting evidence:** "
                f"{cause['supporting_evidence']}"
            )

            st.write(
                f"**Missing evidence:** "
                f"{cause['missing_evidence']}"
            )

            st.write(
                f"**Farmer verification:** "
                f"{cause['verification']}"
            )


    # =====================================================
    # FIELD VERIFICATION
    # =====================================================

    st.header("🔍 BEFORE YOU DECIDE: FIELD VERIFICATION")

    for item in analysis["reasoning"]["field_verification"]:
        st.checkbox(item, value=False)


    # =====================================================
    # INTERVENTIONS
    # =====================================================

    st.divider()

    st.header("⚖️ Three Intervention Alternatives")

    st.caption(
        "These alternatives are presented for comparison. "
        "The AI does not automatically rank or select them."
    )

    for i, intervention in enumerate(
        analysis["interventions"],
        start=1,
    ):

        with st.container(border=True):

            st.subheader(
                f"OPTION {chr(64 + i)} — {intervention['name']}"
            )

            st.write(
                f"**What to do:** {intervention['what_to_do']}"
            )

            st.write(
                f"**Why it may help:** "
                f"{intervention['why_it_may_help']}"
            )

            st.write(
                f"**Timing:** {intervention['timing']}"
            )

            st.write(
                f"**Required resources:** "
                f"{intervention['resources']}"
            )

            st.write(
                f"**Estimated benefit:** "
                f"{intervention['benefit']}"
            )

            st.write(
                f"**Risks:** {intervention['risks']}"
            )

            st.write(
                f"**Uncertainty:** "
                f"{intervention['uncertainty']}"
            )

            costs = intervention["costs"]

            st.metric(
                "Estimated cost",
                f"PKR {costs['total']:,.0f}",
            )

            st.write(
                f"Material: PKR {costs['material']:,.0f}"
            )

            st.write(
                f"Labor: PKR {costs['labor']:,.0f}"
            )

            st.write(
                f"Energy/equipment: "
                f"PKR {costs['energy']:,.0f}"
            )

            st.write(
                f"Other: PKR {costs['other']:,.0f}"
            )

            st.write(
                f"**Expected crop loss estimate:** "
                f"PKR {intervention['expected_crop_loss']:,.0f}"
            )

            st.write(
                f"**Economic exposure:** "
                f"PKR {intervention['economic_exposure']:,.0f}"
            )

            st.write(
                f"**Budget feasibility:** "
                f"{intervention['feasibility']['budget']}"
            )

            st.write(
                f"**Water feasibility:** "
                f"{intervention['feasibility']['water']}"
            )

            st.write(
                f"**Labor feasibility:** "
                f"{intervention['feasibility']['labor']}"
            )

            st.write(
                f"**Overall feasibility:** "
                f"{intervention['feasibility']['overall']}"
            )

            st.caption(
                "Demo estimate — replace with local price "
                "information before real-world use."
            )


    # =====================================================
    # CRITIC
    # =====================================================

    st.divider()

    st.header("🧠 Critic Review")

    critic = analysis["critic"]

    st.write(
        f"**Key uncertainty:** {critic['key_uncertainty']}"
    )

    st.write(
        f"**Missing information:** "
        f"{critic['missing_information']}"
    )

    st.write(
        f"**Alternative explanation:** "
        f"{critic['alternative_explanation']}"
    )

    st.write(
        f"**What should be verified:** "
        f"{critic['verification']}"
    )

    st.write(
        f"**Confidence:** {critic['confidence']}"
    )


    # =====================================================
    # AI REASONING
    # =====================================================

    with st.expander("🔬 View AI Reasoning"):

        st.write("### Farmer-provided evidence")

        st.json(
            analysis["farm_context"]
        )

        st.write("### External evidence")

        st.json(
            analysis["weather"]
        )

        st.write("### AI interpretation")

        st.json(
            analysis["reasoning"]
        )

        st.write("### Evidence records")

        st.json(
            st.session_state.evidence
        )


    # =====================================================
    # HUMAN DECISION GATE
    # =====================================================

    st.divider()

    st.header("👤 HUMAN DECISION GATE")

    st.error(
        "AI analysis is complete. "
        "No intervention has been selected automatically."
    )

    decision = st.radio(
        "YOUR DECISION",
        [
            "Approve Option A",
            "Approve Option B",
            "Approve Option C",
            "Modify an Option",
            "Reject All Options",
            "Request More Information",
        ],
        index=None,
    )

    modification = ""

    if decision == "Modify an Option":

        selected_option = st.selectbox(
            "Which option would you like to modify?",
            ["Option A", "Option B", "Option C"],
        )

        modification = st.text_area(
            "Describe your modification",
            placeholder=(
                "Example: I want to monitor for 5 days "
                "instead of 3 days."
            ),
        )

    reasoning_text = st.text_area(
        "Why did you make this decision? (optional)",
        placeholder=(
            "Example: I chose this because water is limited "
            "and I want to reduce immediate spending."
        ),
    )

    if decision == "Request More Information":

        st.subheader(
            "ℹ️ Information Needed Before Decision"
        )

        for item in [
            "Percentage of plants affected",
            "Duration of symptoms",
            "Comparison between affected and unaffected plants",
            "Soil moisture around the root zone",
            "Recent fertilizer use",
            "Visible insect or disease symptoms",
        ]:
            st.write(f"• {item}")

    if decision and st.button(
        "✅ CONFIRM HUMAN DECISION",
        type="primary",
        use_container_width=True,
    ):

        if decision == "Request More Information":

            st.warning(
                "No final decision was recorded. "
                "Please collect the requested information "
                "and rerun the analysis."
            )

        else:

            st.session_state.decision_confirmed = True
            st.session_state.decision = decision
            st.session_state.human_modification = modification
            st.session_state.human_reasoning = reasoning_text

            st.success(
                "Human decision recorded successfully."
            )


# =========================================================
# FINAL DECISION
# =========================================================

if st.session_state.decision_confirmed:

    st.divider()

    st.header("📋 FINAL DECISION RECORD")

    st.success(
        "FINAL DECISION MADE BY HUMAN USER"
    )

    st.info(
        "The AI provided decision support only."
    )

    st.write(
        f"**Decision source:** HUMAN USER"
    )

    st.write(
        f"**Decision:** "
        f"{st.session_state.decision}"
    )

    if st.session_state.human_modification:
        st.write(
            f"**Human modification:** "
            f"{st.session_state.human_modification}"
        )

    if st.session_state.human_reasoning:
        st.write(
            f"**Human reasoning:** "
            f"{st.session_state.human_reasoning}"
        )

    report_data = {
        "farm_context": analysis["farm_context"],
        "weather": analysis["weather"],
        "reasoning": analysis["reasoning"],
        "interventions": analysis["interventions"],
        "critic": analysis["critic"],
        "decision": st.session_state.decision,
        "human_modification": st.session_state.human_modification,
        "human_reasoning": st.session_state.human_reasoning,
        "evidence": st.session_state.evidence,
        "province": province,
        "district": district,
        "crop": crop,
        "farm_size": farm_size,
        "budget": budget,
    }

    pdf_bytes = generate_pdf_report(report_data)

    st.download_button(
        label="📄 DOWNLOAD FINAL REPORT AS PDF",
        data=pdf_bytes,
        file_name="agrodecision_pk_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "AGRODECISION PK — Human-in-the-Loop Agricultural Decision Support"
)

st.caption(
    "AI INVESTIGATES. AI COMPARES. HUMAN DECIDES."
)

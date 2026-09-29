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
from agents.cost_agent import run_cost_agent
from agents.feasibility_agent import run_feasibility_agent
from agents.critic_agent import run_critic_agent

from utils.weather import get_district_coordinates
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
    reset_analysis()


def get_ai_mode():
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        return "Live AI" if key else "Demo Mode"
    except Exception:
        return "Demo Mode"


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

AGRODECISION PK provides agricultural decision support.
It does **not** automatically select, purchase, or execute
any farm intervention.
"""
)


# =========================================================
# STATUS BAR
# =========================================================

status1, status2, status3, status4 = st.columns(4)

with status1:
    st.metric("AI Mode", get_ai_mode())

with status2:
    weather_status = "Not checked"

    if st.session_state.analysis_complete:
        weather_data = st.session_state.analysis.get("weather", {})
        weather_status = (
            "Demo Data"
            if weather_data.get("demo")
            else "Live Data"
        )

    st.metric("Weather", weather_status)

with status3:
    if st.session_state.analysis_complete:
        farm_status = st.session_state.analysis.get(
            "farm",
            {}
        )
        location = (
            f"{farm_status.get('district', '')}, "
            f"{farm_status.get('province', '')}"
        )
    else:
        location = "Not selected"

    st.metric("Location", location)

with status4:
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
    [
        "English",
        "اردو",
        "ਪੰਜਾਬੀ",
        "سنڌي",
    ],
)

if language != "English":
    st.info(
        "The selected language is recorded for the farmer-facing "
        "decision workflow. Technical AI reasoning remains available "
        "in English under 'View AI Reasoning'."
    )


# =========================================================
# DEMONSTRATION MODE
# =========================================================

with st.expander("🧪 Load Demonstration Scenario"):

    st.write(
        "Use this deterministic scenario to test the application "
        "without requiring an OpenAI API key."
    )

    st.write(
        "**Punjab → Lahore → Wheat → Possible water stress**"
    )

    if st.button(
        "Load Demo Scenario",
        use_container_width=True,
    ):
        load_demo_values()
        st.success("Demonstration scenario loaded.")

    if st.session_state.demo_loaded:
        st.warning(
            "DEMONSTRATION DATA — NOT VERIFIED FOR "
            "REAL-WORLD AGRICULTURAL DECISIONS"
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

province_names = list(PROVINCES.keys())

if default_province not in province_names:
    default_province = province_names[0]

province = st.selectbox(
    "Province",
    province_names,
    index=province_names.index(default_province),
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
    and DEMO_SCENARIO["crop"] in CROPS
    else CROPS[0]
)

crop = st.selectbox(
    "Crop",
    CROPS,
    index=CROPS.index(default_crop),
)


col1, col2 = st.columns(2)

with col1:

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

with col2:

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
# STRUCTURED INFORMATION
# =========================================================

with st.expander(
    "Answer simple questions (optional)"
):

    col1, col2 = st.columns(2)

    with col1:

        main_symptom = st.text_input(
            "Main symptom",
            value=(
                DEMO_SCENARIO.get(
                    "main_symptom",
                    "",
                )
                if st.session_state.demo_loaded
                else ""
            ),
            placeholder=(
                "e.g. yellowing, wilting, spots"
            ),
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
            [
                "Yes",
                "No",
                "Not sure",
            ],
        )

        recent_fertilizer = st.selectbox(
            "Recent fertilizer application?",
            [
                "Yes",
                "No",
                "Not sure",
            ],
        )

        recent_pesticide = st.selectbox(
            "Recent pesticide/fungicide application?",
            [
                "Yes",
                "No",
                "Not sure",
            ],
        )


# =========================================================
# IMAGE
# =========================================================

st.header("📷 Optional Plant Image")

uploaded_image = st.file_uploader(
    "Upload JPG, JPEG or PNG",
    type=[
        "jpg",
        "jpeg",
        "png",
    ],
)

if uploaded_image:

    st.image(
        uploaded_image,
        caption="Uploaded plant image",
        width=400,
    )

    st.warning(
        "Image received for reference. "
        "The current MVP does not treat the image alone "
        "as a confirmed diagnosis."
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

    coordinates = get_district_coordinates(
        district
    )

    if coordinates is None:
        st.warning(
            "Representative coordinates were not available "
            "for this district. Weather analysis will use "
            "demonstration data if live weather cannot be retrieved."
        )

        coordinates = (
            31.5204,
            74.3587,
        )

    farm = {
        "province": province,
        "district": district,
        "crop": crop,
        "farm_size": float(farm_size),
        "budget": float(budget),
        "problem": problem_text
        or "No detailed problem description supplied.",
        "main_symptom": main_symptom,
        "duration": duration,
        "affected_area": affected_area,
        "severity": severity,
        "soil": soil_type,
        "water_source": water_source,
        "water": water_availability,
        "water_availability": water_availability,
        "recent_irrigation": recent_irrigation,
        "recent_fertilizer": recent_fertilizer,
        "recent_pesticide": recent_pesticide,
        "labor": "Moderate",
        "coords": coordinates,
    }

    evidence_tracker = EvidenceTracker()

    try:

        with st.status(
            "Running agricultural analysis...",
            expanded=True,
        ) as status:

            # -------------------------------------------------
            # 1. FARM CONTEXT
            # -------------------------------------------------

            st.write(
                "1. Farm Context Agent"
            )

            context = run_context_agent(
                farm
            )

            evidence_tracker.add(
                source_type="Farmer-provided evidence",
                source_name="Farmer input",
                title="Farm and problem information",
                url="",
                claim_supported=(
                    "Information reported by the farmer"
                ),
                information_used=str(farm),
            )

            # -------------------------------------------------
            # 2. WEATHER
            # -------------------------------------------------

            st.write(
                "2. Weather & Climate Agent"
            )

            weather = run_weather_agent(
                farm
            )

            if weather.get("source"):
                evidence_tracker.add(
                    source_type=weather.get(
                        "source_type",
                        "External evidence",
                    ),
                    source_name=weather.get(
                        "source",
                        "Weather service",
                    ),
                    title=weather.get(
                        "title",
                        "Weather information",
                    ),
                    url=weather.get(
                        "url",
                        "",
                    ),
                    claim_supported=(
                        "Weather/context information"
                    ),
                    information_used=str(
                        weather
                    ),
                    data_timestamp=weather.get(
                        "timestamp",
                        "",
                    ),
                )

            # -------------------------------------------------
            # 3. CROP REASONING
            # -------------------------------------------------

            st.write(
                "3. Crop & Biological Reasoning Agent"
            )

            crop_reasoning = run_crop_agent(
                farm=farm,
                context=context,
                weather=weather,
            )

            # -------------------------------------------------
            # 4. INTERVENTIONS
            # -------------------------------------------------

            st.write(
                "4. Intervention Generation"
            )

            interventions = (
                run_intervention_agent(
                    farm=farm,
                    context=context,
                    weather=weather,
                    crop_reasoning=crop_reasoning,
                )
            )

            # Safety check: exactly three alternatives
            if (
                not isinstance(
                    interventions,
                    list,
                )
                or len(interventions) != 3
            ):
                raise ValueError(
                    "The intervention agent did not return "
                    "exactly three alternatives."
                )

            # -------------------------------------------------
            # 5. COST ANALYSIS
            # -------------------------------------------------

            st.write(
                "5. Cost Analysis"
            )

            interventions = run_cost_agent(
                farm=farm,
                interventions=interventions,
            )

            # -------------------------------------------------
            # 6. FEASIBILITY
            # -------------------------------------------------

            st.write(
                "6. Feasibility Analysis"
            )

            feasibility = (
                run_feasibility_agent(
                    farm=farm,
                    options=interventions,
                )
            )

            for i, intervention in enumerate(
                interventions
            ):

                if i < len(feasibility):
                    intervention[
                        "feasibility"
                    ] = feasibility[i]

            # -------------------------------------------------
            # 7. CRITIC
            # -------------------------------------------------

            st.write(
                "7. Critic Review"
            )

            critic = run_critic_agent(
                farm=farm,
                context=context,
                weather=weather,
                crop_reasoning=crop_reasoning,
                options=interventions,
                feasibility=feasibility,
            )

            status.update(
                label="Analysis complete",
                state="complete",
            )

        # -----------------------------------------------------
        # STORE ANALYSIS
        # -----------------------------------------------------

        st.session_state.analysis = {
            "farm": farm,
            "context": context,
            "weather": weather,
            "reasoning": crop_reasoning,
            "interventions": interventions,
            "feasibility": feasibility,
            "critic": critic,
            "language": language,
            "uploaded_image": bool(
                uploaded_image
            ),
        }

        st.session_state.evidence = (
            evidence_tracker.items
        )

        st.session_state.analysis_complete = True

        st.rerun()

    except Exception:
        st.error(
            "The analysis could not be completed. "
            "The application has kept the farmer decision "
            "gate closed. Please check the inputs and try again."
        )

        st.info(
            "If live AI or weather services are unavailable, "
            "the application is designed to continue using "
            "demonstration/fallback reasoning where possible."
        )


# =========================================================
# RESULTS
# =========================================================

if st.session_state.analysis_complete:

    analysis = st.session_state.analysis

    farm = analysis["farm"]
    weather = analysis["weather"]
    reasoning = analysis["reasoning"]
    interventions = analysis["interventions"]
    critic = analysis["critic"]

    st.divider()

    # =====================================================
    # WEATHER
    # =====================================================

    st.header(
        "🌦️ Weather & Agricultural Context"
    )

    if weather.get("demo"):

        st.warning(
            "DEMO WEATHER DATA — NOT VERIFIED FOR "
            "REAL-WORLD AGRICULTURAL DECISIONS"
        )

    else:

        st.success(
            "LIVE WEATHER DATA — PUBLIC WEATHER SOURCE"
        )

    st.write(
        weather.get(
            "summary",
            "Weather information unavailable.",
        )
    )

    weather_col1, weather_col2, weather_col3 = (
        st.columns(3)
    )

    with weather_col1:
        temperature = weather.get(
            "temperature_c"
        )

        if temperature is not None:
            st.metric(
                "Temperature",
                f"{temperature} °C",
            )

    with weather_col2:
        rainfall = weather.get(
            "recent_rainfall_mm"
        )

        if rainfall is not None:
            st.metric(
                "Recent rainfall",
                f"{rainfall:.1f} mm",
            )

    with weather_col3:
        humidity = weather.get(
            "humidity_percent"
        )

        if humidity is not None:
            st.metric(
                "Humidity",
                f"{humidity}%",
            )


    # =====================================================
    # FARM CONTEXT
    # =====================================================

    st.divider()

    st.header(
        "🌱 Farm Context"
    )

    st.write(
        analysis["context"].get(
            "summary",
            "Farm context summary unavailable.",
        )
    )

    missing = analysis["context"].get(
        "missing_information",
        [],
    )

    if missing:

        st.warning(
            "Some information remains uncertain."
        )

        for item in missing:
            st.write(
                f"• {item}"
            )


    # =====================================================
    # POSSIBLE CAUSES
    # =====================================================

    st.header(
        "🧬 Possible Causes"
    )

    st.caption(
        "These are hypotheses, not confirmed diagnoses."
    )

    possible_causes = reasoning.get(
        "possible_causes",
        [],
    )

    for cause in possible_causes:

        with st.container(border=True):

            st.subheader(
                cause.get(
                    "name",
                    "Possible explanation",
                )
            )

            explanation = cause.get(
                "explanation",
                cause.get(
                    "why",
                    "No explanation provided.",
                ),
            )

            st.write(
                f"**Explanation:** {explanation}"
            )

            st.write(
                f"**Confidence:** "
                f"{cause.get('confidence', 'Unknown')}"
            )

            supporting = cause.get(
                "supporting_evidence",
                cause.get(
                    "why",
                    "Not specified.",
                ),
            )

            missing_evidence = cause.get(
                "missing_evidence",
                "Field evidence is incomplete.",
            )

            verification = cause.get(
                "verification",
                "Inspect representative plants and field conditions.",
            )

            st.write(
                f"**Supporting evidence:** {supporting}"
            )

            st.write(
                f"**Missing evidence:** {missing_evidence}"
            )

            st.write(
                f"**What the farmer can verify:** "
                f"{verification}"
            )


    # =====================================================
    # FIELD VERIFICATION
    # =====================================================

    st.header(
        "🔍 BEFORE YOU DECIDE: FIELD VERIFICATION"
    )

    field_checks = reasoning.get(
        "field_verification",
        [],
    )

    if not field_checks:

        field_checks = [
            "Inspect several affected and unaffected plants.",
            "Check soil/root-zone moisture.",
            "Review recent irrigation and rainfall.",
            "Check whether symptoms are localized or widespread.",
        ]

    for index, item in enumerate(
        field_checks
    ):

        st.checkbox(
            item,
            key=f"field_check_{index}",
        )


    # =====================================================
    # INTERVENTIONS
    # =====================================================

    st.divider()

    st.header(
        "⚖️ Three Intervention Alternatives"
    )

    st.caption(
        "The alternatives are presented for comparison. "
        "No option is automatically selected or ranked."
    )

    for i, intervention in enumerate(
        interventions,
        start=1,
    ):

        option_letter = chr(
            64 + i
        )

        with st.container(border=True):

            st.subheader(
                f"OPTION {option_letter} — "
                f"{intervention.get('name', 'Alternative')}"
            )

            st.write(
                f"**What to do:** "
                f"{intervention.get('what_to_do', '')}"
            )

            st.write(
                f"**Why it may help:** "
                f"{intervention.get('why_it_may_help', '')}"
            )

            st.write(
                f"**Timing:** "
                f"{intervention.get('timing', '')}"
            )

            st.write(
                f"**Resources:** "
                f"{intervention.get('resources', '')}"
            )

            st.write(
                f"**Estimated benefit:** "
                f"{intervention.get('potential_benefit', '')}"
            )

            st.write(
                f"**Risks:** "
                f"{intervention.get('risks', '')}"
            )

            st.write(
                f"**Uncertainty:** "
                f"{intervention.get('uncertainty', '')}"
            )

            costs = intervention.get(
                "costs",
                {},
            )

            st.metric(
                "Estimated cost",
                f"PKR {costs.get('total', 0):,.0f}",
            )

            cost_col1, cost_col2 = (
                st.columns(2)
            )

            with cost_col1:

                st.write(
                    f"Material: "
                    f"PKR {costs.get('material', 0):,.0f}"
                )

                st.write(
                    f"Labor: "
                    f"PKR {costs.get('labor', 0):,.0f}"
                )

            with cost_col2:

                st.write(
                    f"Energy/equipment: "
                    f"PKR {costs.get('energy', 0):,.0f}"
                )

                st.write(
                    f"Other: "
                    f"PKR {costs.get('other', 0):,.0f}"
                )

            st.write(
                "**Cost note:** Demo estimate — "
                "replace with local price information "
                "before real-world use."
            )

            feasibility_info = intervention.get(
                "feasibility",
                {},
            )

            st.write(
                f"**Budget feasibility:** "
                f"{feasibility_info.get('budget', 'Unknown')}"
            )

            st.write(
                f"**Water feasibility:** "
                f"{feasibility_info.get('water', 'Unknown')}"
            )

            st.write(
                f"**Labor feasibility:** "
                f"{feasibility_info.get('labor', 'Unknown')}"
            )

            st.write(
                f"**Overall feasibility:** "
                f"{feasibility_info.get('overall', 'Unknown')}"
            )


    # =====================================================
    # CRITIC
    # =====================================================

    st.divider()

    st.header(
        "🧠 Critic Review"
    )

    st.write(
        f"**Key uncertainty:** "
        f"{critic.get('key_uncertainty', '')}"
    )

    st.write(
        f"**Missing information:** "
        f"{critic.get('missing_information', [])}"
    )

    st.write(
        f"**Alternative explanation:** "
        f"{critic.get('alternative_explanation', '')}"
    )

    verify_items = critic.get(
        "verify",
        critic.get(
            "verification",
            [],
        ),
    )

    st.write(
        "**What should be verified:**"
    )

    for item in verify_items:
        st.write(
            f"• {item}"
        )

    st.write(
        f"**Confidence:** "
        f"{critic.get('confidence', 'Unknown')}"
    )


    # =====================================================
    # AI REASONING
    # =====================================================

    with st.expander(
        "🔬 View AI Reasoning"
    ):

        st.write(
            "### Farmer-provided evidence"
        )

        st.json(
            farm
        )

        st.write(
            "### External evidence"
        )

        st.json(
            weather
        )

        st.write(
            "### AI interpretation"
        )

        st.json(
            reasoning
        )

        st.write(
            "### Evidence records"
        )

        st.json(
            st.session_state.evidence
        )


    # =====================================================
    # SOURCES & EVIDENCE
    # =====================================================

    st.divider()

    st.header(
        "📚 Sources & Evidence"
    )

    if st.session_state.evidence:

        for item in st.session_state.evidence:

            with st.expander(
                item.get(
                    "title",
                    "Evidence item",
                )
            ):

                st.write(
                    f"**Information:** "
                    f"{item.get('information_used', '')}"
                )

                st.write(
                    f"**Source:** "
                    f"{item.get('source_name', '')}"
                )

                st.write(
                    f"**Source type:** "
                    f"{item.get('source_type', '')}"
                )

                st.write(
                    f"**Data timestamp:** "
                    f"{item.get('data_timestamp', '')}"
                )

                url = item.get(
                    "url",
                    "",
                )

                if url:
                    st.markdown(
                        f"[Open source]({url})"
                    )
                else:
                    st.caption(
                        "No external URL — "
                        "farmer-provided information "
                        "or demonstration assumption."
                    )

    else:

        st.info(
            "No external evidence records are available."
        )


    # =====================================================
    # HUMAN DECISION GATE
    # =====================================================

    st.divider()

    st.header(
        "👤 HUMAN DECISION GATE"
    )

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
    selected_option = ""

    if decision == "Modify an Option":

        selected_option = st.selectbox(
            "Which option would you like to modify?",
            [
                "Option A",
                "Option B",
                "Option C",
            ],
        )

        modification = st.text_area(
            "Describe your modification",
            placeholder=(
                "Example: I want to monitor for "
                "5 days instead of 3 days."
            ),
        )

    reasoning_text = st.text_area(
        "Why did you make this decision? (optional)",
        placeholder=(
            "Explain the practical reason for your decision."
        ),
    )


    if decision == "Request More Information":

        st.subheader(
            "ℹ️ Information Needed Before Decision"
        )

        requested_information = [
            "Percentage of plants affected",
            "Duration of symptoms",
            "Comparison between affected and unaffected plants",
            "Soil moisture around the root zone",
            "Recent irrigation history",
            "Recent fertilizer use",
            "Visible insect or disease symptoms",
        ]

        for item in requested_information:

            st.write(
                f"• {item}"
            )


    if decision:

        if st.button(
            "✅ CONFIRM HUMAN DECISION",
            type="primary",
            use_container_width=True,
        ):

            if decision == "Request More Information":

                st.warning(
                    "No final decision was recorded. "
                    "Collect the requested information "
                    "and rerun the analysis."
                )

            else:

                final_modification = modification

                if selected_option:
                    final_modification = (
                        f"{selected_option}: "
                        f"{modification}"
                    )

                st.session_state.decision_confirmed = True
                st.session_state.decision = decision
                st.session_state.human_modification = (
                    final_modification
                )
                st.session_state.human_reasoning = (
                    reasoning_text
                )

                st.success(
                    "Human decision recorded successfully."
                )

                st.rerun()


# =========================================================
# FINAL DECISION RECORD
# =========================================================

if st.session_state.decision_confirmed:

    analysis = st.session_state.analysis

    st.divider()

    st.header(
        "📋 FINAL DECISION RECORD"
    )

    st.success(
        "FINAL DECISION MADE BY HUMAN USER"
    )

    st.info(
        "The AI provided decision support only."
    )

    st.write(
        "**Decision source:** HUMAN USER"
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
        "farm_context": analysis["context"],
        "farm": analysis["farm"],
        "weather": analysis["weather"],
        "reasoning": analysis["reasoning"],
        "interventions": analysis["interventions"],
        "feasibility": analysis["feasibility"],
        "critic": analysis["critic"],
        "decision": st.session_state.decision,
        "human_modification": (
            st.session_state.human_modification
        ),
        "human_reasoning": (
            st.session_state.human_reasoning
        ),
        "evidence": st.session_state.evidence,
        "province": analysis["farm"]["province"],
        "district": analysis["farm"]["district"],
        "crop": analysis["farm"]["crop"],
        "farm_size": analysis["farm"]["farm_size"],
        "budget": analysis["farm"]["budget"],
        "language": analysis["language"],
        "uploaded_image": analysis["uploaded_image"],
    }

    try:

        pdf_bytes = generate_pdf_report(
            report_data
        )

        if pdf_bytes:

            st.download_button(
                label=(
                    "📄 DOWNLOAD FINAL REPORT AS PDF"
                ),
                data=pdf_bytes,
                file_name=(
                    "agrodecision_pk_report.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
            )

    except Exception:

        st.warning(
            "The PDF report could not be generated. "
            "The final human decision is still recorded "
            "above."
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

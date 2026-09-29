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

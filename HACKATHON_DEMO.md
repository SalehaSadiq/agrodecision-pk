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

from io import BytesIO
from html import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


def _safe_text(value, default="Not provided"):
    """
    Convert values into safe printable text for ReportLab.
    """
    if value is None:
        return default

    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value)

    if isinstance(value, dict):
        return "; ".join(
            f"{key}: {value}"
            for key, value in value.items()
        )

    text = str(value).strip()

    return text if text else default


def _paragraph_text(value, default="Not provided"):
    """
    Escape dynamic text before inserting it into ReportLab Paragraphs.
    """
    return escape(
        _safe_text(value, default)
    )


def generate_pdf_report(data):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    story = []

    # =====================================================
    # TITLE
    # =====================================================

    story.append(
        Paragraph(
            "AGRODECISION PK",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            "Human-in-the-Loop Agricultural Decision Support Report",
            styles["Heading2"],
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "<b>FINAL DECISION MADE BY HUMAN USER</b>",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "The AI provided decision support only. "
            "No intervention was automatically selected or executed.",
            styles["Normal"],
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # =====================================================
    # FARM INFORMATION
    # =====================================================

    farm = data.get(
        "farm",
        {},
    )

    farm_table = [
        ["Field", "Value"],
        [
            "Province",
            _paragraph_text(
                farm.get("province")
            ),
        ],
        [
            "District",
            _paragraph_text(
                farm.get("district")
            ),
        ],
        [
            "Crop",
            _paragraph_text(
                farm.get("crop")
            ),
        ],
        [
            "Farm size",
            f"{farm.get('farm_size', 0):,.1f} acres",
        ],
        [
            "Available budget",
            f"PKR {farm.get('budget', 0):,.0f}",
        ],
        [
            "Problem",
            _paragraph_text(
                farm.get("problem")
            ),
        ],
        [
            "Main symptom",
            _paragraph_text(
                farm.get("main_symptom")
            ),
        ],
        [
            "Duration",
            _paragraph_text(
                farm.get("duration")
            ),
        ],
        [
            "Affected area",
            _paragraph_text(
                farm.get("affected_area")
            ),
        ],
        [
            "Severity",
            _paragraph_text(
                farm.get("severity")
            ),
        ],
        [
            "Soil",
            _paragraph_text(
                farm.get("soil")
            ),
        ],
        [
            "Water source",
            _paragraph_text(
                farm.get("water_source")
            ),
        ],
        [
            "Water availability",
            _paragraph_text(
                farm.get("water_availability")
            ),
        ],
    ]

    table = Table(
        farm_table,
        colWidths=[140, 350],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )

    # =====================================================
    # WEATHER
    # =====================================================

    story.append(
        Paragraph(
            "Weather & Agricultural Context",
            styles["Heading2"],
        )
    )

    weather = data.get(
        "weather",
        {},
    )

    weather_summary = weather.get(
        "summary",
        "Weather information unavailable.",
    )

    story.append(
        Paragraph(
            _paragraph_text(weather_summary),
            styles["Normal"],
        )
    )

    if weather.get("demo"):

        story.append(
            Paragraph(
                "<b>DEMO WEATHER DATA — "
                "NOT VERIFIED FOR REAL-WORLD DECISIONS</b>",
                styles["Normal"],
            )
        )

    else:

        story.append(
            Paragraph(
                "<b>LIVE WEATHER DATA — PUBLIC WEATHER SOURCE</b>",
                styles["Normal"],
            )
        )

    story.append(
        Spacer(1, 10)
    )

    # =====================================================
    # FARM CONTEXT
    # =====================================================

    story.append(
        Paragraph(
            "Farm Context",
            styles["Heading2"],
        )
    )

    context = data.get(
        "farm_context",
        data.get(
            "context",
            {},
        ),
    )

    story.append(
        Paragraph(
            _paragraph_text(
                context.get(
                    "summary",
                    "Farm context summary unavailable.",
                )
            ),
            styles["Normal"],
        )
    )

    story.append(
        Spacer(1, 10)
    )

    # =====================================================
    # AI ASSESSMENT
    # =====================================================

    story.append(
        Paragraph(
            "AI Assessment",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "Possible causes are hypotheses, not confirmed diagnoses.",
            styles["Normal"],
        )
    )

    reasoning = data.get(
        "reasoning",
        {},
    )

    possible_causes = reasoning.get(
        "possible_causes",
        [],
    )

    if not possible_causes:

        story.append(
            Paragraph(
                "No possible causes were generated.",
                styles["Normal"],
            )
        )

    for cause in possible_causes:

        story.append(
            Paragraph(
                f"<b>{_paragraph_text(cause.get('name'))}</b>",
                styles["Heading3"],
            )
        )

        explanation = cause.get(
            "explanation",
            cause.get(
                "why",
                "No explanation provided.",
            ),
        )

        story.append(
            Paragraph(
                _paragraph_text(explanation),
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                "Confidence: "
                + _paragraph_text(
                    cause.get(
                        "confidence",
                        "Unknown",
                    )
                ),
                styles["Normal"],
            )
        )

        supporting = cause.get(
            "supporting_evidence",
            cause.get(
                "why",
                "Not specified.",
            ),
        )

        story.append(
            Paragraph(
                "Supporting evidence: "
                + _paragraph_text(supporting),
                styles["Normal"],
            )
        )

        missing = cause.get(
            "missing_evidence",
            "Field evidence is incomplete.",
        )

        story.append(
            Paragraph(
                "Missing evidence: "
                + _paragraph_text(missing),
                styles["Normal"],
            )
        )

        verification = cause.get(
            "verification",
            "Inspect representative plants and field conditions.",
        )

        story.append(
            Paragraph(
                "What the farmer can verify: "
                + _paragraph_text(verification),
                styles["Normal"],
            )
        )

        story.append(
            Spacer(1, 8)
        )

    # =====================================================
    # INTERVENTION ALTERNATIVES
    # =====================================================

    story.append(
        Paragraph(
            "Three Intervention Alternatives",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "The alternatives are presented for comparison. "
            "No option was automatically selected or ranked.",
            styles["Normal"],
        )
    )

    interventions = data.get(
        "interventions",
        [],
    )

    for index, intervention in enumerate(
        interventions,
        start=1,
    ):

        option_letter = chr(
            64 + index
        )

        story.append(
            Paragraph(
                f"Option {option_letter} — "
                f"{_paragraph_text(intervention.get('name', 'Alternative'))}",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                "<b>What to do:</b> "
                + _paragraph_text(
                    intervention.get(
                        "what_to_do"
                    )
                ),
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                "<b>Why it may help:</b> "
                + _paragraph_text(
                    intervention.get(
                        "why_it_may_help"
                    )
                ),
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                "<b>Timing:</b> "
                + _paragraph_text(
                    intervention.get(
                        "timing"
                    )
                ),
                styles["Normal"],
            )
        )

        costs = intervention.get(
            "costs",
            {},
        )

        total_cost = costs.get(
            "total",
            0,
        )

        story.append(
            Paragraph(
                f"<b>Estimated cost:</b> "
                f"PKR {float(total_cost):,.0f}",
                styles["Normal"],
            )
        )

        feasibility = intervention.get(
            "feasibility",
            {},
        )

        story.append(
            Paragraph(
                "<b>Budget feasibility:</b> "
                + _paragraph_text(
                    feasibility.get(
                        "budget",
                        "Unknown",
                    )
                ),
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                "<b>Water feasibility:</b> "
                + _paragraph_text(
                    feasibility.get(
                        "water",
                        "Unknown",
                    )
                ),
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                "<b>Labor feasibility:</b> "
                + _paragraph_text(
                    feasibility.get(
                        "labor",
                        "Unknown",
                    )
                ),
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                "<b>Overall feasibility:</b> "
                + _paragraph_text(
                    feasibility.get(
                        "overall",
                        "Unknown",
                    )
                ),
                styles["Normal"],
            )
        )

        story.append(
            Spacer(1, 8)
        )

    # =====================================================
    # CRITIC REVIEW
    # =====================================================

    story.append(
        Paragraph(
            "Critic Review",
            styles["Heading2"],
        )
    )

    critic = data.get(
        "critic",
        {},
    )

    story.append(
        Paragraph(
            "<b>Key uncertainty:</b> "
            + _paragraph_text(
                critic.get(
                    "key_uncertainty",
                    "Not specified.",
                )
            ),
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "<b>Missing information:</b> "
            + _paragraph_text(
                critic.get(
                    "missing_information",
                    [],
                )
            ),
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "<b>Alternative explanation:</b> "
            + _paragraph_text(
                critic.get(
                    "alternative_explanation",
                    "Not specified.",
                )
            ),
            styles["Normal"],
        )
    )

    verify_items = critic.get(
        "verify",
        critic.get(
            "verification",
            [],
        ),
    )

    story.append(
        Paragraph(
            "<b>What should be verified:</b>",
            styles["Normal"],
        )
    )

    if isinstance(
        verify_items,
        list,
    ):

        for item in verify_items:

            story.append(
                Paragraph(
                    "• "
                    + _paragraph_text(item),
                    styles["Normal"],
                )
            )

    else:

        story.append(
            Paragraph(
                _paragraph_text(
                    verify_items
                ),
                styles["Normal"],
            )
        )

    story.append(
        Paragraph(
            "<b>Confidence:</b> "
            + _paragraph_text(
                critic.get(
                    "confidence",
                    "Unknown",
                )
            ),
            styles["Normal"],
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # =====================================================
    # HUMAN DECISION
    # =====================================================

    story.append(
        Paragraph(
            "Human Decision",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "<b>Decision source: HUMAN USER</b>",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "<b>Decision:</b> "
            + _paragraph_text(
                data.get(
                    "decision",
                    "Not recorded",
                )
            ),
            styles["Normal"],
        )
    )

    if data.get(
        "human_modification"
    ):

        story.append(
            Paragraph(
                "<b>Human modification:</b> "
                + _paragraph_text(
                    data["human_modification"]
                ),
                styles["Normal"],
            )
        )

    if data.get(
        "human_reasoning"
    ):

        story.append(
            Paragraph(
                "<b>Human reasoning:</b> "
                + _paragraph_text(
                    data["human_reasoning"]
                ),
                styles["Normal"],
            )
        )

    story.append(
        Spacer(1, 15)
    )

    # =====================================================
    # SOURCES & EVIDENCE
    # =====================================================

    story.append(
        Paragraph(
            "Sources & Evidence",
            styles["Heading2"],
        )
    )

    evidence_items = data.get(
        "evidence",
        [],
    )

    if not evidence_items:

        story.append(
            Paragraph(
                "No external evidence records are available.",
                styles["Normal"],
            )
        )

    for evidence in evidence_items:

        source_type = _paragraph_text(
            evidence.get(
                "source_type",
                "",
            )
        )

        source_name = _paragraph_text(
            evidence.get(
                "source_name",
                "",
            )
        )

        title = _paragraph_text(
            evidence.get(
                "title",
                "Evidence item",
            )
        )

        story.append(
            Paragraph(
                f"<b>{source_type} — "
                f"{source_name}</b>",
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                title,
                styles["Normal"],
            )
        )

        information_used = evidence.get(
            "information_used",
            "",
        )

        if information_used:

            story.append(
                Paragraph(
                    "<b>Information used:</b> "
                    + _paragraph_text(
                        information_used
                    ),
                    styles["Normal"],
                )
            )

        timestamp = evidence.get(
            "data_timestamp",
            "",
        )

        if timestamp:

            story.append(
                Paragraph(
                    "<b>Data timestamp:</b> "
                    + _paragraph_text(
                        timestamp
                    ),
                    styles["Normal"],
                )
            )

        url = evidence.get(
            "url",
            "",
        )

        if url:

            story.append(
                Paragraph(
                    "<b>Source URL:</b> "
                    + _paragraph_text(url),
                    styles["Normal"],
                )
            )

        story.append(
            Spacer(1, 6)
        )

    # =====================================================
    # DISCLAIMER
    # =====================================================

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Disclaimer",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "This report provides decision support only. "
            "Possible causes are hypotheses rather than confirmed "
            "diagnoses. Costs and other estimates are uncertain and "
            "should be checked against local conditions and current "
            "local prices before real-world use. The system does not "
            "automatically purchase, apply, or execute any intervention.",
            styles["Normal"],
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()

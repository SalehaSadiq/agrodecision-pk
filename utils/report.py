from io import BytesIO
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

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>FINAL DECISION MADE BY HUMAN USER</b>",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "The AI only provided decision support.",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 15))

    farm = data["farm_context"]

    farm_table = [
        ["Field", "Value"],
        ["Province", farm["province"]],
        ["District", farm["district"]],
        ["Crop", farm["crop"]],
        ["Farm size", f"{farm['farm_size_acres']} acres"],
        ["Budget", f"PKR {farm['budget_pkr']:,.0f}"],
        ["Problem", farm["problem"] or "Not provided"],
    ]

    table = Table(
        farm_table,
        colWidths=[140, 350],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "AI Assessment",
            styles["Heading2"],
        )
    )

    reasoning = data["reasoning"]

    for cause in reasoning["possible_causes"]:

        story.append(
            Paragraph(
                f"<b>{cause['name']}</b>",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                cause["explanation"],
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Confidence: {cause['confidence']}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "Intervention Alternatives",
            styles["Heading2"],
        )
    )

    for index, intervention in enumerate(
        data["interventions"],
        start=1,
    ):

        story.append(
            Paragraph(
                f"Option {chr(64 + index)} — {intervention['name']}",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                intervention["what_to_do"],
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Estimated cost: "
                f"PKR {intervention['costs']['total']:,.0f}",
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Feasibility: "
                f"{intervention['feasibility']['overall']}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Critic Review",
            styles["Heading2"],
        )
    )

    critic = data["critic"]

    story.append(
        Paragraph(
            f"Key uncertainty: {critic['key_uncertainty']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Missing information: "
            f"{critic['missing_information']}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Alternative explanation: "
            f"{critic['alternative_explanation']}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Human Decision",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            f"Decision source: HUMAN USER",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Decision: {data['decision']}",
            styles["Normal"],
        )
    )

    if data["human_modification"]:

        story.append(
            Paragraph(
                f"Human modification: "
                f"{data['human_modification']}",
                styles["Normal"],
            )
        )

    if data["human_reasoning"]:

        story.append(
            Paragraph(
                f"Human reasoning: "
                f"{data['human_reasoning']}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Sources & Evidence",
            styles["Heading2"],
        )
    )

    for evidence in data["evidence"]:

        source_text = (
            f"{evidence['source_type']} — "
            f"{evidence['source_name']} — "
            f"{evidence['title']}"
        )

        story.append(
            Paragraph(
                source_text,
                styles["Normal"],
            )
        )

        if evidence.get("url"):
            story.append(
                Paragraph(
                    f"URL: {evidence['url']}",
                    styles["Normal"],
                )
            )

        story.append(Spacer(1, 5))

    story.append(Spacer(1, 15))

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
            "diagnoses. Costs, economic exposure, and other estimates "
            "are uncertain and should be checked against local conditions "
            "and prices before real-world use.",
            styles["Normal"],
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()

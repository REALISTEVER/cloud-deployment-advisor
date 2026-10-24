import gradio as gr
from inference_engine import analyze_facts

APP_TITLE = "Cloud Deployment Readiness Advisor"

def to_tri(value):
    if value == "True":
        return True
    if value == "False":
        return False
    return None

def format_value(value):
    if value is True:
        return "True"
    if value is False:
        return "False"
    if value is None:
        return "Unknown"
    return str(value)

def analyze(
    deployment_environment,
    tests_passed,
    test_coverage,
    secret_scan_passed,
    secrets_detected,
    environment_variables_configured,
    health_check_configured,
    database_migrations_ready,
    rollback_plan_available,
    monitoring_configured,
):
    facts = {
        "deployment_environment": deployment_environment,
        "tests_passed": to_tri(tests_passed),
        "test_coverage": None if test_coverage in (None, "") else test_coverage,
        "secret_scan_passed": to_tri(secret_scan_passed),
        "secrets_detected": to_tri(secrets_detected),
        "environment_variables_configured": to_tri(environment_variables_configured),
        "health_check_configured": to_tri(health_check_configured),
        "database_migrations_ready": to_tri(database_migrations_ready),
        "rollback_plan_available": to_tri(rollback_plan_available),
        "monitoring_configured": to_tri(monitoring_configured),
    }

    result = analyze_facts(facts)

    lines = [
        f"# {result['conclusion_label']}",
        "",
        f"**Supported conclusion:** `{result['supported_conclusion'] or 'None'}`",
        "",
    ]

    if result["validation_errors"]:
        lines.append("## Validation errors")
        for item in result["validation_errors"]:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## Rules fired")
    if result["rules_fired"]:
        for rule in result["rules_fired"]:
            lines.append(f"- **{rule['id']} — {rule['name']}**: {rule['explanation']}")
    else:
        lines.append("- No rule fired.")
    lines.append("")

    lines.append("## Intermediate facts")
    for name, value in result["intermediate_facts"].items():
        lines.append(f"- `{name}` = **{format_value(value)}**")
    lines.append("")

    lines.append("## Recommended next steps")
    for item in result["recommendations"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Missing information")
    if result["missing_information"]:
        for item in result["missing_information"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Conflicts / ambiguity")
    if result["conflicts"]:
        for item in result["conflicts"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append(f"> **Human review required:** {result['human_review']}")

    return "\n".join(lines), result

tri_choices = ["True", "False", "Unknown"]

with gr.Blocks(title=APP_TITLE) as demo:
    gr.Markdown(
        """
        # ☁️ Cloud Deployment Readiness Advisor

        An explainable, rule-based decision-support tool for deciding whether a software release
        has enough evidence for **staging**, **production**, **cautious deployment**, or a **block**.

        The system follows:

        **Input → Validation → Structured facts → Rules → Inference → Explanation → Human review**

        `Unknown` is intentionally different from `False`; missing evidence is never silently treated as failure.
        """
    )

    with gr.Row():
        with gr.Column():
            deployment_environment = gr.Dropdown(
                ["Staging", "Production"],
                value="Production",
                label="Target environment",
            )
            tests_passed = gr.Radio(tri_choices, value="Unknown", label="Automated tests passed?")
            test_coverage = gr.Number(value=None, label="Test coverage % (0–100, blank = Unknown)")
            secret_scan_passed = gr.Radio(tri_choices, value="Unknown", label="Secret scan passed?")
            secrets_detected = gr.Radio(tri_choices, value="Unknown", label="Secrets detected?")
        with gr.Column():
            environment_variables_configured = gr.Radio(
                tri_choices, value="Unknown", label="Required environment variables configured?"
            )
            health_check_configured = gr.Radio(
                tri_choices, value="Unknown", label="Health check configured?"
            )
            database_migrations_ready = gr.Radio(
                tri_choices, value="Unknown", label="Database migrations ready?"
            )
            rollback_plan_available = gr.Radio(
                tri_choices, value="Unknown", label="Rollback plan available?"
            )
            monitoring_configured = gr.Radio(
                tri_choices, value="Unknown", label="Monitoring/alerts configured?"
            )

    analyze_btn = gr.Button("Analyze deployment readiness", variant="primary")

    with gr.Row():
        explanation = gr.Markdown()
        structured = gr.JSON(label="Structured inference result")

    gr.Examples(
        examples=[
            ["Production", "True", 92, "True", "False", "True", "True", "True", "True", "True"],
            ["Staging", "True", 84, "True", "False", "True", "True", "True", "Unknown", "Unknown"],
            ["Production", "False", 90, "True", "False", "True", "True", "True", "True", "True"],
            ["Production", "True", 88, "True", "False", "True", "True", "True", "Unknown", "True"],
            ["Production", "True", 90, "True", "True", "True", "True", "True", "True", "True"],
        ],
        inputs=[
            deployment_environment,
            tests_passed,
            test_coverage,
            secret_scan_passed,
            secrets_detected,
            environment_variables_configured,
            health_check_configured,
            database_migrations_ready,
            rollback_plan_available,
            monitoring_configured,
        ],
        label="Example scenarios",
    )

    analyze_btn.click(
        fn=analyze,
        inputs=[
            deployment_environment,
            tests_passed,
            test_coverage,
            secret_scan_passed,
            secrets_detected,
            environment_variables_configured,
            health_check_configured,
            database_migrations_ready,
            rollback_plan_available,
            monitoring_configured,
        ],
        outputs=[explanation, structured],
        api_name="analyze",
    )

if __name__ == "__main__":
    demo.launch()

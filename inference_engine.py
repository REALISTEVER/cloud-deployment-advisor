from copy import deepcopy
from knowledge_base import RULES, CONCLUSIONS, INTERMEDIATE_FACTS

UNKNOWN = None

def tri(value):
    """Convert UI/API values to True/False/Unknown without collapsing Unknown into False."""
    if value is True or value is False or value is None:
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "pass", "passed"}:
            return True
        if normalized in {"false", "no", "fail", "failed"}:
            return False
        if normalized in {"unknown", "", "none", "null"}:
            return None
    return value

def validate_inputs(facts):
    errors = []
    conflicts = []

    env = facts.get("deployment_environment")
    if env not in {"Staging", "Production"}:
        errors.append("deployment_environment must be either 'Staging' or 'Production'.")

    coverage = facts.get("test_coverage")
    if coverage is not None:
        try:
            coverage = float(coverage)
            facts["test_coverage"] = coverage
        except (TypeError, ValueError):
            errors.append("test_coverage must be a number from 0 to 100 or Unknown.")
        else:
            if coverage < 0 or coverage > 100:
                errors.append("test_coverage must be between 0 and 100.")

    # Problem-specific conflict: these two statements cannot both reasonably be true.
    if facts.get("secret_scan_passed") is True and facts.get("secrets_detected") is True:
        conflicts.append(
            "Secret-scan conflict: the scan is marked Passed, but secrets_detected is also True."
        )

    return errors, conflicts

def _eval_condition(facts, condition):
    fact_name, op, expected = condition
    actual = facts.get(fact_name, UNKNOWN)

    if actual is UNKNOWN:
        return UNKNOWN

    if op == "is":
        return actual is expected
    if op == "==":
        return actual == expected
    if op == ">=":
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False

    raise ValueError(f"Unsupported operator: {op}")

def _missing_for_rule(facts, rule):
    missing = []
    for fact_name, _, _ in rule["conditions"]:
        if facts.get(fact_name, UNKNOWN) is UNKNOWN:
            missing.append(fact_name)
    return missing

def analyze_facts(input_facts):
    facts = deepcopy(input_facts)

    # Normalize tri-state inputs.
    tri_state_names = {
        "tests_passed",
        "secret_scan_passed",
        "secrets_detected",
        "environment_variables_configured",
        "health_check_configured",
        "database_migrations_ready",
        "rollback_plan_available",
        "monitoring_configured",
    }
    for name in tri_state_names:
        facts[name] = tri(facts.get(name))

    # Coverage may also be Unknown.
    if isinstance(facts.get("test_coverage"), str) and facts["test_coverage"].strip().lower() == "unknown":
        facts["test_coverage"] = None

    for name in INTERMEDIATE_FACTS:
        facts.setdefault(name, UNKNOWN)

    errors, conflicts = validate_inputs(facts)

    if errors:
        return {
            "status": "invalid",
            "supported_conclusion": None,
            "conclusion_label": "Invalid Input",
            "rules_fired": [],
            "intermediate_facts": {name: facts.get(name) for name in INTERMEDIATE_FACTS},
            "recommendations": ["Correct the invalid input and run the analysis again."],
            "missing_information": [],
            "conflicts": conflicts,
            "validation_errors": errors,
            "human_review": "No deployment recommendation is made until input validation succeeds.",
        }

    fired = []
    supported_conclusions = []

    # Forward chaining until no new intermediate facts are produced.
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule["id"] in {r["id"] for r in fired}:
                continue

            results = [_eval_condition(facts, c) for c in rule["conditions"]]
            if all(result is True for result in results):
                fired.append(
                    {
                        "id": rule["id"],
                        "name": rule["name"],
                        "explanation": rule["explanation"],
                    }
                )

                if "sets" in rule:
                    fact_name, value = rule["sets"]
                    if facts.get(fact_name) is not value:
                        facts[fact_name] = value
                        changed = True

                if "conclusion" in rule and rule["conclusion"] not in supported_conclusions:
                    supported_conclusions.append(rule["conclusion"])

    # Explicit conflict handling suppresses positive deployment conclusions.
    if conflicts:
        supported_conclusions = [
            c for c in supported_conclusions
            if c == "BLOCK_DEPLOYMENT"
        ]

    # Blockers have priority over positive conclusions.
    if "BLOCK_DEPLOYMENT" in supported_conclusions:
        final = "BLOCK_DEPLOYMENT"
    elif "READY_FOR_PRODUCTION" in supported_conclusions:
        final = "READY_FOR_PRODUCTION"
    elif "READY_FOR_STAGING" in supported_conclusions:
        final = "READY_FOR_STAGING"
    else:
        # Caution is supported only when core technical readiness exists for production,
        # but rollback/monitoring evidence is missing or known incomplete.
        if (
            facts.get("deployment_environment") == "Production"
            and facts.get("technical_readiness") is True
            and facts.get("resilience_ready") is not True
        ):
            final = "DEPLOY_WITH_CAUTION"
        else:
            final = None

    # Missing info: unknown facts that are relevant to positive readiness.
    relevant_inputs = [
        "tests_passed",
        "test_coverage",
        "secret_scan_passed",
        "secrets_detected",
        "environment_variables_configured",
        "health_check_configured",
        "database_migrations_ready",
        "rollback_plan_available",
        "monitoring_configured",
    ]
    missing = [name for name in relevant_inputs if facts.get(name) is UNKNOWN]

    if final:
        conclusion_label = CONCLUSIONS[final]["label"]
        recommendations = list(CONCLUSIONS[final]["recommendations"])
    else:
        conclusion_label = "No Supported Conclusion"
        recommendations = [
            "Collect the missing evidence shown below.",
            "Re-run the analysis after the unknown or conflicting facts are resolved.",
            "Do not treat missing information as a pass or a fail.",
        ]

    if conflicts and final != "BLOCK_DEPLOYMENT":
        recommendations.insert(0, "Resolve conflicting inputs before making a deployment decision.")

    return {
        "status": "ok",
        "supported_conclusion": final,
        "conclusion_label": conclusion_label,
        "rules_fired": fired,
        "intermediate_facts": {name: facts.get(name) for name in INTERMEDIATE_FACTS},
        "recommendations": recommendations,
        "missing_information": missing,
        "conflicts": conflicts,
        "validation_errors": [],
        "human_review": "This is decision support only. A human reviewer must approve the final deployment decision.",
    }

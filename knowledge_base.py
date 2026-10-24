"""Knowledge base for the Cloud Deployment Readiness Advisor.

Tri-state values are represented as:
    True
    False
    None   -> Unknown
"""

APP_NAME = "Cloud Deployment Readiness Advisor"

CONCLUSIONS = {
    "READY_FOR_PRODUCTION": {
        "label": "Ready for Production",
        "recommendations": [
            "Perform a final human review of the deployment plan.",
            "Deploy during the approved change window.",
            "Watch health checks, logs, and alerts immediately after release.",
        ],
    },
    "READY_FOR_STAGING": {
        "label": "Ready for Staging",
        "recommendations": [
            "Deploy to staging and run smoke/integration tests.",
            "Validate health checks and environment-specific configuration.",
            "Do not promote to production until production-readiness evidence is complete.",
        ],
    },
    "DEPLOY_WITH_CAUTION": {
        "label": "Deploy With Caution",
        "recommendations": [
            "Resolve the missing resilience/observability evidence before a normal production release.",
            "If deployment is urgent, require explicit human approval and a monitored change window.",
            "Confirm rollback and monitoring status before increasing traffic.",
        ],
    },
    "BLOCK_DEPLOYMENT": {
        "label": "Block Deployment",
        "recommendations": [
            "Do not deploy until the blocking condition is corrected.",
            "Re-run the relevant validation/test step.",
            "Have a human reviewer confirm that the blocker is resolved.",
        ],
    },
}

# Rule format:
# conditions are evaluated by the inference engine.
# A rule fires only when every condition is definitely True.
# Unknown is never treated as False.
RULES = [
    {
        "id": "R1",
        "name": "Quality gate passes",
        "conditions": [
            ("tests_passed", "is", True),
            ("test_coverage", ">=", 80),
        ],
        "sets": ("quality_gate_passed", True),
        "explanation": "Automated tests pass and coverage is at least 80%.",
    },
    {
        "id": "R2",
        "name": "Secret state is clear",
        "conditions": [
            ("secret_scan_passed", "is", True),
            ("secrets_detected", "is", False),
        ],
        "sets": ("secret_state_clear", True),
        "explanation": "The secret scan passed and no secrets are reported.",
    },
    {
        "id": "R3",
        "name": "Core runtime configuration is ready",
        "conditions": [
            ("environment_variables_configured", "is", True),
            ("health_check_configured", "is", True),
        ],
        "sets": ("runtime_config_ready", True),
        "explanation": "Required environment variables and health checks are configured.",
    },
    {
        "id": "R4",
        "name": "Deployment baseline is ready",
        "conditions": [
            ("quality_gate_passed", "is", True),
            ("secret_state_clear", "is", True),
            ("runtime_config_ready", "is", True),
        ],
        "sets": ("deployment_baseline_ready", True),
        "explanation": "Quality, secret-safety, and runtime-configuration gates all passed.",
    },
    {
        "id": "R5",
        "name": "Technical readiness established",
        "conditions": [
            ("deployment_baseline_ready", "is", True),
            ("database_migrations_ready", "is", True),
        ],
        "sets": ("technical_readiness", True),
        "explanation": "The deployment baseline passed and database migrations are ready.",
    },
    {
        "id": "R6",
        "name": "Resilience is ready",
        "conditions": [
            ("rollback_plan_available", "is", True),
            ("monitoring_configured", "is", True),
        ],
        "sets": ("resilience_ready", True),
        "explanation": "A rollback plan and deployment monitoring are both available.",
    },
    {
        "id": "R7",
        "name": "Production release supported",
        "conditions": [
            ("deployment_environment", "==", "Production"),
            ("technical_readiness", "is", True),
            ("resilience_ready", "is", True),
        ],
        "conclusion": "READY_FOR_PRODUCTION",
        "explanation": "All technical and resilience evidence supports a production release.",
    },
    {
        "id": "R8",
        "name": "Staging release supported",
        "conditions": [
            ("deployment_environment", "==", "Staging"),
            ("technical_readiness", "is", True),
        ],
        "conclusion": "READY_FOR_STAGING",
        "explanation": "The technical readiness chain supports a staging deployment.",
    },
    {
        "id": "R9",
        "name": "Secrets block deployment",
        "conditions": [
            ("secrets_detected", "is", True),
        ],
        "conclusion": "BLOCK_DEPLOYMENT",
        "explanation": "A detected secret is a deployment blocker.",
    },
    {
        "id": "R10",
        "name": "Failed tests block deployment",
        "conditions": [
            ("tests_passed", "is", False),
        ],
        "conclusion": "BLOCK_DEPLOYMENT",
        "explanation": "Known failing tests are a deployment blocker.",
    },
    {
        "id": "R11",
        "name": "Production migration failure blocks deployment",
        "conditions": [
            ("deployment_environment", "==", "Production"),
            ("database_migrations_ready", "is", False),
        ],
        "conclusion": "BLOCK_DEPLOYMENT",
        "explanation": "Production deployment is blocked when database migrations are known not ready.",
    },
]

INPUT_FACTS = [
    "deployment_environment",
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

INTERMEDIATE_FACTS = [
    "quality_gate_passed",
    "secret_state_clear",
    "runtime_config_ready",
    "deployment_baseline_ready",
    "technical_readiness",
    "resilience_ready",
]

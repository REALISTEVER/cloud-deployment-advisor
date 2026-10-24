---
title: Cloud Deployment Readiness Advisor
emoji: ☁️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
---

# Cloud Deployment Readiness Advisor

An explainable knowledge-based decision-support tool for software deployment readiness.

## Purpose

The application evaluates structured deployment evidence and recommends one of the following:

- `READY_FOR_PRODUCTION`
- `READY_FOR_STAGING`
- `DEPLOY_WITH_CAUTION`
- `BLOCK_DEPLOYMENT`

When evidence is insufficient, it produces **No Supported Conclusion** rather than guessing.

## Reasoning pipeline

**Input → Validation → Structured facts → Rules → Inference → Explanation → Human review**

## Input facts

1. Target deployment environment
2. Automated tests passed
3. Test coverage percentage
4. Secret scan passed
5. Secrets detected
6. Environment variables configured
7. Health check configured
8. Database migrations ready
9. Rollback plan available
10. Monitoring/alerts configured

Tri-state boolean inputs are `True`, `False`, or `Unknown`.

## Intermediate facts

- `quality_gate_passed`
- `secret_state_clear`
- `runtime_config_ready`
- `deployment_baseline_ready`
- `technical_readiness`
- `resilience_ready`

## Validation / conflict handling

- Test coverage must be between 0 and 100.
- `Unknown` is not treated as `False`.
- A conflict is reported if the secret scan is marked passed while secrets are simultaneously reported as detected.
- Positive conclusions are not issued from missing evidence.

## API

The Gradio event is explicitly exposed as:

`/analyze`

From Python:

```python
from gradio_client import Client

client = Client("YOUR_USERNAME/YOUR_SPACE")
result = client.predict(
    deployment_environment="Production",
    tests_passed="True",
    test_coverage=92,
    secret_scan_passed="True",
    secrets_detected="False",
    environment_variables_configured="True",
    health_check_configured="True",
    database_migrations_ready="True",
    rollback_plan_available="True",
    monitoring_configured="True",
    api_name="/analyze",
)
print(result)
```

## Local testing

```bash
pip install -r requirements.txt
python test_cases.py
python app.py
```

## Human review

This application is decision support only. A human reviewer remains responsible for the deployment decision.

## Hugging Face setup

Create a Gradio Space, upload these project files, then select **ZeroGPU** in Space hardware/settings as required by the assignment. The rule engine itself does not require GPU computation.

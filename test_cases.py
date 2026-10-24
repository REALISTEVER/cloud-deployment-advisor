"""Local tests for the inference engine.

Run:
    python test_cases.py
"""

from inference_engine import analyze_facts

def base(**updates):
    facts = {
        "deployment_environment": "Production",
        "tests_passed": True,
        "test_coverage": 90,
        "secret_scan_passed": True,
        "secrets_detected": False,
        "environment_variables_configured": True,
        "health_check_configured": True,
        "database_migrations_ready": True,
        "rollback_plan_available": True,
        "monitoring_configured": True,
    }
    facts.update(updates)
    return facts

def rule_ids(result):
    return {r["id"] for r in result["rules_fired"]}

def test_ready_for_production_and_chain():
    r = analyze_facts(base())
    assert r["supported_conclusion"] == "READY_FOR_PRODUCTION"
    assert {"R1","R2","R3","R4","R5","R6","R7"} <= rule_ids(r)
    assert r["intermediate_facts"]["technical_readiness"] is True

def test_ready_for_staging():
    r = analyze_facts(base(deployment_environment="Staging"))
    assert r["supported_conclusion"] == "READY_FOR_STAGING"
    assert "R8" in rule_ids(r)

def test_failed_tests_block():
    r = analyze_facts(base(tests_passed=False))
    assert r["supported_conclusion"] == "BLOCK_DEPLOYMENT"
    assert "R10" in rule_ids(r)

def test_secret_block():
    r = analyze_facts(base(secret_scan_passed=False, secrets_detected=True))
    assert r["supported_conclusion"] == "BLOCK_DEPLOYMENT"
    assert "R9" in rule_ids(r)

def test_migration_block():
    r = analyze_facts(base(database_migrations_ready=False))
    assert r["supported_conclusion"] == "BLOCK_DEPLOYMENT"
    assert "R11" in rule_ids(r)

def test_unknown_is_not_false():
    r = analyze_facts(base(tests_passed=None))
    assert r["supported_conclusion"] is None
    assert "tests_passed" in r["missing_information"]
    assert "R10" not in rule_ids(r)

def test_conflict_detected():
    r = analyze_facts(base(secret_scan_passed=True, secrets_detected=True))
    assert r["conflicts"]
    assert r["supported_conclusion"] == "BLOCK_DEPLOYMENT"

def test_invalid_coverage():
    r = analyze_facts(base(test_coverage=120))
    assert r["status"] == "invalid"
    assert r["supported_conclusion"] is None

def test_no_supported_conclusion():
    r = analyze_facts(base(test_coverage=70))
    assert r["supported_conclusion"] is None
    assert "R1" not in rule_ids(r)

def test_deploy_with_caution():
    r = analyze_facts(base(rollback_plan_available=None))
    assert r["supported_conclusion"] == "DEPLOY_WITH_CAUTION"
    assert r["intermediate_facts"]["technical_readiness"] is True
    assert r["intermediate_facts"]["resilience_ready"] is None

def test_determinism():
    a = analyze_facts(base())
    b = analyze_facts(base())
    assert a == b

if __name__ == "__main__":
    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failures.append((test.__name__, exc))
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests)-len(failures)}/{len(tests)} tests passed")
    if failures:
        raise SystemExit(1)

from __future__ import annotations

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    cost = getattr(item, "koszt", None)
    if cost is None:
        return

    report.koszt = cost
    if report.passed:
        config = item.config
        config._koszt_total = getattr(config, "_koszt_total", 0) + cost
        config._koszt_cases = getattr(config, "_koszt_cases", []) + [(item.nodeid, cost)]


def pytest_report_teststatus(report: pytest.TestReport, config: pytest.Config):
    cost = getattr(report, "koszt", None)
    if report.when == "call" and report.passed and cost is not None:
        return "passed", "K", f"PASSED (koszt={cost})"
    return None


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config):
    total = getattr(config, "_koszt_total", None)
    if total is None:
        return

    cases = getattr(config, "_koszt_cases", [])
    if cases:
        terminalreporter.section("Koszt per test")
        for nodeid, cost in cases:
            terminalreporter.write_line(f"{nodeid}: {cost}")

    terminalreporter.section("Koszt summary")
    terminalreporter.write_line(f"Total koszt: {total}")

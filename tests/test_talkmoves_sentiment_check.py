from pathlib import Path

from app.llm import DemoStructuredProvider
from scripts.talkmoves_sentiment_check import PROXY_MAPPING, evaluate_provider, sample_proxy_rows, write_report


def test_proxy_mapping_is_explicit_and_excludes_unmapped_labels():
    assert PROXY_MAPPING == {"2": "confused", "3": "neutral", "4": "positive"}
    rows = sample_proxy_rows(per_label=3)
    assert len(rows) == 9
    assert {row["proxy_expected"] for row in rows} == {"confused", "neutral", "positive"}


def test_demo_agreement_report_is_repeatable_and_caveated():
    rows = sample_proxy_rows(per_label=2)
    result = evaluate_provider(DemoStructuredProvider(), rows)
    assert result["provider"] == "deterministic-demo-fallback"
    assert result["samples"] == 6
    assert 0 <= result["agreement_rate"] <= 1
    output = Path("validation/test-talkmoves-proxy.md")
    try:
        write_report(rows, [result], output)
        report = output.read_text(encoding="utf-8")
        assert "proxy agreement" in report.lower()
        assert "not confusion ground truth" in report.lower()
        assert "Asking for more information" in report
    finally:
        output.unlink(missing_ok=True)

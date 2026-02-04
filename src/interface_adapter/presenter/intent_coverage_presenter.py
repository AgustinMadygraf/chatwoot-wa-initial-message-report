from __future__ import annotations

from application.use_cases.intent_coverage_report import IntentCoverageReport


def format_intent_coverage(
    report: IntentCoverageReport,
    min_count: int,
    conversation_limit: int = 0,
) -> str:
    lines: list[str] = []
    lines.append("=== Reporte de cobertura de intenciones ===")
    lines.append(f"Mensajes leídos: {report.total_rows}")
    lines.append(f"Mensajes con texto: {report.messages_with_text}")
    lines.append(f"Mensajes sin texto: {report.messages_without_text}")
    lines.append(f"Parseos fallidos: {report.parse_failures}")
    lines.append(f"Predicciones nombradas: {report.named_predictions}")
    lines.append(f"Predicciones sin intención reconocida: {report.fallback_predictions}")

    lines.append("")
    if report.messages_with_text:
        coverage_pct = (report.named_predictions / report.messages_with_text) * 100
        fallback_pct = (report.fallback_predictions / report.messages_with_text) * 100
    else:
        coverage_pct = fallback_pct = 0.0
    lines.append(
        f"Cobertura activa: {report.named_predictions}/{report.messages_with_text} "
        f"({coverage_pct:.1f}% con intención)"
    )
    lines.append(
        f"Predicciones sin intención (fallback): {report.fallback_predictions} "
        f"({fallback_pct:.1f}%)"
    )

    lines.append("")
    header = f"{'Intent':<32} {'Count':>5} {'Pct':>6} {'Status':>8}"
    lines.append(f"Intenciones entrenadas (mínimo {min_count}):")
    lines.append(header)
    lines.append("-" * len(header))
    for coverage in report.training_coverage:
        pct = _compute_pct(coverage.observed_count, max(report.messages_with_text, 1))
        status = "OK" if coverage.meets_threshold else f"< {min_count}"
        lines.append(
            f"{coverage.intent:<32} {coverage.observed_count:>5} {pct:>6} {status:>8}"
        )

    undercovered = [
        coverage.intent
        for coverage in report.training_coverage
        if not coverage.meets_threshold
    ]
    if undercovered:
        lines.append("")
        lines.append("Intenciones con cobertura baja:")
        for intent in undercovered:
            lines.append(f" - {intent}")

    if report.unknown_intents:
        lines.append("")
        lines.append("Intenciones inferidas fuera del NLU:")
        for name, count in report.unknown_intents[:10]:
            lines.append(f" - {name}: {count}")

    if report.samples:
        lines.append("")
        lines.append(f"Muestras ({len(report.samples)} predicciones):")
        for idx, sample in enumerate(report.samples, start=1):
            text = _truncate(sample.text)
            intent = sample.intent or "nulo"
            conf = f"{sample.confidence:.3f}" if sample.confidence is not None else "n/a"
            fallback_suffix = " (fallback)" if sample.is_fallback else ""
            lines.append(f"{idx:02d}. {text} -> {intent}{fallback_suffix} @ {conf}")

    if conversation_limit and report.conversations:
        lines.append("")
        lines.append(f"Resumen por conversaciones (máx {conversation_limit}):")
        header = f"{'Conv ID':<10} {'Top intent (count)':<26} {'Msgs':>4} {'Fallback %':>11} {'Último texto':<48}"
        lines.append(header)
        lines.append("-" * len(header))
        for summary in report.conversations[:conversation_limit]:
            intent_label = (
                f"{summary.top_intent} ({summary.top_intent_count})"
                if summary.top_intent
                else "fallback"
            )
            last_text = _truncate(summary.last_text, max_length=42)
            conf = (
                f"{summary.last_confidence:.3f}"
                if summary.last_confidence is not None
                else "n/a"
            )
            lines.append(
                f"{str(summary.conversation_id):<10} {intent_label:<26} "
                f"{summary.total_messages:>4} {summary.fallback_pct:8.1f}% "
                f"{last_text} [{conf}]"
            )

    return "\n".join(lines)


def _compute_pct(count: int, total: int) -> str:
    ratio = (count / total) * 100 if total > 0 else 0.0
    return f"{ratio:5.1f}%"


def _truncate(text: str, max_length: int = 64) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 3] + "..."


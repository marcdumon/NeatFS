from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import humanize


def human_size(num_bytes: int) -> str:
    try:
        return humanize.naturalsize(num_bytes, binary=True)
    except Exception:  # noqa: BLE001
        return str(num_bytes)


 


def badge(text: str, *, color: str = "#EEF2FF", text_color: str = "#111827") -> str:
    style = (
        f"display:inline-block;padding:2px 8px;border-radius:9999px;"
        f"background:{color};color:{text_color};font-size:12px;margin-right:6px;"
        f"border:1px solid rgba(0,0,0,0.06)"
    )
    return f"<span style=\"{style}\">{text}</span>"


@dataclass
class Metric:
    label: str
    value: str
    help: Optional[str] = None


def metrics_row(metrics: list[Metric]) -> str:
    chips = []
    for m in metrics:
        title = f" title=\"{m.help}\"" if m.help else ""
        chips.append(
            f"<div style=\"padding:8px 10px;border-radius:10px;border:1px solid #e5e7eb;"  # border-gray-200
            f"display:inline-flex;align-items:center;margin-right:8px;background:white\">"
            f"<div style=\"font-size:12px;color:#6b7280;margin-right:6px\">{m.label}</div>"
            f"<div style=\"font-weight:600;color:#111827\"{title}>{m.value}</div>"
            f"</div>"
        )
    return "".join(chips)



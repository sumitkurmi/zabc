# MODULE: Network Complaint Portal - Flow Tracing
# Reusable end-to-end timing trace helper using contextvars and time.perf_counter().

import os
import sys
import uuid
import time
import logging
from contextvars import ContextVar
from typing import Dict, Any, List, Optional

logger = logging.getLogger("flow_trace")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ContextVar storing current active request FlowTrace
current_trace_var: ContextVar[Optional["FlowTrace"]] = ContextVar("current_trace_var", default=None)


def get_current_trace() -> Optional["FlowTrace"]:
    """Returns currently active FlowTrace instance for context thread/task or None."""
    return current_trace_var.get()


class StepRecord:
    """Dataclass holding timing and status for a single execution step."""

    def __init__(self, name: str, depth: int, duration_ms: float, status: str, details: Dict[str, Any]):
        self.name = name
        self.depth = depth
        self.duration_ms = duration_ms
        self.status = status
        self.details = details


class TraceStepContext:
    """Sync and async friendly context manager recording step duration and status."""

    def __init__(self, trace: "FlowTrace", name: str, details: Dict[str, Any]):
        self.trace = trace
        self.name = name
        self.details = details
        self.depth = trace.current_depth
        self.start_t = 0.0

    def add(self, **kwargs):
        """Adds key=value details to the current step."""
        self.details.update(kwargs)

    def _start(self):
        self.start_t = time.perf_counter()
        self.trace.current_depth += 1

    def _end(self, exc_val: Optional[BaseException]):
        duration_ms = (time.perf_counter() - self.start_t) * 1000.0
        self.trace.current_depth = max(0, self.trace.current_depth - 1)
        if exc_val is not None:
            status = f"FAILED ({type(exc_val).__name__})"
        else:
            status = "OK"

        record = StepRecord(
            name=self.name,
            depth=self.depth,
            duration_ms=duration_ms,
            status=status,
            details=self.details.copy()
        )
        self.trace.steps.append(record)

    def __enter__(self):
        self._start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end(exc_val)
        return False  # Re-raise exception unchanged

    async def __aenter__(self):
        self._start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._end(exc_val)
        return False  # Re-raise exception unchanged


class DummyStepContext:
    """No-op step context manager used when tracing is disabled."""

    def add(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class FlowTrace:
    """Per-request trace manager collecting execution steps and logging unified block."""

    def __init__(self, label: str, chat_id: Optional[str] = None):
        self.trace_id = uuid.uuid4().hex[:6]
        self.label = label
        self.chat_id_short = chat_id[:8] if chat_id else None
        self.start_t = time.perf_counter()
        self.steps: List[StepRecord] = []
        self.current_depth = 0
        self.token = None

        # Environment variable overrides
        env_enabled = os.environ.get("FLOW_TRACE", "true").lower() in ("true", "1", "yes")
        self.enabled = env_enabled

        try:
            self.slow_ms = float(os.environ.get("FLOW_TRACE_SLOW_MS", "3000"))
        except Exception:
            self.slow_ms = 3000.0

    def __enter__(self):
        if self.enabled:
            self.token = current_trace_var.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            current_trace_var.reset(self.token)
        return False

    def step(self, name: str, **kwargs) -> TraceStepContext | DummyStepContext:
        """Creates a timing step context manager."""
        if not self.enabled:
            return DummyStepContext()
        return TraceStepContext(self, name, kwargs)

    def _format_time(self, ms: float) -> str:
        """Formats time in ms or seconds (>1000ms)."""
        if ms >= 1000.0:
            return f"{ms / 1000.0:.2f} s"
        return f"{ms:.0f} ms"

    def finish(self):
        """Prints formatted execution trace block to terminal."""
        if not self.enabled:
            return

        try:
            total_duration_ms = (time.perf_counter() - self.start_t) * 1000.0
            total_str = self._format_time(total_duration_ms)

            header_info = f"chat={self.chat_id_short}  " if self.chat_id_short else ""
            lines = [
                "",
                f"[trace {self.trace_id}] {self.label}  {header_info}total {total_str}"
            ]

            llm_time_ms = 0.0
            rag_time_ms = 0.0
            db_time_ms = 0.0

            for s in self.steps:
                indent = "  " * (s.depth + 1)
                time_str = self._format_time(s.duration_ms)
                slow_marker = "  SLOW" if s.duration_ms >= self.slow_ms else ""

                # Format details e.g. provider=gemini model=gemini-1.5-flash
                details_parts = []
                for k, v in s.details.items():
                    details_parts.append(f"{k}={v}")
                details_str = (" " + " ".join(details_parts)) if details_parts else ""

                # Status display
                status_str = f"  {s.status}" if s.status != "OK" or s.depth == 0 else ""
                if s.status == "OK" and s.depth == 0:
                    status_str = "  OK"

                line = f"{indent}{s.name:<32s} {time_str:>8s}{status_str}{details_str}{slow_marker}"
                lines.append(line)

                # Sum outer steps for footer breakdown
                if s.depth == 0:
                    if s.name.startswith("llm.") or s.name == "guard.classify":
                        llm_time_ms += s.duration_ms
                    elif s.name.startswith("rag."):
                        rag_time_ms += s.duration_ms
                    elif s.name.startswith("db."):
                        db_time_ms += s.duration_ms

            # Summary footer
            other_time_ms = max(0.0, total_duration_ms - (llm_time_ms + rag_time_ms + db_time_ms))
            llm_str = self._format_time(llm_time_ms)
            rag_str = self._format_time(rag_time_ms)
            db_str = self._format_time(db_time_ms)
            other_str = self._format_time(other_time_ms)

            lines.append("  " + "-" * 50)
            lines.append(f"  llm time {llm_str} | rag time {rag_str} | db time {db_str} | other {other_str}")
            lines.append("")

            output_text = "\n".join(lines)
            logger.info(output_text)

        except Exception as e:
            # Tracing failures must never break the main request
            pass

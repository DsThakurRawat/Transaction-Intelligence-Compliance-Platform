from typing import Protocol, Optional
from sqlalchemy.orm import Session

class RunResult:
    def __init__(self, findings_count: int, message: str):
        self.findings_count = findings_count
        self.message = message

class Analyzer(Protocol):
    name: str

    def required_inputs(self) -> list[str]:
        """What data it needs (e.g. ['transactions'], ['ledger','processor'])."""
        ...

    def run(self, session: Session, config: dict) -> RunResult:
        """Process inputs, persist Findings (idempotent), return a summary."""
        ...

    def evaluate(self, session: Session) -> Optional[str]:
        """Optional: returns a markdown Scorecard string if applicable."""
        ...

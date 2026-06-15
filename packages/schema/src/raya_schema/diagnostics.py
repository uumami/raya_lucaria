from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    message: str
    path: Path | None = None
    field: str | None = None
    next_action: str | None = None

    def format(self) -> str:
        parts = [self.severity.upper(), self.message]
        if self.path is not None:
            parts.append(f"file={self.path}")
        if self.field:
            parts.append(f"field={self.field}")
        if self.next_action:
            parts.append(f"next={self.next_action}")
        return " | ".join(parts)


@dataclass
class ValidationReport:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    files_read: list[Path] = field(default_factory=list)
    outputs_written: list[Path] = field(default_factory=list)
    context: str | None = None

    @property
    def ok(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)

    @property
    def issues(self) -> list[Diagnostic]:
        return self.diagnostics

    def add_error(
        self,
        message: str,
        *,
        path: Path | None = None,
        field: str | None = None,
        next_action: str | None = None,
    ) -> None:
        self.diagnostics.append(
            Diagnostic(
                severity="error",
                message=message,
                path=path,
                field=field,
                next_action=next_action,
            )
        )

    def add_info(
        self,
        message: str,
        *,
        path: Path | None = None,
        field: str | None = None,
        next_action: str | None = None,
    ) -> None:
        self.diagnostics.append(
            Diagnostic(
                severity="info",
                message=message,
                path=path,
                field=field,
                next_action=next_action,
            )
        )

    def read_file(self, path: Path) -> None:
        if path not in self.files_read:
            self.files_read.append(path)

    def wrote_output(self, path: Path) -> None:
        if path not in self.outputs_written:
            self.outputs_written.append(path)

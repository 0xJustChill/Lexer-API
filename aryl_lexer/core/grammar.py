import re
from pathlib import Path

from .rule import Rule, ALIASES


class Grammar:
    def __init__(self) -> None:
        self._rules: list[Rule] = []

    @property
    def rules(self) -> list[Rule]:
        return list(self._rules)

    def load(self, path: Path | str) -> None:
        resolved = Path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"Grammar file not found: {resolved}")

        self._rules.clear()
        seen_names: set[str] = set()
        seen_patterns: set[str] = set()

        for lineno, raw_line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()

            if not line or line.startswith("//") or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                raise SyntaxError(f"Line {lineno}: expected 'NAME PATTERN [FLAGS]', got: {line!r}")

            name, pattern_token, *flag_parts = parts
            flags = frozenset(flag_parts)

            # Validate flags
            known_flags = {"skip"}
            unknown = flags - known_flags
            if unknown:
                raise NotImplementedError(f"Line {lineno}: unrecognized flags: {unknown}")

            # Resolve pattern
            if pattern_token in ALIASES:
                raw_pattern = ALIASES[pattern_token]
            elif pattern_token.startswith('"') and pattern_token.endswith('"'):
                raw_pattern = re.escape(pattern_token[1:-1])
            else:
                raw_pattern = pattern_token

            # Uniqueness checks
            if name in seen_names:
                raise ValueError(f"Line {lineno}: duplicate rule name '{name}'")
            if raw_pattern in seen_patterns:
                raise ValueError(f"Line {lineno}: duplicate pattern '{raw_pattern}' (rule '{name}')")

            seen_names.add(name)
            seen_patterns.add(raw_pattern)

            self._rules.append(Rule(name=name, raw_pattern=raw_pattern, flags=flags))

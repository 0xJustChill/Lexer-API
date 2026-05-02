import re
from dataclasses import dataclass, field
from re import Pattern, Match


ALIASES: dict[str, str] = {
    "@Ident":  r"[a-zA-Z_][a-zA-Z0-9_]*",
    "@Int":    r"[+-]?[0-9]+",
    "@Uint":   r"[0-9]+",
    "@String": r'"[^"]*"',
}


@dataclass(frozen=True)
class Rule:
    name: str
    raw_pattern: str
    flags: frozenset[str] = field(default_factory=frozenset)
    _compiled: Pattern[str] = field(init=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        try:
            compiled = re.compile(self.raw_pattern)
        except re.error as e:
            raise ValueError(f"Rule '{self.name}': invalid regex '{self.raw_pattern}': {e}")

        # Guard against zero-length matches (infinite loop risk)
        test = compiled.match("")
        if test is not None and test.end() == 0:
            raise ValueError(
                f"Rule '{self.name}': pattern '{self.raw_pattern}' can match zero characters"
            )

        object.__setattr__(self, "_compiled", compiled)

    def match_at(self, source: str, pos: int) -> Match[str] | None:
        return self._compiled.match(source, pos)

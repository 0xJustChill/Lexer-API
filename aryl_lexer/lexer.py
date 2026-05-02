from pathlib import Path
from typing import Iterator

from .core.grammar import Grammar
from .core.token import Token


class ArylLexer:
    def __init__(self, grammar: Grammar) -> None:
        if not grammar.rules:
            raise ValueError("Grammar has no rules loaded")
        self._grammar = grammar
        self._source: str = ""
        self._pos: int = 0

    def load(self, source: str | Path) -> None:
        if isinstance(source, Path):
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source}")
            self._source = source.read_text(encoding="utf-8")
        else:
            self._source = source
        self._pos = 0

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        while self._pos < len(self._source):
            pos = self._pos

            for rule in self._grammar.rules:
                match = rule.match_at(self._source, pos)
                if match is None:
                    continue

                self._pos = match.end()

                if "skip" in rule.flags:
                    break  # consumed, no token emitted — restart loop

                return Token(type=rule.name, value=match.group(), offset=pos)

            else:
                # Fallback: no rule matched — emit error token, consume 1 char
                char = self._source[pos]
                self._pos = pos + 1
                return Token(
                    type="",
                    value=char,
                    offset=pos,
                    is_error=True,
                    what=f"Unmatched character {char!r}",
                    code="ERR_UNMATCHED_CHAR",
                )

        raise StopIteration

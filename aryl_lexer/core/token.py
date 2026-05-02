from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    offset: int
    is_error: bool = False
    what: str | None = None
    code: str | None = None

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValueError(f"Token.offset must be >= 0, got {self.offset}")
        if self.is_error and not self.what:
            raise ValueError("Error tokens must carry a 'what' description")
        if not self.is_error and not self.type:
            raise ValueError("Non-error tokens must have a non-empty 'type'")

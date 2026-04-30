# ChillLexer

## 🎯 Vision & Problem
Existing tokenization engines are either coupled with parsers (ANTLR, PLY) or require code generation and heavy dependencies (Tree-sitter, Flex). `ChillLexer` addresses a specific need: **a pure, iterative lexer driven by external grammar, with zero dependencies and non-blocking error handling**.  
Ideal for file preprocessing, lightweight lexical analysis, injection into custom pipelines, or cross-language integration.

## 🏗️ Architecture & Flow
```
[.ryl] → Grammar.load() → [Rule] (name, compiled_re, flags)
   ↓
ChillLexer.load(source) → cursor pos=0, immutable source
   ↓
LOOP next():
 ├─ match_at(pos) → yield Token(type, value, offset)
 ├─ flag "skip" ? → pos += match.end(), continue (no token emitted)
 └─ fallback → yield Token(is_error=True, what, code), pos += 1
```
- **Zero AST, zero parsing** : pure tokenization only.
- **Priority** : declaration order in `.ryl` = first match wins.
- **Performance** : single `re` compilation at load time, anchored `match()`, zero unnecessary backtracking.
- **Typing** : Python 3.10+, strict `typing`, `@dataclass(frozen=True)`, immutability guaranteed.

## 📜 Grammar Syntax (`.ryl` – Format B Light)
```ryl
# Structure: TOKEN_NAME [PATTERN | @ALIAS | "LITERAL"] [FLAGS...]
IDENT      @Ident
INT        @Int
KW_IF      "if"
OP_EQ      ==
WHITESPACE \s+      skip
COMMENT    //.*     skip
```
| Element | MVP Role |
|---------|----------|
| `TOKEN_NAME` | Unique identifier, valid Python. Duplicate → load error. |
| `PATTERN` | `re`-compatible regex. Strict compilation. Duplicate raw pattern → error. |
| `@ALIAS` | Built-in sugar: `@Int`, `@Uint`, `@String`, `@Ident` |
| `"LITERAL"` | Auto-escaped exact match (`re.escape()`). Useful for keywords/operators. |
| `skip` | MVP flag: consumes the match but emits no token. |
| `# ...` | Line comment. Ignored at load time. |

**Validation locks (loading)** :
- Unique names in file
- Unique raw patterns (prevents redundant rules)
- `re.compile()` success + guaranteed match ≥1 char (anti-infinite loop)
- Unrecognized flags → `NotImplementedError`

## 🔌 API Reference
| Object | Responsibility | Signature (MVP) |
|--------|----------------|-----------------|
| `Token` | Immutable result container | `Token(type: str, value: str, offset: int, is_error: bool = False, what: str \| None = None, code: str \| None = None)` |
| `Rule` | Compiled rule + metadata | `Rule(name, raw_pattern, flags)` + `match_at(source, pos) -> Match \| None` |
| `Grammar` | `.ryl` parser, validation, storage | `Grammar()` → `load(path: Path \| str)` |
| `ChillLexer` | Stateless iterator over source | `ChillLexer(grammar)` → `load(source)` → `__iter__` / `next() -> Token` |

## 🛡️ Error Handling & Fallback
- **Trigger** : No pattern matches at `pos`.
- **MVP Behavior** : Non-blocking. Emits `Token(is_error=True)`, consumes **exactly 1 character**, continues iteration.
- **Metadata** : `what` (human-readable description), `code` (technical identifier, e.g., `ERR_UNMATCHED_CHAR`), `offset` (raw position).
- **V2** : Option `strict=True` to raise `LexerSyntaxError` instead of emitting a token.

## 📦 Project Status & Roadmap
| Phase | Status | Scope |
|-------|--------|-------|
| **MVP (in progress)** | 🟡 Design locked, implementation started, `skip`, 1-char fallback, strict validation, iterative API |
| **V2** | 🔵 Planned | `/* */` comments, `priority:`/`longest:` flags, runtime `Enum` generation, C header export (`.h`), VSCode extension (syntax highlighting) |
| **V3+** | 🟣 Exploratory | `.ryl → .py` compilation cache, large file streaming, integrated performance analysis |

## 📝 Usage Example
```python
from aryl_lexer import Grammar, ChillLexer

grammar = Grammar()
grammar.load("syntax.ryl")

lexer = ChillLexer(grammar)
lexer.load("string")

lexer.load("filepath")

for token in lexer:
    if token.is_error:
        print(f"[ERR @{token.offset}] {token.what}")
    else:
        print(f"{token.type}: '{token.value}'")
```

## ⚖️ Technical Choices & Constraints
- **Regex engine** : Standard `re`. Upfront validation forbids `.*`, backreferences, zero-length patterns. A custom engine would add 2-4 weeks of maintenance for marginal gain in this scope.
- **Priority** : File order. Avoids `longest match` algorithms or complex backtracking. Deterministic and predictable.
- **1-char fallback** : Guarantees cursor progression, eliminates infinite loops, facilitates positional debugging.
- **Zero dependencies** : Python stdlib only. Maximum portability, trivial deployment.

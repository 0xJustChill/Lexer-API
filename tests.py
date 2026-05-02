import sys
sys.path.insert(0, "")

from pathlib import Path
from aryl_lexer import Token, Rule, Grammar, ArylLexer

GRAMMAR_PATH = Path("sample.ryl")

# ── Token tests ────────────────────────────────────────────────────────────────

def test_token_happy():
    t = Token(type="IDENT", value="foo", offset=0)
    assert t.type == "IDENT" and t.value == "foo" and not t.is_error

def test_token_error():
    e = Token(type="", value="@", offset=5, is_error=True,
              what="Unmatched character '@'", code="ERR_UNMATCHED_CHAR")
    assert e.is_error and e.what

def test_token_frozen():
    t = Token(type="IDENT", value="x", offset=0)
    try:
        t.type = "OTHER"  # type: ignore
        assert False, "Should have raised"
    except Exception:
        pass

def test_token_negative_offset():
    try:
        Token(type="X", value="x", offset=-1)
        assert False
    except ValueError:
        pass

def test_error_token_missing_what():
    try:
        Token(type="", value="@", offset=0, is_error=True)
        assert False
    except ValueError:
        pass

# ── Rule tests ─────────────────────────────────────────────────────────────────

def test_rule_match():
    r = Rule(name="INT", raw_pattern=r"[0-9]+")
    m = r.match_at("123abc", 0)
    assert m and m.group() == "123"

def test_rule_no_match():
    r = Rule(name="INT", raw_pattern=r"[0-9]+")
    assert r.match_at("abc", 0) is None

def test_rule_anchored():
    r = Rule(name="INT", raw_pattern=r"[0-9]+")
    assert r.match_at("abc123", 3).group() == "123"

def test_rule_zero_length_rejected():
    try:
        Rule(name="BAD", raw_pattern=r"a*")  # can match empty
        assert False
    except ValueError:
        pass

def test_rule_invalid_regex():
    try:
        Rule(name="BAD", raw_pattern=r"[unclosed")
        assert False
    except ValueError:
        pass

# ── Grammar tests ──────────────────────────────────────────────────────────────

def test_grammar_loads():
    g = Grammar()
    g.load(GRAMMAR_PATH)
    names = [r.name for r in g.rules]
    assert "IDENT" in names and "KW_IF" in names

def test_grammar_skip_flag():
    g = Grammar()
    g.load(GRAMMAR_PATH)
    ws = next(r for r in g.rules if r.name == "WHITESPACE")
    assert "skip" in ws.flags

def test_grammar_alias_resolution():
    g = Grammar()
    g.load(GRAMMAR_PATH)
    ident = next(r for r in g.rules if r.name == "IDENT")
    assert ident.raw_pattern == r"[a-zA-Z_][a-zA-Z0-9_]*"

def test_grammar_literal_escaping():
    g = Grammar()
    g.load(GRAMMAR_PATH)
    kw = next(r for r in g.rules if r.name == "KW_IF")
    import re
    assert re.escape("if") == kw.raw_pattern

def test_grammar_duplicate_name(tmp_path):
    f = tmp_path / "bad.ryl"
    f.write_text("IDENT @Ident\nIDENT @Uint\n")
    g = Grammar()
    try:
        g.load(f)
        assert False
    except ValueError:
        pass

def test_grammar_unknown_flag(tmp_path):
    f = tmp_path / "bad.ryl"
    f.write_text("IDENT @Ident   turbo\n")
    g = Grammar()
    try:
        g.load(f)
        assert False
    except NotImplementedError:
        pass

# ── Lexer tests ────────────────────────────────────────────────────────────────

def test_lexer_basic():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("foo 42")
    tokens = list(lexer)
    types = [t.type for t in tokens if not t.is_error]
    assert types == ["IDENT", "INT"]

def test_lexer_skip_whitespace():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("  foo  ")
    tokens = [t for t in lexer if not t.is_error]
    assert len(tokens) == 1 and tokens[0].type == "IDENT"

def test_lexer_keyword_priority():
    # KW_IF declared after IDENT — but "if" should still match IDENT first
    # This tests declaration-order priority
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("if")
    tokens = [t for t in lexer if not t.is_error]
    # IDENT comes first in file → wins
    assert tokens[0].type == "IDENT"

def test_lexer_error_token():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("@")
    tokens = list(lexer)
    assert len(tokens) == 1 and tokens[0].is_error
    assert tokens[0].code == "ERR_UNMATCHED_CHAR"

def test_lexer_error_consumes_one_char():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("@foo")
    tokens = list(lexer)
    assert tokens[0].is_error and tokens[0].value == "@"
    assert tokens[1].type == "IDENT" and tokens[1].value == "foo"

def test_lexer_offset_tracking():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("foo 42")
    tokens = [t for t in lexer if not t.is_error]
    assert tokens[0].offset == 0
    assert tokens[1].offset == 4

def test_lexer_load_from_path(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("foo 42")
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load(src)
    tokens = [t for t in lexer if not t.is_error]
    assert [t.type for t in tokens] == ["IDENT", "INT"]

def test_lexer_reloadable():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("foo")
    list(lexer)  # exhaust
    lexer.load("42")
    tokens = list(lexer)
    assert tokens[0].type == "INT"

def test_lexer_empty_source():
    g = Grammar(); g.load(GRAMMAR_PATH)
    lexer = ArylLexer(g)
    lexer.load("")
    assert list(lexer) == []

# ── Runner ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import inspect, traceback
    tests = {k: v for k, v in globals().items() if k.startswith("test_")}
    passed = failed = 0
    for name, fn in tests.items():
        try:
            # inject tmp_path fixture if needed
            if "tmp_path" in inspect.signature(fn).parameters:
                import tempfile
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            print(f"  [OK] {name}")
            passed += 1
        except Exception as e:
            print(f"  [KO] {name}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")

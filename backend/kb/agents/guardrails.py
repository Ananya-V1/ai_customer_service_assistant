import re
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    ok: bool
    reason: str = ""


# if question is greater than max length
def check_question_length(question, max_length):
    if len(question) > max_length:
        return GuardrailResult(
            ok=False,
            reason=f"Question is too long ({len(question)} chars, max {max_length}).",
        )
    return GuardrailResult(ok=True)


# identify patterns that are out of scope
_OUT_OF_SCOPE_PATTERNS = [
    re.compile(r"\bwrite (me |us )?(a |an )?(poem|song|story|joke|essay)\b", re.IGNORECASE),
    re.compile(r"\btell me a joke\b", re.IGNORECASE),
    re.compile(r"\btranslate\b", re.IGNORECASE),
    re.compile(r"\bwrite (some |me )?(a |an )?code\b", re.IGNORECASE),
    re.compile(r"\bwhat('?s| is) the weather\b", re.IGNORECASE),
    re.compile(r"\bwho (won|is the (president|prime minister))\b", re.IGNORECASE),
]


def check_topic_scope_cheap(question):
    for pattern in _OUT_OF_SCOPE_PATTERNS:
        if pattern.search(question):
            return GuardrailResult(ok=False, reason="Question appears unrelated to customer support.")
    return GuardrailResult(ok=True)

# SQL can only be a SELECT statement (all other commands are forbidden)
_FORBIDDEN_SQL_KEYWORDS = re.compile(
    r"\b(DELETE|DROP|UPDATE|INSERT|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|EXEC|EXECUTE|"
    r"ATTACH|REPLACE|MERGE|CALL)\b",
    re.IGNORECASE,
)


def check_sql_is_readonly_select(sql):
    stripped = sql.strip()
    if not stripped:
        return GuardrailResult(ok=False, reason="Empty SQL query.")
    if not stripped.lstrip("(").strip().upper().startswith("SELECT"):
        return GuardrailResult(ok=False, reason="Only SELECT statements are allowed.")
    if "--" in stripped or "/*" in stripped:
        return GuardrailResult(ok=False, reason="SQL comments are not allowed.")
    # Allow exactly one trailing semicolon; reject anything with a semicolon
    # elsewhere (i.e. more than one statement).
    body = stripped[:-1] if stripped.endswith(";") else stripped
    if ";" in body:
        return GuardrailResult(ok=False, reason="Only a single SQL statement is allowed.")
    if _FORBIDDEN_SQL_KEYWORDS.search(body):
        return GuardrailResult(ok=False, reason="Query contains a disallowed keyword.")
    return GuardrailResult(ok=True)


# SQL commands can only reference allowed table
_TABLE_REF = re.compile(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)", re.IGNORECASE)


def check_sql_table_allowlist(sql, allowed_tables):
    allowed = {t.lower() for t in allowed_tables}
    referenced = {match.split(".")[-1].lower() for match in _TABLE_REF.findall(sql)}
    disallowed = referenced - allowed
    if disallowed:
        return GuardrailResult(
            ok=False,
            reason=f"Query references table(s) not allowed: {', '.join(sorted(disallowed))}.",
        )
    return GuardrailResult(ok=True)


# --- 5. Row limit is enforced server-side, regardless of the generated SQL -
_TRAILING_LIMIT = re.compile(r"\bLIMIT\s+\d+\s*$", re.IGNORECASE)


def enforce_row_limit(sql, max_rows):
    stripped = sql.strip()
    if stripped.endswith(";"):
        stripped = stripped[:-1].strip()
    stripped = _TRAILING_LIMIT.sub("", stripped).strip()
    return f"{stripped} LIMIT {max_rows}"


# --- 7. Final answer length cap --------------------------------------------

def truncate_answer(answer, max_length):
    if len(answer) <= max_length:
        return answer
    return answer[:max_length].rstrip() + "... (truncated)"

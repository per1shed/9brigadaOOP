from app.domain.posting_rules import PostingRule
from app.support.types import CheckResult
from app.support.errors import DomainError


class LegacyPostingAdapter(PostingRule):
    def __init__(self, legacy):
        self._legacy = legacy

    def check(self, entry):
        allowed = self._legacy.accepts(
            entry.entry_type, entry.amount.amount
        )
        if type(allowed) is not bool:
            raise DomainError("INVALID_RESULT")
        if allowed:
            return CheckResult(True)
        return CheckResult(False, "ENTRY_TYPE_DENIED")

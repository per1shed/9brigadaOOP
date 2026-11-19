from abc import ABC, abstractmethod
from app.support.types import CheckResult, Money, checked, choice
from app.support.errors import DomainError


class PostingRule(ABC):
    @abstractmethod
    def check(self, entry):
        raise NotImplementedError


class AllowedEntryTypeRule(PostingRule):
    def __init__(self, types):
        self._types = frozenset(types)
        for value in self._types:
            choice(value, ("DEBIT", "CREDIT"), "INVALID_CONFIG")

    def check(self, entry):
        if entry.entry_type not in self._types:
            return CheckResult(False, "ENTRY_TYPE_DENIED")
        return CheckResult(True)


class MaximumEntryAmountRule(PostingRule):
    def __init__(self, maximum):
        if not isinstance(maximum, Money):
            raise DomainError("INVALID_CONFIG")
        self._maximum = maximum

    def check(self, entry):
        entry.amount.same_currency(self._maximum)
        if entry.amount.amount > self._maximum.amount:
            return CheckResult(False, "ENTRY_AMOUNT_LIMIT")
        return CheckResult(True)


class AccountPrefixRule(PostingRule):
    def __init__(self, prefixes):
        self._prefixes = tuple(prefixes)
        if any(not isinstance(prefix,str) or not prefix for prefix in self._prefixes):
            raise DomainError("INVALID_CONFIG")

    def check(self, entry):
        for prefix in self._prefixes:
            if entry.account_id.startswith(prefix):
                return CheckResult(True)
        return CheckResult(False, "ACCOUNT_PREFIX_DENIED")


class PostingRuleGroup(PostingRule):
    """Последовательность правил: первый отказ, без изменения входных объектов."""

    def __init__(self, rules):
        self._rules = tuple(rules)
        for rule in self._rules:
            if not isinstance(rule, PostingRule):
                raise DomainError("INVALID_CONFIG")

    def check(self, entry):
        for rule in self._rules:
            result = checked(rule.check(entry))
            if not result.allowed:
                return result
        return CheckResult(True)


class AmountBandRule(PostingRule):
    def __init__(self, minimum, maximum):
        if not isinstance(minimum, Money) or not isinstance(maximum, Money):
            raise DomainError("INVALID_CONFIG")
        minimum.same_currency(maximum)
        if minimum.amount > maximum.amount:
            raise DomainError("INVALID_CONFIG")
        self._minimum = minimum
        self._maximum = maximum

    def check(self, entry):
        entry.amount.same_currency(self._minimum)
        if self._minimum.amount <= entry.amount.amount <= self._maximum.amount:
            return CheckResult(True)
        return CheckResult(False, "ENTRY_AMOUNT_OUTSIDE_BAND")

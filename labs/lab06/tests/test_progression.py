import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from app import api
from app.support.errors import DomainError


def code(expected, operation):
    with pytest.raises(DomainError) as caught:
        operation()
    assert caught.value.code == expected

from app.domain.ledger import LedgerEntry
from app.support.types import money

def test_progression_refused_entry_does_not_reserve_id():
    service = api.create()
    first = LedgerEntry("E1", "T", "ACC-1", money("10"), "DEBIT")
    service.record(first)
    code("ENTRY_AMOUNT_LIMIT", lambda: service.record(LedgerEntry("E2", "T", "ACC-1", money("1001"), "DEBIT")))
    assert service.entries_for_transaction("T") == (first,)
    second = LedgerEntry("E2", "T", "ACC-1", money("20"), "CREDIT")
    service.record(second)
    assert service.entries_for_transaction("T") == (first, second)
    assert service.signed_total("ACC-1", "EUR") == Decimal("10")

from app.domain.posting_rules import PostingRule
from app.services.ledger_service import LedgerService
from app.support.types import Repository, CheckResult

def test_progression_posting_dependency_error_does_not_consume_id():
    calls = []
    class Once(PostingRule):
        def check(self, item):
            calls.append(item)
            if len(calls) == 1: raise DomainError("TEMPORARY")
            return CheckResult(True)
    repo = Repository("entry_id", "DUPLICATE_ENTRY")
    rules = [Once()]
    service = LedgerService(repo, rules)
    rules.clear()
    entry = LedgerEntry("E", "T", "ACC-1", money("10"), "DEBIT")
    code("TEMPORARY", lambda: service.record(entry))
    assert len(calls) == 1 and repo.all() == ()
    service.record(entry)
    assert calls == [entry, entry] and repo.all() == (entry,)

from app.domain.posting_rules import PostingRuleGroup, PostingRule
from app.support.types import CheckResult

def test_progression_group_order_snapshot_and_identity():
    calls = []
    class Rule(PostingRule):
        def __init__(self, name, allowed=True): self.name, self.allowed = name, allowed
        def check(self, entry):
            calls.append(self.name)
            return CheckResult(True) if self.allowed else CheckResult(False, self.name)
    deny = Rule("DENIED", False)
    rules = [Rule("FIRST"), deny, Rule("NEVER")]
    group = PostingRuleGroup(rules)
    rules.clear()
    assert group.check(object()).code == "DENIED"
    assert calls == ["FIRST", "DENIED"]
    calls.clear()
    deny.name = "SAME_INSTANCE"
    assert group.check(object()).code == "SAME_INSTANCE"
    assert calls == ["FIRST", "SAME_INSTANCE"]
    assert PostingRuleGroup([]).check(object()).allowed
    calls.clear()
    nested = PostingRuleGroup([PostingRuleGroup([Rule("A")]), Rule("B")])
    assert nested.check(object()).allowed and calls == ["A", "B"]

def test_progression_group_bad_result_and_error():
    calls = []
    class Bad(PostingRule):
        def check(self, entry): calls.append("bad"); return None
    code("INVALID_RESULT", lambda: PostingRuleGroup([Bad()]).check(object()))
    assert calls == ["bad"]
    class Broken(PostingRule):
        def check(self, entry): raise DomainError("RULE_FAILED")
    code("RULE_FAILED", lambda: PostingRuleGroup([Broken()]).check(object()))
    code("INVALID_CONFIG", lambda: PostingRuleGroup([object()]))


def test_progression_default_assembly_uses_group(monkeypatch):
    calls = []
    def check(self, *args):
        calls.append(args)
        return CheckResult(False, "GROUP_USED")
    monkeypatch.setattr(PostingRuleGroup, "check", check)
    service = api.create()
    item = LedgerEntry("E", "T", "ACC-1", money("10"), "DEBIT")
    code("GROUP_USED", lambda: service.record(item))
    assert len(calls) == 1

from app.domain.posting_rules import AmountBandRule
from app.domain.ledger import LedgerEntry
from app.support.types import money

def test_progression_extra_lab06():
    rule = AmountBandRule(money("10"), money("20"))
    good = LedgerEntry("E1", "T", "A", money("10"), "CREDIT")
    bad = LedgerEntry("E2", "T", "A", money("25"), "CREDIT")
    assert rule.check(good).allowed
    assert rule.check(bad).code == "ENTRY_AMOUNT_OUTSIDE_BAND"
    code("INVALID_CONFIG", lambda: AmountBandRule(money("30"), money("20")))

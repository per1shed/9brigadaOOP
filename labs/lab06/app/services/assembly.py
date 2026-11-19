from app.services.ledger_service import LedgerService
from app.support.types import Repository, money
from app.domain.posting_rules import (
    AccountPrefixRule,
    AllowedEntryTypeRule,
    MaximumEntryAmountRule,
    PostingRuleGroup,
)

def build_service(repository=None, rules=None):
    if repository is None:
        repository = Repository("entry_id", "DUPLICATE_ENTRY")
    if rules is None:
        group = PostingRuleGroup([
            AllowedEntryTypeRule({"DEBIT", "CREDIT"}),
            MaximumEntryAmountRule(money("1000")),
            AccountPrefixRule(("ACC-", "MERCH-")),
        ])
        rules = [group]
    return LedgerService(repository, rules)

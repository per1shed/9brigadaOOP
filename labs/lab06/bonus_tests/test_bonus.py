import pytest
from decimal import Decimal
from datetime import date, datetime, timezone, timedelta
from app import api
from app.support.errors import DomainError
from app.support.types import Repository, CheckResult, Money, money


def error(code, operation):
    with pytest.raises(DomainError) as caught:
        operation()
    assert caught.value.code == code


def invoke(service, method, *args, **kwargs):
    return api.call(service, method, *args, **kwargs)

def test_single_compensation_does_not_edit_original():
    from app.domain.ledger import LedgerEntry
    service=api.create()
    original=LedgerEntry("E1","T","ACC-1",money("10"),"DEBIT")
    service.record(original)
    reversed_entry=service.make_reversal("E1","E2")
    assert reversed_entry.entry_type=="CREDIT" and reversed_entry.reverses_entry_id=="E1"
    assert original.entry_type=="DEBIT"
    assert service.signed_total("ACC-1","EUR")==0
    error("REVERSAL_NOT_ALLOWED",lambda:service.make_reversal("E1","E3"))
    error("REVERSAL_NOT_ALLOWED",lambda:service.make_reversal("E2","E4"))

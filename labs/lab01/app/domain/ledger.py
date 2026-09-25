from dataclasses import dataclass
from decimal import Decimal
from app.support.types import identifier, positive, choice, Money


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    transaction_id: str
    account_id: str
    amount: Money
    entry_type: str
    reverses_entry_id: str | None = None

    def __post_init__(self):
        identifier(self.entry_id)
        identifier(self.transaction_id)
        identifier(self.account_id)
        positive(self.amount)
        choice(self.entry_type, ("DEBIT", "CREDIT"), "INVALID_ENTRY_TYPE")
        if self.reverses_entry_id is not None:
            identifier(self.reverses_entry_id)

    def signed_amount(self) -> Decimal:
        """Возвращает знаковую сумму записи: -amount для DEBIT, +amount для CREDIT."""
        if self.entry_type == "DEBIT":
            return -self.amount.amount
        return self.amount.amount

    def describe(self) -> str:
        # Бонус ЛР1: "E1:DEBIT:10.00:EUR"
        return f"{self.entry_id}:{self.entry_type}:{self.amount.amount:.2f}:{self.amount.currency}"
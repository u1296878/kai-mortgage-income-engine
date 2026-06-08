from dataclasses import dataclass, field


@dataclass
class ScheduleEProperty:
    column: str
    address: str | None = None
    blocks: dict[str, dict] = field(default_factory=dict)
    fair_rental_days: float | None = None
    rents_received: float = 0.0
    insurance: float = 0.0
    mortgage_interest: float = 0.0
    other_interest: float = 0.0
    taxes: float = 0.0
    depreciation_depletion: float = 0.0
    total_expenses: float = 0.0

    @property
    def property_key(self) -> str:
        return self.column.lower()

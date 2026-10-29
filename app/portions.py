"""Explicit consumed amounts and user-reported measurement provenance."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PortionInput(BaseModel):
    grams: float = Field(gt=0, le=5000, allow_inf_nan=False)
    consumed_percent: float = Field(default=100, gt=0, le=100, allow_inf_nan=False)
    leftover_amount: float | None = Field(default=None, ge=0, le=5000, allow_inf_nan=False)
    quantity_basis: Literal['unspecified', 'scale', 'measuring_container', 'label', 'manual_estimate', 'visual_estimate', 'typical_serving'] = 'unspecified'
    unit: Literal['g', 'ml'] | None = None

    @model_validator(mode='after')
    def check_consumption(self):
        if self.leftover_amount is not None:
            if self.consumed_percent != 100:
                raise ValueError('Use leftovers OR consumed percentage, not both')
            if self.leftover_amount >= self.grams:
                raise ValueError('Leftovers must be less than served; do not log an uneaten item')
        if self.consumed_amount() < .01:
            raise ValueError('Consumed amount must be at least 0.01 g or ml')
        return self

    def consumed_amount(self):
        served = Decimal(str(self.grams))
        value = served - Decimal(str(self.leftover_amount)) if self.leftover_amount is not None else served * Decimal(str(self.consumed_percent)) / 100
        return float(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

    def consumption_percent(self):
        return self.consumed_percent if self.leftover_amount is None else round(self.consumed_amount() / self.grams * 100, 6)

    def check_unit(self, expected):
        if self.unit is not None and self.unit != expected:
            raise ValueError(f'This food uses {expected}; grams and millilitres cannot be interchanged without density')
        if self.quantity_basis == 'scale' and expected != 'g':
            raise ValueError('A scale measures grams, not ml. Use measured liquid volume or a matching per-gram food record')
        if self.quantity_basis == 'measuring_container' and expected != 'ml':
            raise ValueError('Container volume cannot establish grams without food density')

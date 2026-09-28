from decimal import Decimal

from sentinel_chain.api.serializers import decimal_to_plain


def test_decimal_to_plain_strips_scientific_notation():
    assert decimal_to_plain(Decimal("1E-8")) == "0.00000001"
    assert decimal_to_plain(Decimal("100.00000000")) == "100.00000000"

from livenza_loyalty_core import balance, points_for_paid_amount


def test_balance_is_sum_of_ledger_entries():
    assert balance([('credit',100),('debit',30),('credit',5)]) == 75


def test_points_config_uses_paid_minor_units():
    assert points_for_paid_amount(25000, points_per_100_inr=1) == 2
    assert points_for_paid_amount(9900, points_per_100_inr=1) == 0
    assert points_for_paid_amount(10000, points_per_100_inr=3) == 3

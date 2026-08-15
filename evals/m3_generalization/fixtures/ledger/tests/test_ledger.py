from bank.ledger import Ledger


def test_recording_and_balance():
    ledger = Ledger()
    ledger.record("salary", 1000)
    ledger.record("rent", -400)
    assert ledger.balance() == 600.0


def test_seeded_entries():
    ledger = Ledger([("opening", 25.0)])
    assert ledger.balance() == 25.0


def test_new_ledger_starts_empty():
    first = Ledger()
    first.record("salary", 1000)
    second = Ledger()
    assert second.history() == []
    assert second.balance() == 0


def test_seeding_does_not_share_the_input_list():
    entries = [("opening", 10.0)]
    ledger = Ledger(entries)
    ledger.record("fee", -1.0)
    assert entries == [("opening", 10.0)]

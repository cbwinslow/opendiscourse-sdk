from opendiscourse.services.validation import validate_record, validate_records


def test_validate_record_success():
    record = {"id": "1", "source": "test", "content": "text"}
    assert validate_record(record)


def test_validate_record_missing_field():
    record = {"id": "1", "source": "test"}
    assert not validate_record(record)


def test_validate_records():
    records = [
        {"id": "1", "source": "test", "content": "a"},
        {"id": "2", "source": "test", "content": "b"},
    ]
    assert validate_records(records)

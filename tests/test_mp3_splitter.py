import pytest
import typer

from mp3_splitter import format_duration, parse_time_to_ms, parse_timestamps


@pytest.mark.parametrize(
    ("text", "expected_ms"),
    [
        ("0", 0),
        ("90", 90_000),
        ("90.5", 90_500),
        ("1:30", 90_000),
        ("1:30.5", 90_500),
        ("0:05", 5_000),
        ("1:02:03", 3_723_000),
        ("1:02:03.25", 3_723_250),
    ],
)
def test_parse_time_to_ms(text, expected_ms):
    assert parse_time_to_ms(text) == pytest.approx(expected_ms)


@pytest.mark.parametrize("text", ["", "abc", "1:2:3:4", "1:xx"])
def test_parse_time_to_ms_rejects_garbage(text):
    with pytest.raises(ValueError):
        parse_time_to_ms(text)


def test_parse_timestamps_rejects_negative():
    # parse_time_to_ms accepts "-5" as a valid float; range validation
    # (0 <= v <= duration) is parse_timestamps's job, not the parser's.
    with pytest.raises(typer.BadParameter):
        parse_timestamps("-5", duration_ms=200_000)


@pytest.mark.parametrize(
    ("ms", "expected"),
    [
        (0, "0:00"),
        (5_000, "0:05"),
        (90_000, "1:30"),
        (3_723_000, "1:02:03"),
    ],
)
def test_format_duration(ms, expected):
    assert format_duration(ms) == expected


def test_parse_timestamps_accepts_mixed_formats():
    assert parse_timestamps("30, 1:00, 90.5", duration_ms=200_000) == [30_000, 60_000, 90_500]


def test_parse_timestamps_rejects_out_of_range():
    with pytest.raises(typer.BadParameter):
        parse_timestamps("1:00", duration_ms=30_000)


def test_parse_timestamps_rejects_non_increasing():
    with pytest.raises(typer.BadParameter):
        parse_timestamps("60, 30", duration_ms=200_000)


def test_parse_timestamps_rejects_duplicates():
    with pytest.raises(typer.BadParameter):
        parse_timestamps("30, 30", duration_ms=200_000)

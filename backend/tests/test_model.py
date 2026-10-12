import json
import pathlib

import pytest

from app.model import classify
from app.parsing import ParseError, parse_episode

DATA = pathlib.Path(__file__).resolve().parents[1] / "sample_data"


def _load(name):
    return parse_episode(name, (DATA / name).read_bytes())


def test_healthy_is_nominal():
    assert classify(_load("episode_healthy.json")[0]).label == "Nominal operation"


def test_phase_c_open_detected():
    p = classify(_load("episode_phase_c_open.json")[-1])
    assert p.label == "Phase C disconnection" and p.confidence > 0.8


def test_harmonics_detected():
    assert classify(_load("episode_harmonics.json")[-1]).label == "Harmonic distortion"


def test_unbalance_detected():
    assert classify(_load("episode_unbalance.json")[-1]).label == "Grid unbalance"


def test_bad_width_rejected():
    bad = json.dumps([{"mea_value": [1.0] * 59}]).encode()
    with pytest.raises(ParseError):
        parse_episode("x.json", bad)

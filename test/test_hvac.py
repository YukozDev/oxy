# pylint: disable=E0401, W0621
"""Tests unitaires pour les opérations HVAC."""

import os
import pytest
from src.main import App


@pytest.fixture
def app_instance(tmp_path):
    """Fixture pour initialiser l'application avec une base de données temporaire."""
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = str(db_path)

    os.environ["T_MAX"] = "30"
    os.environ["T_MIN"] = "10"
    os.environ["HOST"] = "http://fake-host"
    os.environ["TOKEN"] = "fake-token"

    app = App()

    app.send_action_to_hvac = lambda action: None
    return app


def test_hvac_turn_on_ac(app_instance):
    """Si température >= T_MAX → AC ON."""
    action = app_instance.take_action(35)
    assert action == "TurnOnAc"


def test_hvac_turn_on_heater(app_instance):
    """Si température <= T_MIN → Heater ON."""
    action = app_instance.take_action(5)
    assert action == "TurnOnHeater"


def test_hvac_none(app_instance):
    """Si T_MIN < température < T_MAX → None."""
    action = app_instance.take_action(20)
    assert action == "None"

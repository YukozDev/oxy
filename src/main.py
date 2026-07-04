"""Main module for OxygenCS HVAC controller."""

import logging
import json
import time
import os
import sqlite3

from dotenv import load_dotenv
from signalrcore.hub_connection_builder import HubConnectionBuilder
import requests


class App:
    """Main application class for OxygenCS HVAC controller."""

    def __init__(self):
        load_dotenv()

        self._hub_connection = None

        self.config = {
            "ticks": 10,
            "host": os.getenv("HOST"),
            "token": os.getenv("TOKEN"),
            "t_max": float(os.getenv("T_MAX") or 0.0),
            "t_min": float(os.getenv("T_MIN") or 0.0),
            "database_url": os.getenv("DATABASE_URL"),
        }

        # Connexion BD initialisée une seule fois
        self.db = self.init_db()

    def init_db(self):
        """Initialize database connection and create table if needed."""
        conn = sqlite3.connect(self.config["database_url"])
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature REAL NOT NULL,
                action TEXT NOT NULL
            );
        """
        )

        conn.commit()
        return conn

    def __del__(self):
        if self._hub_connection is not None:
            self._hub_connection.stop()

    def start(self):
        """Start Oxygen CS."""
        self.setup_sensor_hub()
        self._hub_connection.start()
        print("Press CTRL+C to exit.")
        while True:
            time.sleep(2)

    def setup_sensor_hub(self):
        """Configure hub connection and subscribe to sensor data events."""
        self._hub_connection = (
            HubConnectionBuilder()
            .with_url(f"{self.config['host']}/SensorHub?token={self.config['token']}")
            .configure_logging(logging.INFO)
            .with_automatic_reconnect(
                {
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 5,
                    "max_attempts": 999,
                }
            )
            .build()
        )
        self._hub_connection.on("ReceiveSensorData", self.on_sensor_data_received)
        self._hub_connection.on_open(lambda: print("||| Connection opened."))
        self._hub_connection.on_close(lambda: print("||| Connection closed."))
        self._hub_connection.on_error(
            lambda data: print(f"||| An exception was thrown closed: {data.error}")
        )

    def on_sensor_data_received(self, data):
        """Callback method to handle sensor data on reception."""
        try:
            print(data[0]["date"] + " --> " + data[0]["data"], flush=True)
            timestamp = data[0]["date"]
            temperature = float(data[0]["data"])

            action = self.take_action(temperature)
            self.save_event_to_database(timestamp, temperature, action)
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(err)

    def take_action(self, temperature):
        """Take action to HVAC depending on current temperature."""
        if float(temperature) >= float(self.config["t_max"]):
            self.send_action_to_hvac("TurnOnAc")
            return "TurnOnAc"
        if float(temperature) <= float(self.config["t_min"]):
            self.send_action_to_hvac("TurnOnHeater")
            return "TurnOnHeater"
        return "None"

    def send_action_to_hvac(self, action):
        """Send action query to the HVAC service."""
        url = (
            f"{self.config['host']}/api/hvac/"
            f"{self.config['token']}/{action}/{self.config['ticks']}"
        )
        # Ajout d'un timeout pour éviter le hang indéfini (W3101)
        r = requests.get(url, timeout=10)
        details = json.loads(r.text)
        print(details, flush=True)

    def save_event_to_database(self, timestamp, temperature, action):
        """Save sensor data into database."""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO measurements (timestamp, temperature, action) VALUES (?, ?, ?)",
                (timestamp, temperature, action),
            )
            self.db.commit()
            print("Saved to DB:", timestamp, temperature, action)
        except sqlite3.Error as e:
            print("DB error:", e)


if __name__ == "__main__":
    app = App()
    app.start()

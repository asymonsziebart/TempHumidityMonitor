<<<<<<< HEAD
# Temperature and Humidity Monitor

A web-based monitoring system that displays real-time temperature and humidity data from an Arduino with DHT11 sensor.

## Features

- Real-time temperature and humidity monitoring
- Historical data visualization with 24-hour graphs
- Dark/Light theme toggle
- Local weather comparison
- Data export to CSV
- Alert system for temperature and humidity thresholds
- Arduino connection status indicator

## Hardware Requirements

- Arduino board
- DHT11 temperature and humidity sensor
- USB cable for Arduino connection

## Software Requirements

- Python 3.x
- Flask
- Arduino IDE
- Required Python packages (install using `pip install -r requirements.txt`):
  - flask
  - pyserial
  - requests

## Setup Instructions

1. Connect DHT11 sensor to Arduino:
   - VCC to 5V
   - GND to GND
   - DATA to Digital Pin 2

2. Upload Arduino code:
   - Open `DHT11_JSON.ino` in Arduino IDE
   - Install required libraries:
     - DHT sensor library
     - ArduinoJson
   - Upload to Arduino

3. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open web browser and navigate to:
   ```
   http://localhost:8080
   ```

## Configuration

Temperature and humidity thresholds can be adjusted in `app.py`:
```python
ALERT_THRESHOLDS = {
    'temp_min': 60,  # °F
    'temp_max': 80,  # °F
    'humid_min': 30,  # %
    'humid_max': 60   # %
}
``` 
=======
# TempHumidityMonitor
>>>>>>> ff0d7388e492a8c6c14ca4f4f93f25dc6c3b11ab

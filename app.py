from flask import Flask, render_template_string, jsonify, send_file
import serial
import serial.tools.list_ports
import json
from threading import Lock
import time
import socket
import sqlite3
from datetime import datetime, timedelta
import io
import csv
import requests

app = Flask(__name__)

# Global variables to store the latest readings and settings
latest_data = {
    'temperature': 0,
    'humidity': 0,
    'timestamp': '',
    'temp_min': 0,
    'temp_max': 0,
    'humid_min': 0,
    'humid_max': 0
}

# Alert thresholds
ALERT_THRESHOLDS = {
    'temp_min': 60,  # °F
    'temp_max': 80,  # °F
    'humid_min': 30,  # %
    'humid_max': 60   # %
}

# Add this after the ALERT_THRESHOLDS definition
WEATHER_API_KEY = "3eba242df2664d5a85b142627241411"
weather_data = {
    'temperature': 0,
    'humidity': 0,
    'condition': '',
    'icon': '',
    'last_update': ''
}

data_lock = Lock()
arduino = None

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings
                 (timestamp TEXT, temperature REAL, humidity REAL)''')
    conn.commit()
    conn.close()

def save_reading(temperature, humidity):
    """Save a reading to the database"""
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO readings VALUES (?, ?, ?)',
              (timestamp, temperature, humidity))
    conn.commit()
    conn.close()

def get_daily_stats():
    """Get min/max values for the day"""
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''SELECT MIN(temperature), MAX(temperature),
                        MIN(humidity), MAX(humidity)
                 FROM readings
                 WHERE timestamp LIKE ?''', (f'{today}%',))
    result = c.fetchone()
    conn.close()
    if result[0] is not None:
        return {
            'temp_min': result[0],
            'temp_max': result[1],
            'humid_min': result[2],
            'humid_max': result[3]
        }
    return {
        'temp_min': 0,
        'temp_max': 0,
        'humid_min': 0,
        'humid_max': 0
    }

def get_graph_data():
    """Get the last 24 hours of readings for the graph"""
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''SELECT timestamp, temperature, humidity
                 FROM readings
                 WHERE timestamp > ?
                 ORDER BY timestamp ASC''', (yesterday,))
    data = c.fetchall()
    conn.close()
    return data

# Initialize database
init_db()

def find_arduino():
    """Try to find and connect to the Arduino"""
    global arduino
    
    # Close existing connection if any
    if arduino is not None:
        try:
            arduino.close()
        except:
            pass
        arduino = None
    
    print("Connecting to Arduino on COM3...")
    
    try:
        arduino = serial.Serial('COM3', 9600, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        print("Successfully connected to Arduino on COM3")
        return True
    except Exception as e:
        print(f"Failed to connect to COM3: {str(e)}")
        return False

def read_arduino_data():
    """Read data from Arduino if available"""
    global arduino
    
    if arduino is None:
        if not find_arduino():
            return
            
    if arduino and arduino.is_open:
        try:
            if arduino.in_waiting:
                line = arduino.readline().decode('utf-8').strip()
                print(f"Raw data received from Arduino: {line}")  # Debug print
                if line:
                    try:
                        data = json.loads(line)
                        print(f"Parsed JSON data: {data}")  # Debug print
                        with data_lock:
                            # Convert Celsius to Fahrenheit
                            celsius = data.get('temperature', 0)
                            fahrenheit = (celsius * 9.0/5.0) + 32.0
                            print(f"Temperature: {celsius}°C -> {fahrenheit}°F")  # Debug print
                            latest_data['temperature'] = fahrenheit
                            latest_data['humidity'] = data.get('humidity', 0)
                            latest_data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Save to database
                            save_reading(fahrenheit, data.get('humidity', 0))
                            
                            # Update daily stats
                            stats = get_daily_stats()
                            latest_data.update(stats)
                            
                            print(f"Updated sensor data: {latest_data}")  # Debug print
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON data received: {line}")
                        print(f"JSON Error: {str(e)}")
        except Exception as e:
            print(f"Error reading Arduino data: {str(e)}")
            arduino = None  # Reset connection on error

def update_weather():
    """Get current weather data"""
    try:
        response = requests.get(
            f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q=auto:ip&aqi=no"
        )
        data = response.json()
        weather_data['temperature'] = data['current']['temp_f']
        weather_data['humidity'] = data['current']['humidity']
        weather_data['condition'] = data['current']['condition']['text']
        weather_data['icon'] = "https:" + data['current']['condition']['icon']
        weather_data['last_update'] = data['current']['last_updated']
    except Exception as e:
        print(f"Error updating weather: {e}")

@app.route('/')
def main_page():
    """Render the main page"""
    # Get graph data for the last 24 hours
    graph_data = get_graph_data()
    timestamps = [row[0] for row in graph_data]
    temperatures = [row[1] for row in graph_data]
    humidities = [row[2] for row in graph_data]
    
    update_weather()  # Get initial weather data
    
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Temperature & Humidity Monitor</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            :root {
                --bg-color: #f4f4f9;
                --text-color: #333;
                --card-bg: white;
                --accent-color: #007bff;
<<<<<<< HEAD
                --home-color: #28a745;  /* Added: Green color for home button */
=======
>>>>>>> origin/main
            }
            
            [data-theme="dark"] {
                --bg-color: #1a1a1a;
                --text-color: #ffffff;
                --card-bg: #2d2d2d;
                --accent-color: #0d6efd;
<<<<<<< HEAD
                --home-color: #218838;  /* Added: Darker green for dark mode */
=======
>>>>>>> origin/main
            }
            
            body {
                font-family: Arial, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                transition: all 0.3s ease;
            }
            
            .dashboard {
                background: var(--card-bg);
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                margin: 20px;
                width: 90%;
                max-width: 1200px;
            }
            
            h1, h2 {
                color: var(--text-color);
                text-align: center;
            }
            
            .controls {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
            }
            
            .button {
                background-color: var(--accent-color);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
            }
            
            .button:hover {
                opacity: 0.9;
            }
            
            .reading {
                display: flex;
                justify-content: space-between;
                margin: 20px 0;
                padding: 20px;
                background: var(--bg-color);
                border-radius: 8px;
                flex-wrap: wrap;
            }
            
            .reading > div {
                flex: 1;
                min-width: 200px;
                margin: 10px;
                text-align: center;
            }
            
            .value {
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
                color: var(--accent-color);
            }
            
            .label {
                font-size: 1.2em;
                color: var(--text-color);
                opacity: 0.8;
            }
            
            .timestamp {
                font-size: 0.9em;
                color: var(--text-color);
                opacity: 0.6;
            }
            
            .alert {
                color: #dc3545;
                font-weight: bold;
            }
            
            .weather-info {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-top: 10px;
            }
            
            .weather-icon {
                width: 50px;
                height: 50px;
            }
            
            .status {
                text-align: center;
                padding: 10px;
                margin-top: 10px;
                border-radius: 5px;
            }
            
            .connected {
                background-color: #d4edda;
                color: #155724;
            }
            
            .disconnected {
                background-color: #f8d7da;
                color: #721c24;
            }
            
<<<<<<< HEAD
            .home-button {
                background-color: var(--home-color);
            }
            
            .home-button:hover {
                opacity: 0.9;
            }
            
=======
>>>>>>> origin/main
            @media (max-width: 768px) {
                .reading {
                    flex-direction: column;
                }
                .reading > div {
                    margin: 10px 0;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <h1>Temperature & Humidity Monitor</h1>
            
            <div class="controls">
                <button class="button" onclick="toggleTheme()">Toggle Dark Mode</button>
                <a href="/export_csv" class="button">Export Data (CSV)</a>
<<<<<<< HEAD
                <a href="http://192.168.1.77:8081/" class="button home-button">Home</a>
=======
>>>>>>> origin/main
            </div>
            
            <div class="status {{ 'connected' if arduino else 'disconnected' }}">
                {{ 'Arduino Connected' if arduino else 'Arduino Disconnected - Check Connection' }}
            </div>
            
            <div class="reading">
                <div>
                    <div class="label">Temperature</div>
                    <div class="value"><span id="temperature">{{ "%.1f"|format(latest_data.temperature) }}</span>°F</div>
                    <div class="alert" id="temp-alert">
                        {% if latest_data.temperature < ALERT_THRESHOLDS['temp_min'] %}
                            Temperature is below minimum threshold!
                        {% elif latest_data.temperature > ALERT_THRESHOLDS['temp_max'] %}
                            Temperature is above maximum threshold!
                        {% endif %}
                    </div>
                    <div>Min: <span id="temp-min">{{ "%.1f"|format(latest_data.temp_min) }}</span>°F</div>
                    <div>Max: <span id="temp-max">{{ "%.1f"|format(latest_data.temp_max) }}</span>°F</div>
                </div>
                
                <div>
                    <div class="label">Humidity</div>
                    <div class="value"><span id="humidity">{{ "%.1f"|format(latest_data.humidity) }}</span>%</div>
                    <div class="alert" id="humid-alert">
                        {% if latest_data.humidity < ALERT_THRESHOLDS['humid_min'] %}
                            Humidity is below minimum threshold!
                        {% elif latest_data.humidity > ALERT_THRESHOLDS['humid_max'] %}
                            Humidity is above maximum threshold!
                        {% endif %}
                    </div>
                    <div>Min: <span id="humid-min">{{ "%.1f"|format(latest_data.humid_min) }}</span>%</div>
                    <div>Max: <span id="humid-max">{{ "%.1f"|format(latest_data.humid_max) }}</span>%</div>
                </div>
                
                <div>
                    <div class="label">Local Weather</div>
                    <div class="value">
                        <span id="weather-temp">{{ "%.1f"|format(weather_data.temperature) }}</span>°F
                        <span id="weather-humid">{{ "%.1f"|format(weather_data.humidity) }}</span>%
                    </div>
                    <div class="weather-info">
                        <img id="weather-icon" src="{{ weather_data.icon }}" alt="Weather icon" class="weather-icon">
                        <span id="weather-condition">{{ weather_data.condition }}</span>
                    </div>
                    <div class="timestamp">Updated: <span id="weather-update">{{ weather_data.last_update }}</span></div>
                </div>
            </div>
            
            <div id="temp-chart"></div>
            <div id="humid-chart"></div>
        </div>
        
        <script>
            function updateReadings() {
                fetch('/data')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('temperature').textContent = data.temperature.toFixed(1);
                        document.getElementById('humidity').textContent = data.humidity.toFixed(1);
                        document.getElementById('timestamp').textContent = data.timestamp;
                        
                        // Update min/max values
                        document.getElementById('temp-min').textContent = data.temp_min.toFixed(1);
                        document.getElementById('temp-max').textContent = data.temp_max.toFixed(1);
                        document.getElementById('humid-min').textContent = data.humid_min.toFixed(1);
                        document.getElementById('humid-max').textContent = data.humid_max.toFixed(1);
                        
                        // Check for alerts
                        const tempAlert = document.getElementById('temp-alert');
                        const humidAlert = document.getElementById('humid-alert');
                        
                        if (data.temperature < {{ ALERT_THRESHOLDS['temp_min'] }}) {
                            tempAlert.textContent = 'Temperature is below minimum threshold!';
                        } else if (data.temperature > {{ ALERT_THRESHOLDS['temp_max'] }}) {
                            tempAlert.textContent = 'Temperature is above maximum threshold!';
                        } else {
                            tempAlert.textContent = '';
                        }
                        
                        if (data.humidity < {{ ALERT_THRESHOLDS['humid_min'] }}) {
                            humidAlert.textContent = 'Humidity is below minimum threshold!';
                        } else if (data.humidity > {{ ALERT_THRESHOLDS['humid_max'] }}) {
                            humidAlert.textContent = 'Humidity is above maximum threshold!';
                        } else {
                            humidAlert.textContent = '';
                        }
                    });
            }
            
            function updateWeather() {
                fetch('/weather')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('weather-temp').textContent = data.temperature.toFixed(1);
                        document.getElementById('weather-humid').textContent = data.humidity.toFixed(1);
                        document.getElementById('weather-condition').textContent = data.condition;
                        document.getElementById('weather-icon').src = data.icon;
                        document.getElementById('weather-update').textContent = data.last_update;
                    });
            }
            
            // Update readings every 2 seconds
            setInterval(updateReadings, 2000);
            
            // Update weather every 5 minutes
            setInterval(updateWeather, 300000);
            
            // Initial updates
            updateReadings();
            updateWeather();
            
            // Theme toggle
            function toggleTheme() {
                const html = document.documentElement;
                if (html.getAttribute('data-theme') === 'dark') {
                    html.removeAttribute('data-theme');
                    localStorage.setItem('theme', 'light');
                } else {
                    html.setAttribute('data-theme', 'dark');
                    localStorage.setItem('theme', 'dark');
                }
            }
            
            // Initialize theme
            document.addEventListener('DOMContentLoaded', () => {
                const savedTheme = localStorage.getItem('theme');
                if (savedTheme === 'dark') {
                    document.documentElement.setAttribute('data-theme', 'dark');
                }
            });
            
            // Temperature chart
            const tempData = {
                x: {{ timestamps|tojson }},
                y: {{ temperatures|tojson }},
                type: 'scatter',
                name: 'Temperature',
                line: {color: '#ff7f0e'}
            };
            
            const tempLayout = {
                title: 'Temperature History (24h)',
                xaxis: {
                    title: 'Time (Last 24 Hours)',
                    showgrid: true,
                    gridcolor: 'rgba(128,128,128,0.2)',
                    tickangle: -45
                },
                yaxis: {
                    title: 'Temperature (°F)',
                    showgrid: true,
                    gridcolor: 'rgba(128,128,128,0.2)'
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {color: getComputedStyle(document.body).getPropertyValue('--text-color')},
                margin: {t: 30, b: 80}
            };
            
            Plotly.newPlot('temp-chart', [tempData], tempLayout);
            
            // Humidity chart
            const humidData = {
                x: {{ timestamps|tojson }},
                y: {{ humidities|tojson }},
                type: 'scatter',
                name: 'Humidity',
                line: {color: '#1f77b4'}
            };
            
            const humidLayout = {
                title: 'Humidity History (24h)',
                xaxis: {
                    title: 'Time (Last 24 Hours)',
                    showgrid: true,
                    gridcolor: 'rgba(128,128,128,0.2)',
                    tickangle: -45
                },
                yaxis: {
                    title: 'Humidity (%)',
                    showgrid: true,
                    gridcolor: 'rgba(128,128,128,0.2)'
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {color: getComputedStyle(document.body).getPropertyValue('--text-color')},
                margin: {t: 30, b: 80}
            };
            
            Plotly.newPlot('humid-chart', [humidData], humidLayout);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(
        template,
        latest_data=latest_data,
        weather_data=weather_data,
        ALERT_THRESHOLDS=ALERT_THRESHOLDS,
        timestamps=timestamps,
        temperatures=temperatures,
        humidities=humidities,
        arduino=arduino
    )

@app.route('/data')
def get_data():
    """Return the latest sensor data as JSON"""
    read_arduino_data()  # Update readings
    return jsonify(latest_data)

@app.route('/weather')
def get_weather():
    """Return the latest weather data as JSON"""
    update_weather()  # Update weather data
    return jsonify(weather_data)

@app.route('/export_csv')
def export_csv():
    """Export sensor data as CSV"""
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM readings ORDER BY timestamp DESC')
    data = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Temperature (°F)', 'Humidity (%)'])
    writer.writerows(data)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'sensor_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

if __name__ == '__main__':
    print("Starting Temperature & Humidity Monitor...")
    # Get the computer's IP address to display it
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 8080
    print(f"Server is accessible at: http://{local_ip}:{port}")
    print("Press Ctrl+C to stop the server")
<<<<<<< HEAD
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
=======
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
>>>>>>> origin/main

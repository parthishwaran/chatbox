from flask import Flask, render_template, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# Load CSV - using the exact column names from your file
data = pd.read_csv('engine_data.csv')

# Define responses
condition_responses = {
    1: {"problem": "Normal", "cause": "No issues detected.", "manual": "Section 1.1 - General Operation"},
    0: {"problem": "Potential Issue", "cause": "Possible low pressure or temperature anomaly.", "manual": "Section 2.1 - Diagnostics"},
    "Overheating": {"problem": "Overheating", "cause": "Low coolant, radiator blockage, or thermostat failure.", "manual": "Section 3.2 - Cooling System"},
    "Low Oil Pressure": {"problem": "Low Oil Pressure", "cause": "Oil pump failure, low oil level, or worn bearings.", "manual": "Section 5.1 - Lubrication System"},
    "Low Fuel Pressure": {"problem": "Low Fuel Pressure", "cause": "Clogged fuel filter, failing fuel pump, or fuel line leak.", "manual": "Section 4.1 - Fuel System"}
}

def diagnose_problem(rpm, oil_press, fuel_press, cool_press, oil_temp, cool_temp):
    if cool_temp > 90:
        return "Overheating"
    elif oil_press < 2.5:
        return "Low Oil Pressure"
    elif fuel_press < 10:
        return "Low Fuel Pressure"
    else:
        return 1

def parse_input(text):
    # Initialize with defaults
    params = {
        'rpm': None,
        'cool_temp': None,
        'oil_press': 3.0,
        'fuel_press': 15.0,
        'cool_press': 2.0,
        'oil_temp': 80.0
    }

    # Extract all numbers
    numbers = re.findall(r'\d+\.?\d*', text)
    
    # Simple assignment based on position
    if len(numbers) >= 1:
        params['rpm'] = float(numbers[0])
    if len(numbers) >= 2:
        params['cool_temp'] = float(numbers[1])
    
    return params

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['message'].strip()
        params = parse_input(user_message)
        
        if params['rpm'] is None:
            return jsonify({'response': "Please include the RPM value (e.g., '700 81')."})
        if params['cool_temp'] is None:
            return jsonify({'response': "Please include the coolant temperature (e.g., '700 81')."})
        
        # Match with CSV using your exact column names
        row = data[
            (data['Engine rpm'].round() == round(params['rpm'])) &
            (data['Coolant temp'].between(params['cool_temp'] - 2, params['cool_temp'] + 2))
        ]
        
        if not row.empty:
            condition = row['Engine Condition'].iloc[0]
        else:
            condition = diagnose_problem(
                params['rpm'], params['oil_press'], params['fuel_press'],
                params['cool_press'], params['oil_temp'], params['cool_temp']
            )
        
        response = condition_responses.get(condition, condition_responses[0])
        reply = f"Condition: {response['problem']}<br>Possible Causes: {response['cause']}<br>Refer to: {response['manual']}"
        return jsonify({'response': reply})
    
    except Exception as e:
        return jsonify({'response': "Please provide two numbers like: '700 81' (RPM and Coolant Temp)"})

if __name__ == '__main__':
    app.run(debug=True)
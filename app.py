from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# Load dataset
df = pd.read_csv('data/diet_plans.csv')

# BMI calculation function
def calculate_bmi(weight, height):
    height_in_m = height / 100
    bmi = weight / (height_in_m ** 2)
    return round(bmi, 1)

# BMI category function
def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal weight"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"

# Diet recommendation function
# Diet recommendation function - Updated version
def recommend_diet(region, bmi_category, dietary_preference, health_condition):
    # First try to find exact matches
    filtered = df[
        (df['region'] == region) & 
        (df['bmi_category'] == bmi_category) &
        (df['dietary_preference'].str.contains(dietary_preference, case=False)) &
        (df['health_condition'].str.contains(health_condition, case=False))
    ]
    
    # If not enough exact matches, relax the health condition requirement
    if len(filtered) < 7:
        filtered = df[
            (df['region'] == region) & 
            (df['bmi_category'] == bmi_category) &
            (df['dietary_preference'].str.contains(dietary_preference, case=False))
        ]
    
    # If still not enough, just match region and BMI category
    if len(filtered) < 7:
        filtered = df[
            (df['region'] == region) & 
            (df['bmi_category'] == bmi_category)
        ]
    
    # If still not enough, just match BMI category
    if len(filtered) < 7:
        filtered = df[df['bmi_category'] == bmi_category]
    
    # Ensure we return exactly 7 days by duplicating if necessary
    if len(filtered) >= 7:
        return filtered.sample(7)
    else:
        # Duplicate the available rows to make 7 days
        needed = 7 - len(filtered)
        duplicated = filtered.sample(needed, replace=True)
        return pd.concat([filtered, duplicated])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        age = int(request.form.get('age'))
        gender = request.form.get('gender')
        weight = float(request.form.get('weight'))
        height = float(request.form.get('height'))
        region = request.form.get('region')
        dietary_preference = request.form.get('dietary_preference')
        health_condition = request.form.get('health_condition', 'none')
        activity_level = request.form.get('activity_level')
        
        # Calculate BMI
        bmi = calculate_bmi(weight, height)
        bmi_category = get_bmi_category(bmi)
        
        # Get recommendations
        recommendations = recommend_diet(region, bmi_category, dietary_preference, health_condition)
        
        if recommendations.empty:
            return render_template('result.html', 
                                 name=name,
                                 bmi=bmi,
                                 bmi_category=bmi_category,
                                 no_recommendations=True)
        
        # Convert recommendations to a list of dictionaries
        diet_plan = []
        for day, row in enumerate(recommendations.to_dict('records'), 1):
            diet_plan.append({
                'day': f'Day {day}',
                'breakfast': row['breakfast'],
                'mid_morning_snack': row['mid_morning_snack'],
                'lunch': row['lunch'],
                'evening_snack': row['evening_snack'],
                'dinner': row['dinner'],
                'calories': row['calories'],
                'notes': row['notes']
            })
        
        return render_template('result.html', 
                             name=name,
                             age=age,
                             gender=gender,
                             weight=weight,
                             height=height,
                             bmi=bmi,
                             bmi_category=bmi_category,
                             region=region,
                             dietary_preference=dietary_preference,
                             health_condition=health_condition,
                             activity_level=activity_level,
                             diet_plan=diet_plan)
    
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
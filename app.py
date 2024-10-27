from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('nutritional_info.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    campuses = conn.execute("SELECT DISTINCT Campus FROM nutritional_info").fetchall()
    conn.close()
    return render_template('index.html', campuses=campuses)

@app.route('/get_days', methods=['POST'])
def get_days():
    campus = request.form['campus']
    conn = get_db_connection()
    days = conn.execute("SELECT DISTINCT Day FROM nutritional_info WHERE Campus = ?", (campus,)).fetchall()
    conn.close()
    return jsonify([day['Day'] for day in days])


@app.route('/get_meals', methods=['POST'])
def get_meals():
    campus = request.form['campus']
    day = request.form['day']
    conn = get_db_connection()
    meals = conn.execute("SELECT DISTINCT Meal FROM nutritional_info WHERE Campus = ? AND Day = ?", (campus, day)).fetchall()
    conn.close()
    return jsonify([meal['Meal'] for meal in meals])


@app.route('/get_food_items', methods=['POST'])
def get_food_items():
    campus = request.form['campus']
    day = request.form['day']
    meal = request.form['meal']
    conn = get_db_connection()
    foods = conn.execute("SELECT DISTINCT FoodName FROM nutritional_info WHERE Campus = ? AND Day = ? AND Meal = ?", (campus, day, meal)).fetchall()
    conn.close()
    return jsonify([food['FoodName'] for food in foods])

#calorie ring
def get_calories():
    food_name = request.form['food_name']
    conn = get_db_connection()
    calorie_data = conn.execute("SELECT Calories FROM nutritional_info WHERE FoodName = ?", (food_name,)).fetchone()
    conn.close()
    
    if calorie_data:
        return jsonify({"calories": calorie_data['Calories']})
    else:
        return jsonify({"calories": 0})

@app.route('/get_nutrition', methods=['POST'])
def get_nutrition():
    campus = request.form['campus']
    day = request.form['day']
    meal = request.form['meal']
    food_name = request.form['food_name']
    conn = get_db_connection()
    nutrition = conn.execute('''SELECT * FROM nutritional_info 
                                WHERE Campus = ? AND Day = ? AND Meal = ? AND FoodName = ?''', 
                                (campus, day, meal, food_name)).fetchone()
    conn.close()
    return jsonify(dict(nutrition)) if nutrition else jsonify({})

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/')
def index():
    conn = get_db_connection()
    campuses = conn.execute("SELECT DISTINCT Campus FROM nutritional_info").fetchall()
    conn.close()
    return render_template('index.html', campuses=campuses)

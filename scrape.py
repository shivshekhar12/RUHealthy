from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import sqlite3
import re

def scraping():
    # Make the database if it doesn't exist
    con = sqlite3.connect('nutritional_info.db')
    cur = con.cursor()
    # Add Calories column to the table if it doesn't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS nutritional_info (
                Campus TEXT,
                Day TEXT,
                Meal TEXT,
                FoodName TEXT,
                ServingSizeNumber REAL,
                ServingSizeUnit TEXT,
                Calories REAL,
                TotalFat REAL,
                TotalCarbs REAL,
                SaturatedFat REAL,
                DietaryFiber REAL,
                TransFat REAL,
                Sugars REAL,
                Cholesterol REAL,
                Protein REAL,
                Sodium REAL)''')

    service = Service(executable_path='chromedriver')
    driver = webdriver.Chrome()
    action = ActionChains(driver)

    dining_halls = {
        'Busch': 'https://menuportal23.dining.rutgers.edu/foodpronet/pickmenu.aspx?sName=Rutgers+University+Dining&locationNum=04&locationName=Busch+Dining+Hall&naFlag=1',
        'Livingston': 'https://menuportal23.dining.rutgers.edu/foodpronet/pickmenu.aspx?sName=Rutgers+University+Dining&locationNum=03&locationName=Livingston+Dining+Commons&naFlag=1',
        'College Ave': 'https://menuportal23.dining.rutgers.edu/FoodPronet/pickmenu.aspx?sName=Rutgers+University+Dining&locationNum=13&locationName=The+Atrium&naFlag=1',
        'Cook/Douglass': 'https://menuportal23.dining.rutgers.edu/FoodPronet/pickmenu.aspx?sName=Rutgers+University+Dining&locationNum=05&locationName=Neilson+Dining+Hall&naFlag=1'
    }

    for hall in dining_halls:
        url = dining_halls[hall]
        driver.get(url)

        num_days = len(driver.find_elements(By.TAG_NAME, 'option'))
        for day_options in range(0, num_days):
            day = driver.find_elements(By.TAG_NAME, 'option')
            day_text = day[day_options].text
            day[day_options].click()
            Campus = hall
            Day = day_text
            for meal in range(1, 4):
                try:
                    meal_element = driver.find_element(By.XPATH, f'//*[@id="content-text"]/div[2]/div[{meal}]')
                    meal_name = meal_element.text
                    print(f"Scraping meal: {meal_name}")

                    meal_element.click()

                    num_fieldset = len(driver.find_elements(By.TAG_NAME, 'fieldset'))

                    for num in range(1, num_fieldset + 1):
                        try:
                            driver.find_element(By.XPATH, f'/html/body/div[5]/div/div[1]/div[2]/form/div[1]/fieldset[{num}]/div[3]/a').click()

                            try:
                                food_name = driver.find_element(By.XPATH, '/html/body/div[5]/div[1]/h2[2]').text.strip()

                                serving_size_text = driver.find_element(By.XPATH, '//*[@id="facts"]/p[1]').text
                                serving_size_match = re.search(r"Serving Size (\d+)\s(\w+)", serving_size_text)
                                if serving_size_match:
                                    serving_size_number = int(serving_size_match.group(1))
                                    serving_size_unit = serving_size_match.group(2)
                                else:
                                    serving_size_number = 0
                                    serving_size_unit = None


                                calories_text = driver.find_element(By.XPATH, '//*[@id="facts"]/p[2]').text
                                calories_match = re.search(r"Calories\s(\d+)", calories_text)
                                calories = float(calories_match.group(1)) if calories_match else None

                                matches = driver.find_elements(By.TAG_NAME, 'td')
                                nutrition_list = [match.text.strip() for match in matches if '%' not in match.text and match.text.strip()]
                                nutrition_list = [item.replace('- - -', '0') for item in nutrition_list if item]
                                parsed_data = parse_nutrition_data(nutrition_list)

                                cur.execute('''INSERT INTO nutritional_info 
                                            (Campus, Day, Meal, FoodName, ServingSizeNumber, ServingSizeUnit, Calories, TotalFat, TotalCarbs, SaturatedFat, DietaryFiber, TransFat, Sugars, Cholesterol, Protein, Sodium)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                            (Campus, Day, meal_name, food_name, serving_size_number, serving_size_unit, calories,
                                             parsed_data.get('Total Fat', None),
                                             parsed_data.get('Tot. Carb.', None),
                                             parsed_data.get('Sat. Fat', None), 
                                             parsed_data.get('Dietary Fiber', None),
                                             parsed_data.get('Trans Fat', None),
                                             parsed_data.get('Sugars', None),
                                             parsed_data.get('Cholesterol', None),
                                             parsed_data.get('Protein', None),
                                             parsed_data.get('Sodium', None)))

                                con.commit()
                                print(f"{Campus} - {meal_name} - {Day} - {food_name}: {parsed_data} - Calories: {calories} - Serving Size: {serving_size_number} {serving_size_unit}")

                            except NoSuchElementException:
                                print("Nutritional information not found for this item.")
                            
                            driver.back()

                        except NoSuchElementException:
                            print(f"Food item {num} not found in meal {meal_name}")

                except NoSuchElementException:
                    print(f"No meal found for meal index {meal}")

    driver.quit()
    con.close()

def parse_nutrition_data(nutrition_list):
    nutrition_dict = {}
    for item in nutrition_list:
        match = re.match(r'(.+?)\s([\d.]+)\s?(mg|g)?', item)

        if match:
            nutrient_name = match.group(1).strip()
            value = float(match.group(2))
            unit = match.group(3)

            if unit == 'mg':
                value = round(value / 1000, 2)
            
            nutrition_dict[nutrient_name] = value
    return nutrition_dict

if __name__ == "__main__":
    scraping()

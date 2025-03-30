from flask import Flask, render_template, jsonify, request,redirect,url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time, os, folium
from PIL import Image

app = Flask(__name__)

# Dummy user credentials (Replace with database validation)
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == VALID_USERNAME and password == VALID_PASSWORD:
            return redirect(url_for("home")) 
        else:
            return render_template("login.html", error="Invalid Username or Password")

    return render_template("login.html")
@app.route("/signup")
def signup():
    return render_template("signup.html")  

@app.route('/run_selenium', methods=['GET'])
def run_selenium():
    lat = request.args.get('lat')
    lng = request.args.get('lng')

    if not lat or not lng:
        return jsonify({"error": "Latitude and Longitude required"}), 400

    # Call your Selenium script here (Example: Print received values)
    result = f"Running Selenium with Latitude: {lat}, Longitude: {lng}"

    m = folium.Map(location=[lat, lng], zoom_start=100)

    # Save the map
    m.save("centered_map.html")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")

    # Start WebDriver
    # service = Service(executable_path=r"C:/Users/heva/Documents/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(executable_path=r"C:/Users/heva/Documents/chromedriver-win64/chromedriver.exe")

    # Load HTML file
    file_path = os.path.abspath("centered_map.html")  # Ensure the path is absolute
    driver.get(f"file://{file_path}")

    # Capture screenshot
    driver.save_screenshot("static/images/output.png")
    time.sleep(10)
    # Close driver
    driver.quit()

    return jsonify({"message": result})

if __name__ == "__main__":
    app.run(debug=True)




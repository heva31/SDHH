from flask import Flask, render_template, jsonify, request,session, redirect,url_for
from flask_dance.contrib.google import make_google_blueprint, google
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time, os, folium
from dotenv import load_dotenv
from PIL import Image
import requests

import cv2, math
import numpy as np
import matplotlib.pyplot as plt

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
# Dummy user credentials (Replace with database validation)
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"
# Google OAuth Blueprint
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
    ],
    redirect_url="/google_login/authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

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

@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    user_info = resp.json()
    print(user_info)
    session["user"] = user_info
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

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
    options.add_argument("--headless")

    # Start WebDriver
    # service = Service(executable_path=r"C:/Users/heva/Documents/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(executable_path=r"C:/Users/heva/Documents/chromedriver-win64/chromedriver.exe")

    # Load HTML file
    file_path = os.path.abspath("centered_map.html")  # Ensure the path is absolute
    driver.get(f"file://{file_path}")

    # Capture screenshot
    driver.save_screenshot("static/images/output.png")
    
    
    # Close driver
    driver.quit()
    processed_area = imageProcessing()
    avg= data_fetch(lat,lng,processed_area)
    return jsonify({"message": result,"avg":avg})

def imageProcessing():
      # Load edge detection model from the models folder
    model_path = os.path.join("model", "model.yml.gz")
    edge_detector = cv2.ximgproc.createStructuredEdgeDetection(model_path)

    # Load the image from the static/images folder
    image_path = os.path.join("static", "images", "output.png")
    image = cv2.imread(image_path)
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Run the structured edge detection algorithm
    edges = edge_detector.detectEdges(image_rgb.astype(np.float32) / 240.0)

    # Convert edges to binary
    edges_binary = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)  # Convert to 3 channels
    edges_binary = cv2.cvtColor(edges_binary, cv2.COLOR_BGR2GRAY)  # Convert back to grayscale
    _, edges_binary = cv2.threshold(edges_binary, 0.1, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, hierarchy = cv2.findContours(edges_binary.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_areas = [(cv2.contourArea(c), c) for c in contours]
    largest_contour = max(contour_areas, key=lambda x: x[0])[1]
    angle_degrees = 22.990099100827187
    # Calculate the area of the largest contour
    area = cv2.contourArea(largest_contour)
    angle_radians = math.radians(angle_degrees)
    cosine_value = math.cos(angle_radians)
    scale=156543.03*cosine_value/2**20
    meter_area=scale*area
    print("Area of the object:", meter_area)

    highlighted_image = image.copy()
    cv2.drawContours(highlighted_image, [largest_contour], -1, (0, 255, 0), 2)
    # print(highlighted_image)
    # plt.imshow(cv2.cvtColor(highlighted_image, cv2.COLOR_BGR2RGB))
    plt.title('Highlighted Object')
    plt.axis('off')
    # plt.show()
    # Display the detected edges and contours
    # plt.imshow(edges_binary, cmap='gray')
    plt.title('Structured Edge Detection and Contours')
    plt.axis('off')
    # plt.show()
    return meter_area


def data_fetch(lat,lon,meter_area):

    # Solar Energy Calculation
    
    start_date, end_date = "20250301", "20250323"  # March 2025
    
    # Rooftop Details
    rooftop_area=meter_area
    panel_efficiency = 0.20  # 20% efficiency
    
    # Fetch NASA solar radiation data
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&start={start_date}&end={end_date}&latitude={lat}&longitude={lon}&community=RE&format=JSON"
    response = requests.get(url)
    data = response.json()
    
    # Extract daily solar radiation (kWh/m²/day)
    solar_radiation = data['properties']['parameter']['ALLSKY_SFC_SW_DWN']
    
    # Calculate energy output for each day (Watts)
    energy_output = {date: S * rooftop_area * panel_efficiency * 1000 for date, S in solar_radiation.items()}
    
    # Plot energy generation graph
    dates = list(energy_output.keys())
    values = list(energy_output.values())
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='o', linestyle='-', color='b')
    plt.xticks(rotation=45)
    plt.xlabel('Date')
    plt.ylabel('Energy Output (W)')
    plt.title('Daily Energy Generation for March 2025')
    plt.grid()
    # plt.show()
    
    # Calculate the average monthly energy output
    average_energy = sum(energy_output.values()) / len(energy_output)
    
    # Print results
    print(f"Total Energy for March: {sum(energy_output.values()):.2f} W")
    print(f"Average Daily Energy Output for March: {average_energy:.2f} W")
    return average_energy
if __name__ == "__main__":
    app.run(debug=True)




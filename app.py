from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    user = request.json.get('user')
    password = request.json.get('pass')

    if not user or not password:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_usr").send_keys(user)
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass").send_keys(password)
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_aceptar").click()

        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/datos_personales.aspx")
        name = driver.find_element(By.ID, "lb_nom").text
        driver.quit()

        return jsonify({"status": "ok", "nombre": name})
    except Exception as e:
        return jsonify({"status": "fail", "error": str(e)}), 500

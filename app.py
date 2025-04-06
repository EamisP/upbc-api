from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    user = request.json.get("user")
    password = request.json.get("pass")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_usr").send_keys(user)
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass").send_keys(password)
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_aceptar").click()

        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/datos_personales.aspx")
        name = driver.find_element(By.ID, "lb_nom").text
        driver.quit()

        return jsonify({"status": "ok", "nombre": name})
    except Exception as e:
        return jsonify({"status": "fail", "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

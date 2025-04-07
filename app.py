from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    # Recibir datos en formato JSON
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Configurar Chrome en modo headless con un directorio único de usuario
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    
    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Abrir la página de la escuela
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        wait = WebDriverWait(driver, 3)
        
        # Completar el formulario de login
        username_field = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr")))
        password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass")
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Hacer clic en el botón de acceso
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar")))
        submit_button.click()
        
        # Esperar a que se muestre el elemento con el name y dar tiempo adicional para que carguen todos los datos
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_lb_lnom")))
        time.sleep(3)
        
        # Extraer los datos:
        personal = {
            "name": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lnom").text,
            "career": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lprog").text
        }
        
        address = {
            "dir": driver.find_element(By.ID, "ContentPlaceHolder1_lb_ldir").text,
            "col": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lcol").text,
            "mun": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lmun").text,
            "edo": driver.find_element(By.ID, "ContentPlaceHolder1_lb_ledo").text,
            "cp": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lcp").text
        }
        
        tutor = {
            "name": driver.find_element(By.ID, "ContentPlaceHolder1_lb_tutor").text,
            "mail": driver.find_element(By.ID, "ContentPlaceHolder1_lbmemail").text
        }
        
        institution = {
            "mail": driver.find_element(By.ID, "ContentPlaceHolder1_lb_inst_email").text,
            "password": driver.find_element(By.ID, "ContentPlaceHolder1_lb_inst_clave").text
        }
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()
    
    # Armar la respuesta completa con todos los datos agrupados
    result = {
        "personal": personal,
        "address": address,
        "tutor": tutor,
        "institution": institution
    }
    
    return jsonify(result)

if __name__ == '__main__':
    # Render espera que la aplicación escuche en el puerto 8080
    app.run(host='0.0.0.0', port=8080)

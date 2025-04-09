from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import tempfile
import shutil

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    # Recibir datos en formato JSON
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Crear un directorio temporal único para el perfil de Chrome
    temp_dir = tempfile.mkdtemp()
    
    # Configurar Chrome en modo headless con el directorio temporal
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={temp_dir}")
    
    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Abrir la página de la escuela
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        wait = WebDriverWait(driver, 5)  # Aumentamos el tiempo de espera en caso de que la página tarde
        
        # Completar el formulario de login
        username_field = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr")))
        password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass")
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Hacer clic en el botón de acceso
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar")))
        submit_button.click()
        
        # Esperar a que se muestre el elemento con el nombre y dar tiempo adicional para cargar datos
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_lb_lnom")))
        time.sleep(1)
        
        # Extraer los datos personales, dirección, tutor e institución
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
        
        # Extraer los datos de la boleta (tabla) 
        # Se espera a que la tabla esté presente en el DOM
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gv_hrsxsem")))
        tabla = driver.find_element(By.ID, "ContentPlaceHolder1_gv_hrsxsem")
        filas = tabla.find_elements(By.TAG_NAME, "tr")
        
        boleta = []
        # Se asume que la primera fila es el encabezado
        for fila in filas[1:]:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) >= 3:
                boleta.append({
                    "materia": celdas[0].text.strip(),
                    "calificacion": celdas[1].text.strip(),
                    "cuatrimestre": celdas[2].text.strip()
                })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()
        # Eliminar el directorio temporal creado
        shutil.rmtree(temp_dir)
    
    # Armar la respuesta completa con todos los datos extraídos
    result = {
        "personal": personal,
        "address": address,
        "tutor": tutor,
        "institution": institution,
        "boleta": boleta
    }
    
    return jsonify(result)

if __name__ == '__main__':
    # Render espera que la aplicación escuche en el puerto 8080
    app.run(host='0.0.0.0', port=8080)

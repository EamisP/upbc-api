from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import tempfile
import shutil

app = Flask(__name__)

# Función para aceptar alertas si aparecen
def accept_alert_if_present(driver, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
        print("Alerta aceptada correctamente.")
    except TimeoutException:
        print("No se mostró ninguna alerta.")

# Función para verificar si existe un elemento
def element_exists(driver, by, value, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        return True
    except TimeoutException:
        return False

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    temp_dir = tempfile.mkdtemp()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={temp_dir}")

    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")

        username_field = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr")))
        password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass")
        username_field.send_keys(username)
        password_field.send_keys(password)

        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar")))
        submit_button.click()

        accept_alert_if_present(driver)
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/npe_alu_materias.aspx")
        accept_alert_if_present(driver)
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_lb_lnom")))

        # Datos básicos
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

        # Boleta
        boleta = []
        if element_exists(driver, By.ID, "ContentPlaceHolder1_gv_hrsxsem"):
            tabla = driver.find_element(By.ID, "ContentPlaceHolder1_gv_hrsxsem")
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            for fila in filas[1:]:
                celdas = fila.find_elements(By.TAG_NAME, "td")
                if len(celdas) >= 3:
                    boleta.append({
                        "materia": celdas[0].text.strip(),
                        "calificacion": celdas[1].text.strip(),
                        "cuatrimestre": celdas[2].text.strip()
                    })

        # Materias
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/npe_alu_materias.aspx")
        accept_alert_if_present(driver)

        subjects_data = []
        if element_exists(driver, By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']"):
            subject_links = driver.find_elements(By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")
            for i, subject_link in enumerate(subject_links):
                subject_name = subject_link.text.strip()
                subject_link.click()
                time.sleep(1)

                final_grade_elem = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_lb_califfinal_{i}")
                final_grade = final_grade_elem.text.strip()

                subjects_data.append({
                    "materia": subject_name,
                    "calificacion_final": final_grade,
                    "unidades": []
                })

        # Horario
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/alu_horario.aspx")
        horario = []
        if element_exists(driver, By.ID, "ContentPlaceHolder1_gv_hrsxsem"):
            horario_tabla = driver.find_element(By.ID, "ContentPlaceHolder1_gv_hrsxsem")
            rows = horario_tabla.find_elements(By.TAG_NAME, "tr")
            for idx, row in enumerate(rows[1:]):
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 9:
                    horario.append({
                        "materia": cells[1].text.strip().split("\n")[0],
                        "grupo": cells[2].text.strip(),
                        "L": cells[3].text.strip(),
                        "M": cells[4].text.strip(),
                        "M1": cells[5].text.strip(),
                        "J": cells[6].text.strip(),
                        "V": cells[7].text.strip(),
                        "S": cells[8].text.strip()
                    })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()
        shutil.rmtree(temp_dir)

    return jsonify({
        "personal": personal,
        "address": address,
        "tutor": tutor,
        "institution": institution,
        "boleta": boleta,
        "materias": subjects_data,
        "horario": horario
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

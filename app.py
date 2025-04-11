from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import tempfile
import shutil

app = Flask(__name__)

def safe_text(driver, by, locator, default="Sin información", timeout=5):
    """Intenta obtener el texto de un elemento; si no está o hay timeout, devuelve default."""
    try:
        elem = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        text = elem.text.strip()
        return text if text else default
    except (TimeoutException, NoSuchElementException):
        return default

def safe_find_elements(driver, by, locator, timeout=5):
    """Intenta obtener una lista de elementos; si falla, devuelve lista vacía."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        return driver.find_elements(by, locator)
    except Exception:
        return []

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

    try:
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        wait = WebDriverWait(driver, 5)
        # Login
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr"))).send_keys(username)
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass").send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar"))).click()
        time.sleep(1)

        # Datos básicos con safe_text
        personal = {
            "name": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_lnom"),
            "career": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_lprog")
        }
        address = {
            "dir": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_ldir"),
            "col": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_lcol"),
            "mun": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_lmun"),
            "edo": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_ledo"),
            "cp":  safe_text(driver, By.ID, "ContentPlaceHolder1_lb_lcp")
        }
        tutor = {
            "name": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_tutor"),
            "mail": safe_text(driver, By.ID, "ContentPlaceHolder1_lbmemail")
        }
        institution = {
            "mail": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_inst_email"),
            "password": safe_text(driver, By.ID, "ContentPlaceHolder1_lb_inst_clave")
        }

        # Boleta
        boleta = []
        rows = safe_find_elements(driver, By.CSS_SELECTOR, "#ContentPlaceHolder1_gv_hrsxsem tr")
        for fila in rows[1:]:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            boleta.append({
                "materia": celdas[0].text.strip() if len(celdas) > 0 else "Sin información",
                "calificacion": celdas[1].text.strip() if len(celdas) > 1 else "Sin información",
                "cuatrimestre": celdas[2].text.strip() if len(celdas) > 2 else "Sin información"
            })

        # Materias y unidades
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/npe_alu_materias.aspx")
        time.sleep(2)
        subjects_data = []
        links = safe_find_elements(driver, By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")
        for i, link in enumerate(links):
            materia = link.text.strip() or "Sin información"
            try:
                link.click()
                time.sleep(1)
                cal_final = safe_text(driver, By.ID, f"ContentPlaceHolder1_gv1_lb_califfinal_{i}")
                # Unidades
                unidades = []
                rows_u = safe_find_elements(driver, By.CSS_SELECTOR, f"#ContentPlaceHolder1_gv1_dv_gv1x_{i} tr")[1:]
                for row_u in rows_u:
                    cols = row_u.find_elements(By.TAG_NAME, "td")
                    unidades.append({
                        "unidad": cols[0].text.strip() if len(cols)>0 else "Sin información",
                        "descripcion": cols[1].text.strip() if len(cols)>1 else "Sin información",
                        "calificacion": cols[2].text.strip() if len(cols)>2 else "Sin información",
                    })
            except Exception:
                cal_final = "Sin información"
                unidades = []
            subjects_data.append({
                "materia": materia,
                "calificacion_final": cal_final,
                "unidades": unidades
            })

        # ... (idéntica lógica para calificaciones especiales y horario,
        #    usando safe_text y safe_find_elements donde haga falta,
        #    y devolviendo "Sin información" como default)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()
        shutil.rmtree(temp_dir)

    result = {
        "personal": personal,
        "address": address,
        "tutor": tutor,
        "institution": institution,
        "boleta": boleta,
        "materias": subjects_data,
        # "horario": horario,  etc.
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

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

def accept_alert_if_present(driver, timeout=5):
    """Si aparece una alerta, la acepta; si no, continúa."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
        print("Alerta aceptada correctamente.")
    except TimeoutException:
        # No se presentó alerta
        pass

def safe_text(driver, by, locator, default="Sin información", timeout=5):
    """Retorna el texto de un elemento o default si no se encuentra."""
    try:
        elem = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        text = elem.text.strip()
        return text if text else default
    except (TimeoutException, NoSuchElementException):
        return default

def safe_find_elements(driver, by, locator, timeout=5):
    """Retorna una lista de elementos o una lista vacía en caso de error."""
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
    
    # Directorio temporal para el perfil de Chrome
    temp_dir = tempfile.mkdtemp()
    
    # Configurar Chrome en modo headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={temp_dir}")
    
    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 1. Login inicial
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr"))).send_keys(username)
        driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass").send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar"))).click()
        accept_alert_if_present(driver)  # Aceptar alerta post login

        # 2. Redireccionar a datos personales
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/datos_personales.aspx")
        accept_alert_if_present(driver)  # Aceptar alerta de redirect
        time.sleep(1)
        
        # Datos básicos
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
        
        # 3. Extraer la boleta (tabla)
        boleta = []
        rows = safe_find_elements(driver, By.CSS_SELECTOR, "#ContentPlaceHolder1_gv_hrsxsem tr")
        for fila in rows[1:]:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            boleta.append({
                "materia": celdas[0].text.strip() if len(celdas) > 0 else "Sin información",
                "calificacion": celdas[1].text.strip() if len(celdas) > 1 else "Sin información",
                "cuatrimestre": celdas[2].text.strip() if len(celdas) > 2 else "Sin información"
            })
        
        # 4. Extraer información de materias y sus unidades
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/npe_alu_materias.aspx")
        accept_alert_if_present(driver)  # Aceptar alerta de redirect
        time.sleep(1)
        subjects_data = []
        subject_links = safe_find_elements(driver, By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")
        num_subjects = len(subject_links)
        
        for i in range(num_subjects):
            try:
                subject_link = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_lk_mat_desc_{i}")
                subject_name = subject_link.text.strip() or "Sin información"
                
                subject_link.click()
                time.sleep(2)
                
                final_grade = safe_text(driver, By.ID, f"ContentPlaceHolder1_gv1_lb_califfinal_{i}")
                
                # Extraer las unidades si existen
                unidades = []
                try:
                    detail_div = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_dv_gv1x_{i}")
                    table = detail_div.find_element(By.CSS_SELECTOR, "table[id^='ContentPlaceHolder1_gv1_gv1x_']")
                    rows_unidades = table.find_elements(By.XPATH, ".//tr[position()>1]")
                    for row in rows_unidades:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        unidades.append({
                            "unidad": cells[0].text.strip() if len(cells) > 0 else "Sin información",
                            "descripcion": cells[1].text.strip() if len(cells) > 1 else "Sin información",
                            "calificacion": cells[2].text.strip() if len(cells) > 2 else "Sin información"
                        })
                except Exception:
                    unidades = []
                
                subjects_data.append({
                    "materia": subject_name,
                    "calificacion_final": final_grade,
                    "unidades": unidades
                })
            except Exception:
                continue
        
        # 5. Procesar calificaciones especiales (rpt_calificaciones.aspx)
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/rpt_calificaciones.aspx")
        wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$dd_corte")))
        time.sleep(2)
        
        special_grades = []
        for corte in ["1", "2", "3"]:
            select_elem = Select(wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$dd_corte"))))
            select_elem.select_by_value(corte)
            time.sleep(2)
            try:
                tr_nivel = wait.until(EC.presence_of_element_located((
                    By.XPATH, "//tr[td[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'NIVEL')]]"
                )))
                tds = tr_nivel.find_elements(By.TAG_NAME, "td")
                if tds:
                    grade_text = tds[-1].text.strip()
                    try:
                        grade_val = float(grade_text) if grade_text != "" else 0.0
                    except Exception:
                        grade_val = 0.0
                    special_grades.append(grade_val)
                else:
                    special_grades.append(0.0)
            except Exception:
                special_grades.append(0.0)
        
        if len(special_grades) == 3 and all(g > 0 for g in special_grades):
            special_final = round(sum(special_grades) / 3, 2)
            special_final_str = str(special_final)
        else:
            special_final_str = "N/A"
        
        special_subject = {
            "materia": "INGLÉS",
            "calificacion_final": special_final_str,
            "unidades": [
                {"unidad": "1", "descripcion": "Calificación corte 1", "calificacion": str(special_grades[0]) if len(special_grades) > 0 else "N/A"},
                {"unidad": "2", "descripcion": "Calificación corte 2", "calificacion": str(special_grades[1]) if len(special_grades) > 1 else "N/A"},
                {"unidad": "3", "descripcion": "Calificación corte 3", "calificacion": str(special_grades[2]) if len(special_grades) > 2 else "N/A"}
            ]
        }
        subjects_data.append(special_subject)
        
        # 6. Obtener el horario (alu_horario.aspx)
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/alu_horario.aspx")
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gv_hrsxsem")))
        time.sleep(2)
        
        horario = []
        horario_tabla = driver.find_element(By.ID, "ContentPlaceHolder1_gv_hrsxsem")
        rows = horario_tabla.find_elements(By.TAG_NAME, "tr")
        # Se asume que la primera fila es el encabezado
        for idx, row in enumerate(rows[1:]):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 9:
                try:
                    materia_elem = cells[1].find_element(By.ID, f"ContentPlaceHolder1_gv_hrsxsem_lb_materia_{idx}")
                    materia_text = materia_elem.text.strip()
                except Exception:
                    materia_text = cells[1].text.split("\n")[0].strip() or "Sin información"
                try:
                    maestro_elem = cells[1].find_element(By.ID, f"ContentPlaceHolder1_gv_hrsxsem_lb_maestro_{idx}")
                    maestro_text = maestro_elem.text.strip()
                except Exception:
                    parts = cells[1].text.split("\n")
                    maestro_text = parts[1].strip() if len(parts) > 1 else "Sin información"
                
                grupo = cells[2].text.strip() if cells[2].text.strip() else "Sin información"
                def clean(cell):
                    t = cell.text.strip()
                    return t if t != "\xa0" and t != "" else "Sin información"
                
                lunes = clean(cells[3])
                martes = clean(cells[4])
                m1 = clean(cells[5])
                jueves = clean(cells[6])
                viernes = clean(cells[7])
                sabado = clean(cells[8])
                
                horario.append({
                    "materia": materia_text,
                    "maestro": maestro_text,
                    "grupo": grupo,
                    "L": lunes,
                    "M": martes,
                    "M1": m1,
                    "J": jueves,
                    "V": viernes,
                    "S": sabado
                })
        
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
        "horario": horario
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

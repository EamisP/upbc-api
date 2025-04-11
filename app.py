from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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
    
    # Crear un directorio temporal para el perfil de Chrome
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
        # 1. Iniciar sesión en la página principal
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
        wait = WebDriverWait(driver, 3)
        
        username_field = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr")))
        password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass")
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar")))
        submit_button.click()
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("Alerta aceptada correctamente.")
        except TimeoutException:
            print("No se mostró ninguna alerta.")
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/npe_alu_materias.aspx")
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("Alerta aceptada correctamente.")
        except TimeoutException:
            print("No se mostró ninguna alerta.")
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_lb_lnom")))
        time.sleep(1)
        
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
        
        # Extraer la boleta (tabla existente)
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gv_hrsxsem")))
        tabla = driver.find_element(By.ID, "ContentPlaceHolder1_gv_hrsxsem")
        filas = tabla.find_elements(By.TAG_NAME, "tr")
        boleta = []
        for fila in filas[1:]:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) >= 3:
                boleta.append({
                    "materia": celdas[0].text.strip(),
                    "calificacion": celdas[1].text.strip(),
                    "cuatrimestre": celdas[2].text.strip()
                })
        
        # 2. Navegar a la página de materias y extraer la información adicional
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/npe_alu_materias.aspx")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")))
        time.sleep(2)
        
        subjects_data = []
        subject_links = driver.find_elements(By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")
        num_subjects = len(subject_links)
        
        for i in range(num_subjects):
            try:
                subject_link = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_lk_mat_desc_{i}")
                subject_name = subject_link.text.strip()
                
                subject_link.click()
                time.sleep(2)
                
                final_grade_elem = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_lb_califfinal_{i}")
                final_grade = final_grade_elem.text.strip()
                
                unidades = []
                try:
                    detail_div = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_dv_gv1x_{i}")
                    table = detail_div.find_element(By.CSS_SELECTOR, "table[id^='ContentPlaceHolder1_gv1_gv1x_']")
                    rows = table.find_elements(By.XPATH, ".//tr[position()>1]")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            unidad_num = cells[0].text.strip()
                            descripcion = cells[1].text.strip()
                            calificacion_unidad = cells[2].text.strip()
                            unidades.append({
                                "unidad": unidad_num,
                                "descripcion": descripcion,
                                "calificacion": calificacion_unidad
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
        
        # 3. Procesar calificaciones especiales desde rpt_calificaciones.aspx
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
        
        # 4. Obtener el horario de los alumnos desde alu_horario.aspx
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/alu_horario.aspx")
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gv_hrsxsem")))
        time.sleep(2)
        
        horario = []
        horario_tabla = driver.find_element(By.ID, "ContentPlaceHolder1_gv_hrsxsem")
        rows = horario_tabla.find_elements(By.TAG_NAME, "tr")
        # Suponemos que la primera fila es el encabezado
        for idx, row in enumerate(rows[1:]):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 9:
                # Obtener materia y maestro desde el segundo TD (índice 1)
                try:
                    materia_elem = cells[1].find_element(By.ID, f"ContentPlaceHolder1_gv_hrsxsem_lb_materia_{idx}")
                    materia_text = materia_elem.text.strip()
                except Exception:
                    materia_text = cells[1].text.split("\n")[0].strip()
                try:
                    maestro_elem = cells[1].find_element(By.ID, f"ContentPlaceHolder1_gv_hrsxsem_lb_maestro_{idx}")
                    maestro_text = maestro_elem.text.strip()
                except Exception:
                    # Si no se encuentra, se extrae de la parte siguiente del mismo TD
                    parts = cells[1].text.split("\n")
                    maestro_text = parts[1].strip() if len(parts) > 1 else ""
                
                grupo = cells[2].text.strip()
                # Para el horario, cada celda puede tener &nbsp;; se limpia con strip() y se comprueba
                def clean(cell):
                    t = cell.text.strip()
                    return t if t != "\xa0" and t != "" else ""
                
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
        "horario": horario  # Se agrega el horario extraído
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

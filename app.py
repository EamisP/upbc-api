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
        wait = WebDriverWait(driver, 10)
        
        # Completar el formulario de login
        username_field = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr")))
        password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass")
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Hacer clic en el botón de acceso y esperar a que la página se cargue
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar")))
        submit_button.click()
        wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_lb_lnom")))
        time.sleep(1)
        
        # Extraer datos básicos
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
        # Esperar a que aparezcan los enlaces de las materias
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")))
        time.sleep(2)
        
        subjects_data = []
        # Se obtienen todos los enlaces de materias (el número puede variar)
        subject_links = driver.find_elements(By.CSS_SELECTOR, "a[id^='ContentPlaceHolder1_gv1_lk_mat_desc_']")
        num_subjects = len(subject_links)
        
        for i in range(num_subjects):
            try:
                # Reubicar el enlace de la materia (para evitar referencias obsoletas)
                subject_link = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_lk_mat_desc_{i}")
                subject_name = subject_link.text.strip()
                
                # Hacer click en el enlace de la materia y esperar 2 segundos
                subject_link.click()
                time.sleep(2)
                
                # Extraer la calificación final de la materia
                final_grade_elem = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_lb_califfinal_{i}")
                final_grade = final_grade_elem.text.strip()
                
                # Inicializar lista para la información de las unidades
                unidades = []
                try:
                    # Buscar el contenedor del detalle de unidades (si existe)
                    detail_div = driver.find_element(By.ID, f"ContentPlaceHolder1_gv1_dv_gv1x_{i}")
                    # Dentro del contenedor, buscar la tabla de unidades
                    table = detail_div.find_element(By.CSS_SELECTOR, "table[id^='ContentPlaceHolder1_gv1_gv1x_']")
                    
                    # Obtener todas las filas excepto la de encabezado
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
                except Exception as ex:
                    # Si no se encuentra el detalle, se deja la lista vacía
                    unidades = []
                
                # Agregar los datos de la materia a la lista
                subjects_data.append({
                    "materia": subject_name,
                    "calificacion_final": final_grade,
                    "unidades": unidades
                })
            except Exception as e:
                continue  # Si hay error con alguna materia, continuar con la siguiente
        
        # 3. Procesar calificaciones especiales desde rpt_calificaciones.aspx para una materia (por ejemplo, inglés)
        # Esta sección interactúa con el select "ctl00$ContentPlaceHolder1$dd_corte" y obtiene las calificaciones de las 3 unidades
        driver.get("https://www2.upbc.edu.mx/alumnos/siaax/rpt_calificaciones.aspx")
        wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$dd_corte")))
        time.sleep(2)
        
        # Usando Selenium's Select para interactuar con el select
        select_elem = Select(driver.find_element(By.NAME, "ctl00$ContentPlaceHolder1$dd_corte"))
        special_grades = []
        
        for corte in ["1", "2", "3"]:
            select_elem.select_by_value(corte)
            # Esperar a que se actualice la tabla
            time.sleep(2)
            try:
                # Buscar el TR que contenga en alguno de sus TD la palabra "NIVEL"
                tr_nivel = driver.find_element(By.XPATH, "//tr[td[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'NIVEL')]]")
                tds = tr_nivel.find_elements(By.TAG_NAME, "td")
                if tds:
                    grade_text = tds[-1].text.strip()
                    try:
                        grade_val = float(grade_text) if grade_text != "" else 0.0
                    except:
                        grade_val = 0.0
                    special_grades.append(grade_val)
                else:
                    special_grades.append(0.0)
            except Exception as e:
                special_grades.append(0.0)
        
        # Calcular la calificación final especial:
        # Si se obtuvieron tres calificaciones y cada una es mayor que 0, se promedian; de lo contrario se retorna "N/A"
        if len(special_grades) == 3 and all(g > 0 for g in special_grades):
            special_final = round(sum(special_grades) / 3, 2)
            special_final_str = str(special_final)
        else:
            special_final_str = "N/A"
        
        # Crear el diccionario para la materia especial (por ejemplo, "INGLÉS")
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
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()
        shutil.rmtree(temp_dir)
    
    # Combinar toda la información en el resultado final
    result = {
        "personal": personal,
        "address": address,
        "tutor": tutor,
        "institution": institution,
        "boleta": boleta,
        "materias": subjects_data
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

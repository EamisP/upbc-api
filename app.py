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
                # Si hay error con alguna materia se ignora y continúa
                continue
        
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

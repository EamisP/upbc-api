from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.options import Options

options = Options()
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=options)

try:
    # 1. Abrir la página de la escuela
    driver.get("https://www2.upbc.edu.mx/alumnos/siaax/")
    wait = WebDriverWait(driver, 10)
    
    # 2. Ubicar los campos de usuario y contraseña y realizar el login
    username_field = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tb_usr")))
    password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tb_pass")
    username_field.send_keys("220132")
    password_field.send_keys("Temporalpass")
    
    # 3. Hacer clic en el botón de acceso
    submit_button = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_tb_aceptar")))
    submit_button.click()
    
    # 4. Esperar a que aparezca un elemento que confirme el login (por ejemplo, el nombre del alumno)
    wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_lb_lnom")))
    time.sleep(3)  # Espera adicional para asegurar que todos los elementos estén cargados

    # 5. Extraer los datos con scraping

    # Nombre
    name = driver.find_element(By.ID, "ContentPlaceHolder1_lb_lnom").text

    # Número de estudiante
    numberStudent = driver.find_element(By.ID, "ContentPlaceHolder1_lb_lmat").text

    # Carrera
    career = driver.find_element(By.ID, "ContentPlaceHolder1_lb_lprog").text

    # Dirección (se compone de varios campos)
    direccion = {
        "direccion": driver.find_element(By.ID, "ContentPlaceHolder1_lb_ldir").text,
        "colonia": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lcol").text,
        "municipio": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lmun").text,
        "estado": driver.find_element(By.ID, "ContentPlaceHolder1_lb_ledo").text,
        "cp": driver.find_element(By.ID, "ContentPlaceHolder1_lb_lcp").text
    }

    # Correo personal
    mailPersonal = driver.find_element(By.ID, "ContentPlaceHolder1_lb_lemail").text

    # Datos del tutor
    tutorData = {
        "tutor": driver.find_element(By.ID, "ContentPlaceHolder1_lb_tutor").text,
        "correoTutor": driver.find_element(By.ID, "ContentPlaceHolder1_lbmemail").text
    }

    # Correo institucional del estudiante
    mailStudent = {
        "instEmail": driver.find_element(By.ID, "ContentPlaceHolder1_lb_inst_email").text,
        "instClave": driver.find_element(By.ID, "ContentPlaceHolder1_lb_inst_clave").text
    }

    # 6. Imprimir los datos en la terminal
    print("Nombre:", name)
    print("Número de estudiante:", numberStudent)
    print("Carrera:", career)
    print("Dirección:")
    print("  Dirección:", direccion["direccion"])
    print("  Colonia:", direccion["colonia"])
    print("  Municipio:", direccion["municipio"])
    print("  Estado:", direccion["estado"])
    print("  Código Postal:", direccion["cp"])
    print("Correo personal:", mailPersonal)
    print("Datos del tutor:")
    print("  Tutor:", tutorData["tutor"])
    print("  Correo del tutor:", tutorData["correoTutor"])
    print("Correo institucional:")
    print("  Email:", mailStudent["instEmail"])
    print("  Clave:", mailStudent["instClave"])

    time.sleep(5)  # Espera para poder ver la salida antes de cerrar el navegador
finally:
    driver.quit()

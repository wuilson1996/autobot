# websockets
import asyncio
from asgiref.sync import sync_to_async
import websockets
import base64
#import cv2

# instagram
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests
import json
import threading
import os
from PIL import Image
import random
from colorama import init, Fore, Back, Style
import logging
import platform

# email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import re
import time
from time import sleep


class ReCapchat:
    def __init__(self, driver=None, language="en-US") -> None:
        self._driver = driver
        self.language = language

    def run(self, name_file = "audio"):
        soup = BeautifulSoup(self._driver.page_source, "html.parser")
        iframe = soup.find("iframe", {"id": "recaptcha-iframe"})
        print(iframe)
        #for i in iframe:
        #    print(i.get("title"))
        result = False
        if iframe is not None:
            try:
                WebDriverWait(self._driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='recaptcha-iframe']")))
                WebDriverWait(self._driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@title='reCAPTCHA']")))
            except Exception as e:
                print("[-] ReCapchat not Found")
            while True:
                if iframe is None:
                    break
                else:
                    try:
                        checkbox = WebDriverWait(self._driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//span[@id='recaptcha-anchor']")))
                        is_checked = checkbox.get_attribute("aria-checked")
                        soup = BeautifulSoup(checkbox.get_attribute("innerHTML"), "html.parser")
                        if is_checked == "true" and "recaptcha-checkbox-checked" in checkbox.get_attribute("class"):
                            result = True
                            print("[+] Checkmark reCapcha Verification success")
                            self._driver.switch_to.default_content()
                            sleep(2)
                            for b in self._driver.find_elements_by_xpath("//button[@type='button']"):
                                if "Siguiente" == str(b.text).strip():
                                    b.click()
                                    break
                            break
                    except Exception as error:
                        print("[-] ReCapchat not Found")
        else:
            print("[-] ReCapchat not Found")
            result = True
        return result

class ServiceEmail:
    def __init__(self, username, password, to) -> None:
        # Configuración del servidor
        self.smtp_server = "mail.fixco.co"#"smtp.office365.com"
        self.puerto_imap = 993
        self.smtp_port = 587
        self.username = username
        self.password = password
        # settings server received
        #self.imap_server = "mail.fixco.co"#"outlook.office365.com"
        self.to = to

    def received(self):
        # Conectar al servidor
        mail = imaplib.IMAP4_SSL(self.smtp_server, self.puerto_imap)
        mail.login(self.username, self.password)

        # Seleccionar la bandeja de entrada
        mail.select("inbox")

        # Ejecutar el bucle de verificación por 1 minuto
        confirmation_code = None
        start_time = time.time()
        while time.time() - start_time < 60:
            try:
                # Buscar correos no leídos
                status, messages = mail.search(None, 'UNSEEN')
                email_ids = messages[0].split()
                #print("Check message: "+str(time.time() - start_time))
                status_received = False
                for e_id in email_ids:
                    status, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")
                            from_ = msg.get("From")
                            #print("Subject:", subject)
                            #print("From:", from_)

                            # Obtener el cuerpo del correo
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                    except:
                                        pass
                                    #if content_type == "text/plain" and "attachment" not in content_disposition:
                                        #print("Body:", body)
                                    #    pass
                            else:
                                body = msg.get_payload(decode=True).decode()
                                #print("Body:", body)

                            try:
                                soup = BeautifulSoup(body, 'html.parser')
                                if self.is_instagram(soup):
                                    try:
                                        # Extraer el código de confirmación (asumiendo que el formato es consistente)
                                        confirmation_code = soup.find('td', attrs={'style': 'padding:10px;color:#565a5c;font-size:32px;font-weight:500;text-align:center;padding-bottom:25px;'}).text.strip()
                                        #print(f"Código de confirmación: {confirmation_code}")
                                        status_received = True
                                        break
                                    except Exception as e:
                                        print("Error message email: "+str(e))
                            except Exception as e2:
                                print("Error exception body: "+str(e2))
                    
                if status_received:
                    break
            except Exception as e3:
                print("Error general while: "+str(e3))
        mail.logout()

        return confirmation_code
    
    # Verificar que el correo proviene de Instagram y contiene el texto esperado
    def is_instagram(self, soup):
        # Verificar que el título contiene "Facebook" o "Instagram"
        title = soup.title.string if soup.title else ""
        if "Instagram" not in title and "Facebook" not in title:
            return False

        # Verificar que el cuerpo contiene el texto esperado
        expected_text = "Someone tried to sign up for an Instagram account"
        body_text = soup.get_text()
        if expected_text not in body_text:
            return False

        return True


class ManageInsta:
    def __init__(self, email, password_email, password, username, name, end_search) -> None:
        self.url = "https://www.instagram.com"
        self.driver = None
        self._email = email
        self._password = password
        self._password_email = password_email
        self._username = username
        self._name = name
        self.end_search = end_search
        self._active_search = True

        self.day = "15"
        self.month = "junio"
        self.anio = "2000"

    @property
    def cant(self):
        return self.end_search

    @property
    def active_search(self):
        return self._active_search
    
    @active_search.setter
    def active_search(self, state):
        self._active_search = state

    def create(self):
        pass
    
    def _webdriver(self) -> webdriver.Firefox:
        options = webdriver.FirefoxOptions()
        #options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)

    def _webdriver2(self, proxy_extention=None) -> webdriver.Chrome:
        options = webdriver.Options()
        #options.add_argument("--headless")
        options.add_argument("disable-gpu")
        options.add_argument("no-sandbox")
        path_extention = os.path.abspath("manage_insta.py").replace("manage_insta.py", "captchaSolver")
        path_extention2 = os.path.abspath("manage_insta.py").replace("manage_insta.py", "holaVpn")
        #path_extention3 = os.path.abspath("manage_insta.py").replace("manage_insta.py", "VeePn")
        #path_extention4 = os.path.abspath("manage_insta.py").replace("manage_insta.py", "vpn")
        options.add_argument(f"--load-extension={path_extention},{path_extention2}")
        path_driver = os.path.abspath("chromedriver.exe")
        #if proxy_extention:
        #    options.add_extension(proxy_extention)
        return webdriver.Chrome(path_driver, options=options)

    def create_account(self, _driver:webdriver.Firefox):
        try:
            _driver.get(self.url)
            _driver.implicitly_wait(15)
            _driver.maximize_window()
            time.sleep(4)
            for b in _driver.find_elements_by_tag_name("button"):
                if "Permitir todas las cookies" in b.text:
                    b.click()
                    time.sleep(5)
                    break
            for a in _driver.find_elements_by_tag_name("a"):
                print(a.text)
                if "Regístrate" == str(a.text).strip() or "Sign up" in str(a.text).strip():
                    a.click()
                    break
            sleep(2)
            _driver.find_element_by_xpath("//input[@name='emailOrPhone']").send_keys(self._email)
            sleep(1)
            _driver.find_element_by_xpath("//input[@name='fullName']").send_keys(self._name)
            sleep(1)
            _driver.find_element_by_xpath("//input[@name='username']").send_keys(self._username)
            sleep(1)
            _driver.find_element_by_xpath("//input[@name='password']").send_keys(self._password)
            sleep(1)
            #screen_width = _driver.execute_script("return window.screen.availWidth;")
            #screen_height = _driver.execute_script("return window.screen.availHeight;")
            #print(screen_width, screen_height)
            # Calcular las dimensiones de cada ventana (mitad de la pantalla)
            #half_screen_width = screen_width // 2
            #_driver.set_window_size(half_screen_width, screen_height)
            #_driver.set_window_position(0, 0)

            for b in _driver.find_elements_by_xpath("//button[@type='submit']"):
                if "Registrarte" == str(b.text).strip() or "Siguiente" == str(b.text).strip() or "Sign up" in str(b.text).strip():
                    b.click()
                    break
    
            if "Este nombre de usuario no está disponible. Prueba otro." in _driver.page_source:
                logging.info(f"Este nombre de usuario no está disponible. Prueba otro: {self._email}")
                return False

            time.sleep(2)

            for day in _driver.find_element_by_xpath("//select[@title='Day:']").find_elements_by_tag_name("option"):
                if day.text == self.day:
                    day.click()

            for day in _driver.find_element_by_xpath("//select[@title='Month:']").find_elements_by_tag_name("option"):
                if day.text == self.month:
                    day.click()

            for day in _driver.find_element_by_xpath("//select[@title='Year:']").find_elements_by_tag_name("option"):
                if day.text == self.anio:
                    day.click()

            for b in _driver.find_elements_by_tag_name("button"):
                if "Siguiente" == str(b.text).strip() or "Next" == str(b.text).strip():
                    b.click()
                    break
            
            time.sleep(5)
            re_captcha = ReCapchat(_driver)
            re_captcha.run()

            service_email = ServiceEmail(
                username=self._email,
                password=self._password_email,
                to=""
            )
            start_time = time.time()
            state = True
            print("Check code confirmation")
            while time.time() - start_time < 60:
                try:
                    confirmation_code = service_email.received()
                    print(confirmation_code)
                except Exception as e:
                    logging.info(e)
                    state = False
                    break
                _driver.find_element_by_xpath("//input[@name='email_confirmation_code']").send_keys(confirmation_code)

                for b in _driver.find_elements_by_xpath("//div[@role='button']"):
                    if "Siguiente" == str(b.text).strip() or "Next" == str(b.text).strip():
                        b.click()
                        break
                time.sleep(1)
                if "El código no es válido. Puedes solicitar uno nuevo." in str(_driver.page_source):
                    logging.info("El código no es válido. Puedes solicitar uno nuevo.")
                    _driver.find_element_by_xpath("//input[@name='email_confirmation_code']").clear()
                else:
                    break
            
            time.sleep(10)
            try:
                if "Activar notificaciones" in str(_driver.page_source):
                    for b in _driver.find_elements_by_tag_name("button"):
                        if "Ahora no" == str(b.text).strip():
                            b.click()
                            break
                #state = False
            except Exception as e:
                logging.info("Error Activa notifications: "+str(e))
        except Exception as e:
            logging.info("Error: "+str(e))
            print("Error: "+str(e))
            state = False
        return state

    def sign_in(self, _driver:webdriver.Firefox):
        _driver.get(self.url)
        _driver.implicitly_wait(15)
        _driver.maximize_window()
        time.sleep(2)
        for b in _driver.find_elements_by_tag_name("button"):
            if "Permitir todas las cookies" in b.text:
                b.click()
                time.sleep(5)
                break
        _driver.find_element_by_xpath("//input[@name='username']").send_keys(self._email)
        _driver.find_element_by_xpath("//input[@name='password']").send_keys(self._password)
        time.sleep(1)
        for b in _driver.find_elements_by_xpath("//button[@type='submit']"):
            if "Entrar" == str(b.text).strip():
                b.click()
                #screen_width = _driver.execute_script("return window.screen.availWidth;")
                #screen_height = _driver.execute_script("return window.screen.availHeight;")
                #print(screen_width, screen_height)
                # Calcular las dimensiones de cada ventana (mitad de la pantalla)
                #half_screen_width = screen_width // 2
                #_driver.set_window_size(half_screen_width, screen_height)
                #_driver.set_window_position(0, 0)
                break
        # time.sleep(2)
        # if "¿Guardar tu información de inicio de sesión?" in str(_driver.page_source):
        #     for b in _driver.find_elements_by_tag_name("button"):
        #         if "Ahora no" == str(b.text).strip():
        #             b.click()
        #             break

        # time.sleep(2)
        # if "Activar notificaciones" in str(_driver.page_source):
        #     for b in _driver.find_elements_by_tag_name("button"):
        #         if "Ahora no" == str(b.text).strip():
        #             b.click()
        #             break
        time.sleep(5)
        state = True
        block = False
        for b in _driver.find_elements_by_xpath("//button[@type='submit']"):
            if "Entrar" == str(b.text).strip():
                state = False
                if "Tu contraseña no es correcta. Vuelve a comprobarla." in _driver.page_source:
                    block = True
                    logging.info(f"Account login problem: {self._email}")
                break
        
        time.sleep(5)
        if "hemos suspendido tu cuenta permanentemente." in _driver.page_source or "Intento de inicio de sesión sospechoso" in _driver.page_source:
            block = True
            logging.info(f"Account login problem block: {self._email}")
        return state, block
    
    def logout(self, _driver:webdriver.Firefox):
        time.sleep(10)
        #print("Activar notificaciones" in str(_driver.page_source))
        if "Activar notificaciones" in str(_driver.page_source):
            for b in _driver.find_elements_by_tag_name("button"):
                #print(b.text)
                if "Ahora no" == str(b.text).strip():
                    b.click()
                    break
        time.sleep(2)
        buttons = _driver.find_elements_by_xpath("//a[@role='link']")
        for b in buttons:
            if "Más" == str(b.text).strip(""):
                b.click()
                break
        time.sleep(2)
        _dialog = _driver.find_elements_by_xpath("//div[@role='dialog']")
        for d in _dialog:
            if "Salir" in d.text:
                for s in d.find_elements_by_tag_name("div"):
                    if "Salir" == str(s.text).strip():
                        #print(str(s.text).strip())
                        s.click()
                        break
                break

    def send_dm(self, person_user, text_dm, _driver:webdriver.Firefox):
        _driver.get(self.url+"/"+person_user+"/")
        _driver.implicitly_wait(15)
        #_driver.maximize_window()
        
        state = False
        if "Esta página no está disponible." not in _driver.page_source and "Esta cuenta es privada" not in _driver.page_source and "Síguela para ver sus fotos o vídeos." not in _driver.page_source:
            try:
                buttons = _driver.find_elements_by_xpath("//button[@type='button']")
                for b in buttons:
                    if "Seguir" in b.text:
                        b.click()
                        break
            except Exception as e:
                logging.info("Error in button Seguir")

            time.sleep(2)
            try:
                buttons = _driver.find_elements_by_xpath("//div[@role='button']")
                for b in buttons:
                    if "Enviar mensaje" in b.text:
                        b.click()
                        break
            except Exception as e:
                logging.info("Error in button Enviar mensaje")
            time.sleep(3)
            try:
                _driver.find_element_by_xpath("//div[@role='textbox']").send_keys(text_dm)
            except Exception as e:
                logging.info("Error in textbox")

            if "Activar notificaciones" in str(_driver.page_source):
                for b in _driver.find_elements_by_tag_name("button"):
                    if "Ahora no" == str(b.text).strip():
                        b.click()
                        break
            time.sleep(2)
            try:
                buttons = _driver.find_elements_by_xpath("//div[@role='button']")
                for b in buttons:
                    if "Enviar" in b.text:
                        logging.info(f"[+] Send Message with user {person_user}...")
                        #b.click()
                        state = True
                        break
            except Exception as e:
                logging.info("Error in button Enviar mensaje")
        return state

    def get_users(self, person_user, _driver:webdriver.Firefox):
        _driver.get(self.url+"/"+person_user+"/")
        _driver.implicitly_wait(15)
        #_driver.maximize_window()

        time.sleep(3)
        _driver.find_element_by_xpath("//a[@href='/crece.en.redes.sociales/followers/']").click()
        time.sleep(5)
        return self.dialog_data(_driver)

    def dialog_data(self, _driver:webdriver.Firefox):
        time.sleep(5)
        _dialog = _driver.find_elements_by_xpath("//div[@role='dialog']")
        div_class = ""
        links_user = []
        #for d in _dialog:
            #print(d.get_attribute("innerHTML"))
            #print("----------------------------------------------------")
        if "Seguidores" in str(_dialog[1].get_attribute("innerHTML")):
            soup = BeautifulSoup(_dialog[1].get_attribute("innerHTML"), 'html.parser')
            if "Siguiendo" in str(_dialog[1].get_attribute("innerHTML")):
                for c in soup.find_all("div")[19].get("class"):
                    div_class += c+" "

                logging.info(f"[+] Account with used... {div_class}")
            else:
                next_div = soup.find("div").find("div")
                #print(next_div.find_all("div")[19])
                #for nd in next_div.find_all("div"):
                #    print("-------------------------------------------")
                #    print(nd)
                for c in next_div.find_all("div")[13].get("class"):
                    div_class += c+" "
                
                logging.info(f"[+] Account new... {div_class}")

            #print(div_class)
            acum = 400
            _dialog2 = _driver.find_element_by_xpath("//div[@class='"+div_class.strip()+"']")
            while self.active_search:
                try:
                    _driver.execute_script("arguments[0].scrollTop="+str(acum)+";", _dialog2)
                    acum += 600
                    time.sleep(1)
                    _dialog = _driver.find_elements_by_xpath("//div[@role='dialog']")
                    soup = BeautifulSoup(_dialog[1].get_attribute("innerHTML"), 'html.parser')
                    for a in soup.find_all("a", {"role":"link"}):
                        #print(a.get("href"))
                        if str(a.get("href")).strip()[1:-1] not in links_user:
                            #print(str(a.get("href")).strip()[1:-1])
                            links_user.append(str(a.get("href")).strip()[1:-1])
                            yield str(a.get("href")).strip()[1:-1]

                    #if len(links_user) >= self.end_search:
                    #    break
                except Exception as e:
                    logging.info("Error in get follows sleep 15 seconds...")
                    time.sleep(15)
            
            for b in _dialog2.find_elements_by_xpath("//button[@type='button']"):
                if "Cerrar" in b.get_attribute("innerHTML"):
                    #print(b.get_attribute("innerHTML"))
                    b.click()
                    break
            #self.write_file(links_user)
        #return links_user

        #print("-------------------------------2------------------------------")
        #_dialog2 = _driver.find_element_by_xpath("//div[@style='height: auto; overflow: hidden auto;']")
        #print(_dialog2.get_attribute("innerHTML"))
        #print(_dialog2)
        #_driver.execute_script("arguments[0].scrollTop=200;", _dialog2)

        #_dialog3 = _driver.find_element_by_xpath("//div[@style='height: auto; overflow: hidden auto;']/preceding-sibling::div")
        #print(_dialog3)
        #actions = ActionChains(_driver)
        #actions.move_to_element(_dialog2).perform()

    def close(self, _driver:webdriver.Firefox):
        _driver.close()

    def write_file(self, data):
        with open("file.txt", "w") as file:
            for d in data:
                file.write(d+"\n")

class AsyncIterator:
    def __init__(self, seq):
        self.iter = iter(seq)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

def create_accounts(data):
    manage_insta = ManageInsta(
        email=data["email"],
        password_email=data["password_email"],
        password=data["password"],
        username=data["username"],
        name=data["username"],
        end_search=0
    )
    _driver = manage_insta._webdriver()
    manage_insta.create_account(_driver)
    #state, block = manage_insta.sign_in(_driver)
    #print(state, block)
    time.sleep(5)
    #manage_insta.logout(_driver)
    # if state:
    #     data = manage_insta.get_users("crece.en.redes.sociales")
    #     for d in data:
    #manage_insta.send_dm("thehollywoodhustle", "Yo bro, this is the an automatic message from the demo of the instahack software we are working on. we are Anonymous. We are Legion. We do not forgive. We do not forget. Expect us.")
    time.sleep(10)

    manage_insta.close(_driver)

@sync_to_async
def task_in_async(data):
    create_accounts(data)

async def received():
    async with websockets.connect("ws://192.168.20.7:8000/ws/sync/fda7166a4c4766a77327769624b9416035762dd3") as websocket:
        print("[+] Connection to Server success!")
        
        #await websocket.send('{"date":"2024-06-10","type":"all"}')
        while True:
            #try:
                print("[+] Esperando Datos...")
                r = await websocket.recv()
                print(r)
                await task_in_async(json.loads(r))
            #except Exception as e:
            #    print("Error: "+str(e))

async def received_smsend():
    nombre_cliente = "Juan Perez"
    documento_cliente = "123456789"
    monto_prestado = 500000
    interes = 20
    total_pagar = 600000
    modalidad_pago = "Semanal"
    mensaje = f"""Nuevo Cobro a nombre de:{nombre_cliente} - Documento:{documento_cliente} - Monto Prestado:{monto_prestado} - Interes:{interes} - Total:{total_pagar} - Modalidad:{modalidad_pago}
    """
    mensaje = mensaje.encode('utf-8')
    # Convertir el mensaje a base64
    mensaje_base64 = base64.b64encode(mensaje)
    print(str(mensaje_base64)[2:-1])
    async with websockets.connect("wss://4c8c-2800-484-bb90-be00-f00b-cb06-4ec0-d201.ngrok-free.app/ws/smsend/fda7166a4c4766a77327769624b9416035762dd3") as websocket:
        print("[+] Connection to Server success!")
        try:
            await websocket.send('{"phone":"3013804529","text":"'+str(mensaje_base64)[2:-1]+'"}')
            #while True:
            #    print("[+] Esperando Datos...")
            #    r = await websocket.recv()
            #    print(r)
        except Exception as e:
            print("Error: "+str(e))

if __name__ == "__main__":
    asyncio.run(received())
    #create_accounts()
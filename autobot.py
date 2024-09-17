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
import argparse

_logging = logging.basicConfig(filename="logger.log", level=logging.INFO)

class ReCapchat:
    def __init__(self, driver=None, language="en-US") -> None:
        self._driver = driver
        self.language = language

    def run(self, name_file = "audio"):
        soup = BeautifulSoup(self._driver.page_source, "html.parser")
        iframe = soup.find("iframe", {"id": "recaptcha-iframe"})
        logging.info(iframe)
        #for i in iframe:
        #    print(i.get("title"))
        result = False
        if iframe is not None:
            try:
                WebDriverWait(self._driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='recaptcha-iframe']")))
                WebDriverWait(self._driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@title='reCAPTCHA']")))
            except Exception as e:
                logging.info("[-] ReCapchat not Found")
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
                            logging.info("[+] Checkmark reCapcha Verification success")
                            self._driver.switch_to.default_content()
                            sleep(2)
                            for b in self._driver.find_elements_by_xpath("//button[@type='button']"):
                                if "Siguiente" == str(b.text).strip():
                                    b.click()
                                    break
                            break
                    except Exception as error:
                        logging.info("[-] ReCapchat not Found")
        else:
            logging.info("[-] ReCapchat not Found")
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
        while time.time() - start_time < 180:
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
                                        logging.info("Error message email: "+str(e))
                            except Exception as e2:
                                logging.info("Error exception body: "+str(e2))
                    
                if status_received:
                    break
            except Exception as e3:
                logging.info("Error general while: "+str(e3))
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
    
    def _webdriver2(self) -> None:
        if platform.system() == "Windows":
            return self._driver_chrome()
        else:
            return self._driver_firefox()

    def _driver_firefox(self):
        options = webdriver.FirefoxOptions()
        #options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        path_extention = os.path.abspath("autobot.py").replace("autobot.py", "captchaSolver")
        options.add_argument(f"--load-extension={path_extention}")
        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)

    def _webdriver(self, proxy_extention=None):
        options = webdriver.Options()
        #options.add_argument("--headless")
        options.add_argument("disable-gpu")
        options.add_argument("no-sandbox")
        path_extention = os.path.abspath("autobot.py").replace("autobot.py", "captchaSolver")
        path_extention2 = os.path.abspath("autobot.py").replace("autobot.py", "holaVpn")
        #path_extention3 = os.path.abspath("autobot.py").replace("autobot.py", "VeePn")
        #path_extention4 = os.path.abspath("autobot.py").replace("autobot.py", "vpn")
        options.add_argument(f"--load-extension={path_extention}")
        if platform.system() == "Windows":
            path_driver = os.path.abspath("chromedriver.exe")
        else:
            path_driver = os.path.abspath("chromedriver")
        
        #if proxy_extention:
        #    options.add_extension(proxy_extention)
        return webdriver.Chrome(path_driver, options=options)

    def create_account(self, _driver):
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
                #logging.info(a.text)
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
                    logging.info("Click button Registrarte")
                    b.click()
                    break
            time.sleep(2)
            if "Este nombre de usuario no está disponible. Prueba otro." in _driver.page_source or "This username isn't available. Please try another." in _driver.page_source:
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
                    logging.info("Click button Siguiente date")
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
            status = True
            block = False
            logging.info("Check code confirmation")
            while time.time() - start_time < 300:
                try:
                    confirmation_code = service_email.received()
                    logging.info(confirmation_code)
                except Exception as e:
                    logging.info(e)
                    status = False
                    break
                if confirmation_code != None:
                    _driver.find_element_by_xpath("//input[@name='email_confirmation_code']").send_keys(confirmation_code)

                    for b in _driver.find_elements_by_xpath("//div[@role='button']"):
                        if "Siguiente" == str(b.text).strip() or "Next" == str(b.text).strip():
                            b.click()
                            break
                    time.sleep(1)
                    if "El código no es válido. Puedes solicitar uno nuevo." in str(_driver.page_source) or "That code isn't valid. You can request a new one." in str(_driver.page_source):
                        logging.info("El código no es válido. Puedes solicitar uno nuevo.")
                        _driver.find_element_by_xpath("//input[@name='email_confirmation_code']").clear()
                    else:
                        break
                else:
                    status = False
            time.sleep(15)
            try:
                if "Activar notificaciones" in str(_driver.page_source) or "Turn on Notifications" in str(_driver.page_source):
                    for b in _driver.find_elements_by_tag_name("button"):
                        if "Ahora no" == str(b.text).strip() or "Not Now" in str(b.text).strip() or "Not now" in str(b.text).strip():
                            b.click()
                            break
            except Exception as e:
                logging.info("Error Activa notifications: "+str(e))
            
            time.sleep(5)
            if "hemos suspendido tu cuenta permanentemente." in _driver.page_source or "Intento de inicio de sesión sospechoso" in _driver.page_source or "We Detected An Unusual Login Attempt" in _driver.page_source or "Suspicious Login Attempt" in _driver.page_source or "We suspended your account" in _driver.page_source or "We suspect automated behavior on your account" in _driver.page_source:
                block = True
                status = False
                logging.info(f"Account login problem block: {self._email}")
        except Exception as e:
            logging.info("Error: "+str(e))
            status = False
        return status, block

    def sign_in(self, _driver):
        _driver.get(self.url)
        _driver.implicitly_wait(15)
        _driver.maximize_window()
        time.sleep(5)
        for b in _driver.find_elements_by_tag_name("button"):
            if "Permitir todas las cookies" in b.text:
                b.click()
                time.sleep(5)
                break
        _driver.find_element_by_xpath("//input[@name='username']").send_keys(self._email)
        _driver.find_element_by_xpath("//input[@name='password']").send_keys(self._password)
        time.sleep(1)
        for b in _driver.find_elements_by_xpath("//button[@type='submit']"):
            if "Entrar" == str(b.text).strip() or "Log in" == str(b.text).strip():
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
        status = True
        block = False
        for b in _driver.find_elements_by_xpath("//button[@type='submit']"):
            if "Entrar" == str(b.text).strip() or "Log in" == str(b.text).strip():
                status = False
                if "Tu contraseña no es correcta. Vuelve a comprobarla." in _driver.page_source or "Sorry, your password was incorrect. Please double-check your password." in _driver.page_source:
                    block = True
                    logging.info(f"Account login problem: {self._email}")
                break
        
        time.sleep(5)
        if "hemos suspendido tu cuenta permanentemente." in _driver.page_source or "Intento de inicio de sesión sospechoso" in _driver.page_source or "We Detected An Unusual Login Attempt" in _driver.page_source or "Suspicious Login Attempt" in _driver.page_source or "We suspended your account" in _driver.page_source  or "We suspect automated behavior on your account" in _driver.page_source:
            block = True
            status = False
            logging.info(f"Account login problem block: {self._email}")
        return status, block
    
    def logout(self, _driver):
        _driver.get(self.url)
        _driver.implicitly_wait(15)
        time.sleep(4)
        block = False
        status = False
        if "hemos suspendido tu cuenta permanentemente." in _driver.page_source or "Intento de inicio de sesión sospechoso" in _driver.page_source or "We Detected An Unusual Login Attempt" in _driver.page_source or "Suspicious Login Attempt" in _driver.page_source or "We suspended your account" in _driver.page_source or "We suspect automated behavior on your account" in _driver.page_source:
            block = True
            status = True
            logging.info(f"Account login problem block: {self._email}")
        if not block:
            #print("Activar notificaciones" in str(_driver.page_source))
            if "Activar notificaciones" in str(_driver.page_source) or "Turn on Notifications" in str(_driver.page_source):
                for b in _driver.find_elements_by_tag_name("button"):
                    #print(b.text)
                    if "Ahora no" == str(b.text).strip() or "Not Now" in str(b.text).strip() or "Not now" in str(b.text).strip():
                        b.click()
                        break
            time.sleep(1)
            buttons = _driver.find_elements_by_xpath("//a[@role='link']")
            for b in buttons:
                if "Más" == str(b.text).strip("") or "More" == str(b.text).strip(""):
                    b.click()
                    break
            time.sleep(1)
            _dialog = _driver.find_elements_by_xpath("//div[@role='dialog']")
            for d in _dialog:
                if "Salir" in d.text or "Log out" in d.text:
                    for s in d.find_elements_by_tag_name("div"):
                        if "Salir" == str(s.text).strip() or "Log out" == str(s.text).strip():
                            #print(str(s.text).strip())
                            status = True
                            s.click()
                            break
                    break
        return status, block

    def send_dm(self, person_user, text_dm, _driver):
        _driver.get(self.url+"/"+person_user+"/")
        _driver.implicitly_wait(15)
        #_driver.maximize_window()
        time.sleep(2)
        block = False
        status = False
        if "hemos suspendido tu cuenta permanentemente." in _driver.page_source or "Intento de inicio de sesión sospechoso" in _driver.page_source or "We Detected An Unusual Login Attempt" in _driver.page_source or "Suspicious Login Attempt" in _driver.page_source or "We suspended your account" in _driver.page_source or "We suspect automated behavior on your account" in _driver.page_source:
            block = True
            logging.info(f"Account login problem block: {self._email}")
        if not block:
            if "Esta página no está disponible." not in _driver.page_source and "Esta cuenta es privada" not in _driver.page_source and "Síguela para ver sus fotos o vídeos." not in _driver.page_source and "This account is private" not in _driver.page_source:
                # try:
                #     buttons = _driver.find_elements_by_xpath("//button[@type='button']")
                #     for b in buttons:
                #         if "Seguir" in b.text or "Follow" in b.text:
                #             b.click()
                #             break
                # except Exception as e:
                #     logging.info("Error in button Seguir")

                time.sleep(2)
                button_message = False
                try:
                    buttons = _driver.find_elements_by_xpath("//div[@role='button']")
                    for b in buttons:
                        if "Enviar mensaje" in b.text or "Message" in b.text:
                            b.click()
                            button_message = True
                            break
                except Exception as e:
                    logging.info("Error in button Enviar mensaje")
                if button_message:
                    time.sleep(3)
                    try:
                        for t in text_dm:
                            _driver.find_element_by_xpath("//div[@role='textbox']").send_keys(t)
                    except Exception as e:
                        logging.info("Error in textbox")

                    if "Activar notificaciones" in str(_driver.page_source) or "Turn on Notifications" in str(_driver.page_source):
                        for b in _driver.find_elements_by_tag_name("button"):
                            if "Ahora no" == str(b.text).strip() or "Not Now" in str(b.text).strip() or "Not now" in str(b.text).strip():
                                b.click()
                                break
                    time.sleep(2)
                    try:
                        # Not everyone can message this account.
                        buttons = _driver.find_elements_by_xpath("//div[@role='button']")
                        for b in buttons:
                            if "Enviar" in b.text or "Send" in b.text:
                                logging.info(f"[+] Send Message with user {person_user}...")
                                b.click()
                                status = True
                                break
                    except Exception as e:
                        logging.info("Error in button Enviar mensaje")
        return status, block

    def get_users(self, person_user, _driver):
        _driver.get(self.url+"/"+person_user+"/")
        _driver.implicitly_wait(15)
        #_driver.maximize_window()

        time.sleep(3)
        _driver.find_element_by_xpath("//a[@href='/crece.en.redes.sociales/followers/']").click()
        time.sleep(5)
        return self.dialog_data(_driver)

    def dialog_data(self, _driver):
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

    def close(self, _driver):
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

DRIVER = {}
websocket = None

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
    status, block = manage_insta.create_account(_driver)
    if status:
        DRIVER[data["email"]] = {"driver": _driver, "instance": manage_insta}
        logging.info("[+] SignUp success...")
    else:
       manage_insta.close(_driver)
    return status, block

# def sign_in_account(data):
#     manage_insta = ManageInsta(
#         email=data["email"],
#         password_email=data["password_email"],
#         password=data["password"],
#         username=data["username"],
#         name=data["username"],
#         end_search=0
#     )
#     _driver = manage_insta._webdriver()
#     #manage_insta.create_account(_driver)
#     state, block = manage_insta.sign_in(_driver)
#     logging.info(state, block)
#     time.sleep(5)
#     if not block:
#         manage_insta.logout(_driver)
#         # if state:
#         #     data = manage_insta.get_users("crece.en.redes.sociales")
#         #     for d in data:
#         #manage_insta.send_dm("thehollywoodhustle", "Yo bro, this is the an automatic message from the demo of the instahack software we are working on. we are Anonymous. We are Legion. We do not forgive. We do not forget. Expect us.")
#         time.sleep(10)

#     manage_insta.close(_driver)

# def send_dm_account(data):
#     manage_insta = ManageInsta(
#         email=data["email"],
#         password_email=data["password_email"],
#         password=data["password"],
#         username=data["username"],
#         name=data["username"],
#         end_search=0
#     )
#     _driver = manage_insta._webdriver()
#     #manage_insta.create_account(_driver)
#     state, block = manage_insta.sign_in(_driver)
#     #print(state, block)
#     #time.sleep(1)
#     #manage_insta.logout(_driver)
#     logging.info(state)
#     if state:
#         # data = manage_insta.get_users("crece.en.redes.sociales")
#         # for d in data:
#         manage_insta.send_dm(
#             "wuilsoft", 
#             "Yo bro, this is the an automatic message from the demo of the instahack software we are working on. we are Anonymous. We are Legion. We do not forgive. We do not forget. Expect us.",
#             _driver    
#         )
#         manage_insta.logout(_driver)
#     time.sleep(10)

#     manage_insta.close(_driver)


def sign_in_with_browse(data):
    manage_insta = ManageInsta(
        email=data["email"],
        password_email=data["password_email"],
        password=data["password"],
        username=data["username"],
        name=data["username"],
        end_search=0
    )
    _driver = manage_insta._webdriver()
    status, block = manage_insta.sign_in(_driver)
    if status:
        logging.info("[+] SignIn success...")
        DRIVER[data["email"]] = {"driver": _driver, "instance": manage_insta}
    else:
        _driver.close()
    return status, block

def logout_with_browse(data):
    status, block = DRIVER[data["email"]]["instance"].logout(DRIVER[data["email"]]["driver"])
    DRIVER[data["email"]]["instance"].close(DRIVER[data["email"]]["driver"])
    del DRIVER[data["email"]]
    logging.info("[+] LogOut success...")
    return status, block

def send_dm_with_browse(data):
    status, block = DRIVER[data["email"]]["instance"].send_dm(
        data["follow"],
        data["text"],
        DRIVER[data["email"]]["driver"]    
    )
    if block:
        DRIVER[data["email"]]["instance"].close(DRIVER[data["email"]]["driver"])
        del DRIVER[data["email"]]
    logging.info("[+] Send DM success...")
    return status, block

@sync_to_async
def task_in_async(data) -> bool:
    if data["object"] == "CreateAccount":
        status, block = create_accounts(data)
    # elif data["object"] == "SignInAccount":
    #     status, block = sign_in_account(data)
    # elif data["object"] == "SendDmAccount":
    #     status, block = send_dm_account(data)
    elif data["object"] == "SignIn":
        status, block = sign_in_with_browse(data)
    elif data["object"] == "LogOut":
        status, block = logout_with_browse(data)
    elif data["object"] == "SendDm":
        status, block = send_dm_with_browse(data)
    return status, block

async def task_follow_current(data):
    status, block = await task_in_async(data)
    aux_data = data
    aux_data["status"] = status
    aux_data["block"] = block
    aux_data["machine"] = "BotMaster"
    await websocket.send(json.dumps(aux_data))

async def received(machine, _url):
    global websocket
    url = f"wss://{_url}/ws/sync/fda7166a4c4766a77327769624b9416035762dd3/{machine}"
    while True:
        try:
            async with websockets.connect(url) as ws:
                websocket = ws
                logging.info(f"[+] Connection to Server success! MachineName: {machine}")
                print(f"[+] Connection to Server success! MachineName: {machine}")
                while True:
                    try:
                        logging.info("[+] Esperando Datos...")
                        print("[+] Esperando Datos...")
                        r = await websocket.recv()
                        data = json.loads(r)
                        logging.info(f"{data['email']} {data['object']}")
                        print(f"{data['email']} {data['object']}")
                        if data["object"] == "SendDm":
                            follows = data["follow"]
                            for f in follows:
                                data["follow"] = f
                                asyncio.create_task(task_follow_current(data))
                        else:
                            status, block = await task_in_async(data)
                            aux_data = data
                            aux_data["status"] = status
                            aux_data["block"] = block
                            aux_data["machine"] = "BotMaster"
                            await websocket.send(json.dumps(aux_data))
                    except Exception as e:
                        logging.info(f"Error al recibir o procesar datos: " + str(e))
                        break
        except Exception as errorConnect:
            logging.info(f"[-] Error to connect: "+str(errorConnect))
            logging.info(f"[+] Reconected websocket in 5 seconds...")
            await asyncio.sleep(5)
    
    logging.info(f"[+] Disconnection to Server success! MachineName: {machine}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Autobot Instagram')
    parser.add_argument('machine', type=str, help='Name machine')
    parser.add_argument('url', type=str, help='url botMaster')
    # Parsear los argumentos
    args = parser.parse_args()
    asyncio.run(received(args.machine, args.url))
    #create_accounts({"object":"CreateAccount","email":"accountsite8909334@fixco.co","password_email":"8og3:#_o@##c","password":"Colombia123*","username":"accountsite8909334"})
    #sign_in_account({"object":"SignInAccount","email":"accountsite8909334@fixco.co","password_email":"8og3:#_o@##c","password":"Colombia123*","username":"accountsite8909334"})
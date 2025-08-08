import pandas as pd
import os, sys, json, time, openpyxl


from helper20sms import Helper20SMS, BadApiKeyProvidedException


from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import By
import selenium.webdriver.support.expected_conditions as EC  # noqa
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import undetected_chromedriver as uc






class Parser:
    def __init__(self, url: str):
        self.driver = uc.Chrome()
        self.token = open('token.txt', 'r', encoding='utf-8').read()
        self.url = "https://samokat.ru"
        self.f = 0

    def token_check(self):
        self.f = 0
        if len(self.token) < 2:
            print("Токен не указан. Укажите его в файле token.txt. Инструкция указана в файле инструкция.txt")
            self.f += 1
        else:
            print(f"Токен введён, начинаем регистрацию аккаунта. Не открывайте файл token.txt до завершения работы скрипта")
        return self.f

    def get_driver(self):
        self.driver.get(self.url)
        return self.driver

    def get_cookie(self) -> list[dict]:
        client = Helper20SMS(self.token)
        #items = []
        self.driver.delete_all_cookies()
        self.driver.get(self.url)
        driver = self.get_driver()
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH, "//*[contains(@class, 'ProfileButton_content')]"
            ))
        )


        button = driver.find_element(By.XPATH, "//*[contains(@class, 'Text_text__7SbT7 Text_text--type_p1SemiBold__qdVrZ')]")
        button.click()
        waitinn = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                (By.XPATH, '//button[.//span[text()="Войти по номеру телефона"]]')
            ))
        )
        #button_rega = driver.find_element(By.XPATH, "//*[contains(@class, 'Button_button__86Aws Button_button--size_m__CL5Gn Button_button--theme_secondary__KZeBK')]")
        #button_rega.click()

        button = driver.find_element(By.XPATH, '//button[.//span[text()="Войти по номеру телефона"]]')
        driver.execute_script("arguments[0].click();", button)

        balance = client.get_balance()["data"]["balance"]
        if balance > 5:
            print("Баланс в норме")
        else:
            return(print("Недостаточно денег. Номер не арендован"))
        buy = client.get_number(14452, max_price=15)
        print(f"Номер арендован. Order ID: {buy['data']['order_id']}, номер: {buy['data']['number']}, цена: {buy['data']['price']}")
        rent_number = buy['data']['number']

        order_code = buy['data']['order_id']

        input_selector = '//input[@type="tel"]'

        input_field = driver.find_element(By.XPATH, input_selector)
        input_field.send_keys(rent_number[1:])
        input_field.send_keys(Keys.ENTER)

        time.sleep(10)

        codes = client.get_codes(order_code)
        #current_code = client.get_codes(order_code)['data']['codes'][1]
        input_field = driver.switch_to.active_element

        #f = 0
        #while f>12:
            #codes = client.get_codes(order_code)['data']['codes']
            #if len(codes) > 1 and codes[1] is not None and f < 12:
                #current_code = codes[1]
                #input_field.send_keys(current_code)
                #print("Ввод успешен")
                #break
            #else:
                #time.sleep(10)
                #print("Код не поступил, ожидаем 10 секунд и повторяем")
                #f += 1
        print("Начинаем попытку авторизации")
        for _ in range(12):
            codes = client.get_codes(order_code)['data']['codes']

            if len(codes) > 0 and codes[0] is not None:
                current_code = codes[0]
                input_field.send_keys(current_code)
                print("Вход успешен.")
                break
            time.sleep(10)
            print(f"Код не поступил после {_}/12 попытки. Ждём 10 секунд и пробуем снова")

        else:
            time.sleep(10)
            client.set_order_status(order_code, status = "CANCEL")
            print('Код не получен, заказ завершён, деньги возвращены на баланс')
            sys.exit()

        cookie = driver.get_cookie("__Secure-next-auth.session-token")
        print(cookie)
        cookie_value = cookie['value']
        new_data = pd.DataFrame([{"session_token": cookie_value}])
        file_path = "cookies.xlsx"

        if os.path.exists(file_path):
            # Читаем старые данные
            old_data = pd.read_excel(file_path)
            # Объединяем
            combined = pd.concat([old_data, new_data], ignore_index=True)
        else:
            combined = new_data

        # Перезаписываем файл с объединёнными данными
        combined.to_excel(file_path, index=False)
        print("cookie записаны в таблицу.")

#token = open('token.txt', 'r', encoding='utf-8').read()
#if token is None:
    #print("Токен не указан. Укажите его в файле token.txt")
parser = Parser('https://samokat.ru')
parser.token_check()
if parser.f > 0:
    time.sleep(10)
    sys.exit()
#attempts = int(input("Введите количество попыток получения Cookie:"))
#for _ in range(attempts):
parser.get_cookie()



if input("Программа выполнила работу. Для выхода нажмите ENTER"):
    parser.driver.quit()
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
from sqlalchemy import select, delete, MetaData, NullPool, create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Float
from selenium.common.exceptions import TimeoutException


DATABASE_URL = f"postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"

metadata = MetaData()
engine = create_engine(DATABASE_URL, poolclass=NullPool)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Session = sessionmaker(bind=engine)
session = Session()

class Base(DeclarativeBase):
    pass

Base.metadata.create_all(engine)

class CookieData(Base):
    __tablename__ = "cookiedata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cookie = Column(String)
    is_used = Column(Integer)



async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

attempts_value = int(input("Введите количество попыток регистрации аккаунта: "))

class Parser:
    def __init__(self, url: str):
        self.driver = uc.Chrome(driver_executable_path="/home/johndoe/dev/chrome_138/Linux_x64_1465706_chromedriver_linux64/chromedriver_linux64/chromedriver")
        self.token = open('token.txt', 'r', encoding='utf-8').read()
        self.url = "https://samokat.ru"
        self.f = 0
        self.cookie = None

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

    def register_account(self):
        client = Helper20SMS(self.token)
        #items = []
        driver = self.get_driver()
        #self.driver = uc.Chrome()
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH, "//*[contains(@class, 'ProfileButton_content')]"
            ))
        )


        button = driver.find_element(By.XPATH, "//*[contains(@class, 'Text_text__7SbT7 Text_text--type_p1SemiBold__qdVrZ')]")
        button.click()
        try:
            waitinn = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                (By.XPATH, '//button[.//span[text()="Войти по номеру телефона"]]')
            ))
        )
        except TimeoutException:
            print("Кнопка входа по номеру телефона не загрузилась. Пробуем снова")
            self.driver.quit()
            return 1

        #button_rega = driver.find_element(By.XPATH, "//*[contains(@class, 'Button_button__86Aws Button_button--size_m__CL5Gn Button_button--theme_secondary__KZeBK')]")
        #button_rega.click()

        button = driver.find_element(By.XPATH, '//button[.//span[text()="Войти по номеру телефона"]]')
        driver.execute_script("arguments[0].click();", button)

        balance = client.get_balance()["data"]["balance"]
        if balance > 15:
            print("Баланс в норме")
        else:
            return(print("Недостаточно денег. Номер не арендован"))
            driver.quit()
        buy = client.get_number(14452, max_price=20)
        # Самокат [1] = 14452, Самокат [4] = 15883, Самокат [3] = 37423
        print(f"Номер арендован. ID заказа: {buy['data']['order_id']}, номер: {buy['data']['number']}, цена: {buy['data']['price']}")
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
        for _ in range(24):
            codes = client.get_codes(order_code)['data']['codes']

            if len(codes) > 0 and codes[0] is not None:
                current_code = codes[0]
                input_field.send_keys(current_code)
                print("Вход успешен.")
                return 0
            time.sleep(4)
            print(f"Код не поступил после {_+1}/24 попытки. Ждём 5 секунд и пробуем снова")

        else:
            time.sleep(3)
            client.set_order_status(order_code, status = "CANCEL")
            print('Код не получен, заказ завершён, деньги будут возвращены на баланс')
            self.driver.quit()
            time.sleep(7)
            sys.exit()

    def get_cookie(self):

        time.sleep(3)
        self.driver.refresh()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH, "//*[contains(@class, 'ProfileButton_content')]"
            ))
        )
        time.sleep(2)


        self.cookie = self.driver.get_cookie("__Secure-next-auth.session-token")
        print(self.cookie)

    def write_cookie_xlsx(self):
        cookie_value = self.cookie['value']
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
        print("Сookie записаны в таблицу. Начинаем следующую попытку")
        self.driver.quit()

    def write_cookie_localdb(self):
        #cookie_value = "ajsfjas"
        Base.metadata.create_all(engine)
        cookie_value = self.cookie['value']
        new_db_note = CookieData(cookie = cookie_value, is_used = 0)
        session.add(new_db_note)
        session.commit()
        session.refresh(new_db_note)
        session.close()
        self.driver.quit()

#token = open('token.txt', 'r', encoding='utf-8').read()
#if token is None:
    #print("Токен не указан. Укажите его в файле token.txt")
#parser = Parser('https://samokat.ru')
#parser.token_check()
#if parser.f > 0:
    #time.sleep(10)
    #sys.exit()

i = 0
for i in range(attempts_value):
    if i < attempts_value:
        i += 1
        parser = Parser('https://samokat.ru')
        parser.token_check()
        if parser.f > 0:
            time.sleep(10)
            sys.exit()
        if parser.register_account() != 1:
            parser.get_cookie()
            parser.write_cookie_localdb()
            print(f"Ход выполнения: {i}/{attempts_value}")
        else:
            pass
    #parser.register_account()
    #input("Аккаунт зарегистрирован. Для сохранения куки и выхода нажмите ENTER")
    #parser.get_cookie()
    #parser.write_cookie_localdb()



print("Программа выполнила работу. Это окно закроется автоматически через 8 секунд")
time.sleep(8)
sys.exit()
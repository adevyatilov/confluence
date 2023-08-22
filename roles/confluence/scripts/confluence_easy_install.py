import os
import re
from typing import Union
from pprint import pprint

import docker
import requests
from bs4 import BeautifulSoup

# Параметры Confluence
CONFLUENCE_ADMIN_EMAIL = os.environ.get("CONFLUENCE_ADMIN_EMAIL", 'admin@mail.ru')
CONFLUENCE_ADMIN_LOGIN = os.environ.get("CONFLUENCE_ADMIN_LOGIN", 'ksadmin')
CONFLUENCE_ADMIN_FULLNAME = os.environ.get("CONFLUENCE_ADMIN_FULLNAME", 'Администратор')
CONFLUENCE_ADMIN_PASSWORD = os.environ.get("CONFLUENCE_ADMIN_PASSWORD", 'ksadmin_235689')

# Наименование контейнеров docker
DOCKER_CONTAINER_CONFLUENCE_NAME = os.environ.get("DOCKER_CONTAINER_CONFLUENCE_NAME", 'confluence_confluence_1')
DOCKER_CONTAINER_POSTGRES_NAME = os.environ.get("DOCKER_CONTAINER_POSTGRES_NAME", 'confluence_postgres_1')
DOCKER_CONFLUENCR_NETWORK_NAME = os.environ.get("DOCKER_CONFLUENCR_NETWORK_NAME", 'confluence-network')

class ConfluenceRequests():
   """
      Класс для упрашения запросов к confluence серверу
   """
   def __init__(self, ip: str, port: Union[str, int] = 8090):
      self.URL = f"http://{ip}:{port}/"
      self.session = requests.Session()
      self.atl_token = self.__get_atl_token(self.session.post(self.URL))

   def __get_atl_token(self, response: requests.Response) -> str:
      """
         Параметры:
            reponse: объект requests. Ответ на запрос
         return:
            возвращает atl_token страницы
      """
      soup = BeautifulSoup(response.text, 'lxml')
      pprint(response.status_code)
      pprint(response.text)
      return soup.find(attrs={"name": "atl_token"})["value"]

   def post(self, urn: str, **kwargs) -> requests.Response:
      """
         Отправляет post запрос
      """
      # Устанавливаем atl_token
      kwargs.setdefault('data', {}).update({"atl_token": self.atl_token})

      # Отправляем POST запрос. Вызываем исключение, если ответ 40x, 50x
      response = self.session.post(f"{self.URL}/setup/{urn}", **kwargs)
      response.raise_for_status()

      return response


class DockerContainer():
   """
      Абстракция для задачи в работе с контейнером
   """
   def __init__(self, name: str):
      self.client = docker.from_env()
      self.container = self.client.containers.get(name)
      self.ports = self.container.ports
      self.name = self.container.name
      self.ip = self.__get_ip_addres()
      self.env = self.__get_environ()

   def __get_environ(self) -> dict:
      """
         Возвращает переменные окружения контейнера
      """
      env = {}
      container_env_output = self.exec_run('env')
      for variable in container_env_output.split('\n'):
         if variable:
            var_name, var_value = variable.split('=', 1)
            env.update({var_name: var_value})
      return env

   def __get_ip_addres(self) -> str:
      """
         Возвращает ip адрес контейнера
      """
      network = self.client.networks.get(DOCKER_CONFLUENCR_NETWORK_NAME)
      container_ip = network.attrs['Containers'][self.container.id]['IPv4Address'].split('/')[0]

      return container_ip

   def exec_run(self, cmd: str, *args, **kwargs) -> str:
      """
         Выполняет команду в контейнере и возвращает ее результат
      """
      return self.container.exec_run(cmd, *args, **kwargs).output.decode('ASCII')


def confluence_get_server_id(response: requests.Response) -> str:
   """
      Возвращает serverID. Данный ID нужен для активации confluence
   """
   soup = BeautifulSoup(response.text, 'lxml')

   return soup.find(attrs={"id": "serverId"})["value"]


def main():
   container_postgres = DockerContainer(DOCKER_CONTAINER_POSTGRES_NAME)
   container_confluence = DockerContainer(DOCKER_CONTAINER_CONFLUENCE_NAME)
   # Порт контейнера confluence по умолчанию 8090
   confluence_requests = ConfluenceRequests(container_confluence.ip)

   # confluence_install_steps каждый элемент параметры для запроса
   # urn - URN адреса
   # cоmment - коментарий к запросу
   # data - данные передаваемые в запрос
   confluence_install_steps = [
      {
         "urn": "selectglobaldefaultlocale.action?globalDefaultLocale=ru_RU",
         "comment": "Запрос смены языка на Русский"
      },
      {
         "urn": "dosetupstart.action",
         "comment": "Выбор промышленной устаноки",
         "data": {
            "setupType": "custom",
            "setup-next-button": "Далее"
         }
      },
      {
         "urn": "dosetuplicense.action",
         "comment": 'Страница "License Key". Отправляем ключ активации.',
         "data": {
            "setupTypeCustom": "Далее"
         }
      },
      {
         "urn": "setupdbchoice.action",
         "data": {
            "thisNodeClustered": "false",
            "dbChoice": "custom",
            "setup-next-button": "Далее"
         }
      },
      {
         "urn": "setupdbtype.action",
         "comment": 'Страниц "Set up your database". Запрос с настройками базы данных',
         "data": {
            "dbConfigInfo.databaseType": "postgresql",
            "dbConfigInfo.simple": "false",
            "dbConfigInfo.databaseUrl": f"jdbc:postgresql://{container_postgres.ip}:5432/{container_postgres.env['POSTGRES_DB']}",
            "dbConfigInfo.hostname": "",
            "dbConfigInfo.port": "",
            "dbConfigInfo.databaseName": "",
            "dbConfigInfo.serviceName": "",
            "dbConfigInfo.userName": f"{container_postgres.env['POSTGRES_USER']}",
            "dbConfigInfo.password": f"{container_postgres.env['POSTGRES_PASSWORD']}",
            "dbConfigInfo.instanceName": "",
            "database": ""
         }
      },
      {
         "urn": "setupdata.action",
         "comment": 'Старница "Load Content". Выбираем создание пустого сайта',
         "data": {
           "dbchoiceSelect":	"Пустой+Сайт",
            "contentChoice": "blank"
         }
      },
      {
         "urn": "setupusermanagementchoice.action",
         "comment": 'Страница "Configure User Management". Выбираем управление пользователями групп и пользователей в confluence.',
         "data": {
            "userManagementChoice": "internal",
            "internal": "Управление+пользователями+и+группами+в+Confluence"
         }
      },
      {
         "urn": "setupadministrator.action",
         "comment": 'Страница "Configure System Administrator Account". Заполняем учетные данные администратора',
         "data": {
            "username": f"{CONFLUENCE_ADMIN_LOGIN}",
            "fullName": f"{CONFLUENCE_ADMIN_FULLNAME}",
            "email": f"{CONFLUENCE_ADMIN_EMAIL}",
            "password": f"{CONFLUENCE_ADMIN_PASSWORD}",
            "confirm": f"{CONFLUENCE_ADMIN_PASSWORD}",
            "setup-next-button": "Далее"
         }
      }
   ]

   # Меняем язык Confluence на русский
   confluence_requests.post(confluence_install_steps[0]['urn'])
   print('[+] ', confluence_install_steps[0]['comment'])

   # Выполняем первый запрос и забираем serverID
   resonpse = confluence_requests.post(confluence_install_steps[1]['urn'], data=confluence_install_steps[1]['data'])
   server_id = confluence_get_server_id(resonpse)
   print(server_id)
   # # Выполняем команду в контейнере
   atlassian_agent_output = container_confluence.exec_run('java -jar /var/agent/atlassian-agent.jar'
                                                          ' -p conf'
                                                          f' -m {CONFLUENCE_ADMIN_EMAIL}'
                                                          f' -n {CONFLUENCE_ADMIN_EMAIL}'
                                                          f' -o localhost'
                                                          f' -s {server_id}')
   print(atlassian_agent_output)
   # Убираем лишний вывод команды atlassian-agent, оставляем только ключ
   confLicenseString = '\n'.join(atlassian_agent_output.split('\n')[9:-2])
   print(confLicenseString)
   # Добавляем ключ в данные запроса  и отправляем
   confluence_install_steps[2]['data'].update(confLicenseString=confLicenseString)
   confluence_requests.post(confluence_install_steps[2]['urn'], data=confluence_install_steps[2]['data'])
   # Далее со страниц получать ничего не нужно. Используем цикл для отправки запроса
   for install_step in confluence_install_steps[3:]:
         confluence_requests.post(install_step["urn"], data=install_step["data"])
   print('Настройка confluence завершена.')

if __name__ == '__main__':
   main()
   # test()


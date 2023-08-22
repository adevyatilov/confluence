# Ansible роль Confluence
Ansible роль, содержит развертывание confluence, postgres 11 в контейнерах docker

## Сведения перед установкой
На управляющем серверве должен быть установлен `docker` или содержать архив confluence.tar c образами haxqer/confluence:8.4.0 postgres:11
в директории ./roles/confluence/files

## Описание заданий роли
Для операционной системы Ubuntu:
 - `docker-Ubuntu.yml` - установка docker и docker-compose в Ubuntu
 - `confluence-Ubuntu.yml` - развертывание confluence и postgres c помощью docker-compose

## Переменные роли
Все указанные переменные находяться в файле ./roles/confluence/defaults/main.yml.
Значения указанные со звездой рекомендуется переопределить при подключении роли, как сделано в файле ubuntu.yml

Директория для данных:
 - `confluence_project_dir` - директория для данных confluence, по умолчанию /docker/confluence

Переменные базы данных:
 - `confluence_postgres_dbname`* - наименование базы данных, по умолчанию confluence
 - `confluence_postgres_user`* - пользователь, по умолчанию confluence_bdadmin
 - `confluence_postgres_password` - пароль, по умолчанию задается 30 символьный случайный пароль формата hex

Переменные Confluence:
 - `confluence_confluence_admin_email`* - почта администратора, по умолчанию admin@mail.ru
 - `confluence_confluence_admin_login`* - логин администратора, по умолчанию admin
 - `confluence_confluence_admin_password`* - пароль администратора, по умолчанию admin
 - `confluence_confluence_admin_fullname` - имя учетной записи администратора, по умолчанию Администратор

## Запуск
```bash
# В переменной confluenceIP указываем IP адрес, куда будет развертываться confluence
confluenceIP="you IP"

# Указываем IP адрес в файле инвентори
sed -i "s/# <IP confluence sever>/${confluenceIP}/" hosts.ini

# Выдаем права на запуск
sudo chmod u+x run.sh

# Запускаем скрипт развертывания
./run.sh
```
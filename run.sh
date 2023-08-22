#!/usr/bin/bash

# Относительный путь к архиву с образами Сonfluence 8.4.0 и Postgres 11
PATH_ARCHIVE_IMAGES=./roles/confluence/files/confluence.tar

if [ ! -e "${PATH_ARCHIVE_IMAGES}" ]; then
   # Скачивание образов
   {
      docker pull postgres:11
      docker pull haxqer/confluence:8.4.0
   } > /dev/null

   # Сохраняем образы в архив
   docker save -o ${PATH_ARCHIVE_IMAGES}  haxqer/confluence:8.4.0 postgres:11
fi

# Запускаем плейбук
ansible-playbook -i hosts.ini $@ ubuntu.yml
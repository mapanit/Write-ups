# Cybersecurity Write-ups

Коллекция write-up’ов и заметок по практическим лабораториям и заданиям в области информационной безопасности.

## Профили и портфолио

- [GitHub](https://github.com/mapanit)
- [Сайт-портфолио](https://mapanit.github.io/mapanit-site/)

## Разделы

- [Hack The Box](./hackthebox/) — разборы машин и лабораторных заданий.
- [PortSwigger Web Security Academy](./PortSwiggger/) — заметки по веб-уязвимостям и лабораторным заданиям.
- [VulnHub](./vulnhub/) — разборы уязвимых виртуальных машин.

## Скрипт для изображений

`main.py` переносит встроенные base64-изображения из Markdown в отдельные файлы и заменяет их на относительные ссылки.

```bash
python main.py path/to/write-up.md
```

Для предварительного просмотра без сохранения изменений:

```bash
python main.py path/to/write-up.md --dry-run
```

Скрипт также принимает путь к каталогу и обрабатывает Markdown-файлы рекурсивно. По умолчанию изображения сохраняются в подкаталог `images`; изменить его можно с помощью `--out-dir`.

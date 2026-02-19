#!/bin/bash
# Аудит сервера 193.42.124.206: что запущено, порты, проекты.
# Запуск на сервере: скопировать и вставить в SSH-сессию, или:
#   ssh root@193.42.124.206 'bash -s' < scripts/audit-server.sh

set -e
echo "=== АУДИТ СЕРВЕРА $(hostname) === $(date)"
echo

echo "--- 1. Процессы Python (боты, приложения) ---"
ps aux | grep -E 'python|python3' | grep -v grep || true
echo

echo "--- 2. Слушающие порты (кто чем занят) ---"
(ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) || true
echo

echo "--- 3. Systemd-сервисы (user/root), связанные с ботом или приложениями ---"
systemctl list-units --type=service --state=running --no-pager 2>/dev/null | head -50 || true
echo
echo "Все юниты (включая остановленные) с bot, python, molotok в имени:"
systemctl list-unit-files --no-pager 2>/dev/null | grep -iE 'bot|python|molotok' || true
echo

echo "--- 4. Содержимое /root и /home ---"
echo "/root:"
ls -la /root 2>/dev/null || true
echo "/home:"
ls -la /home 2>/dev/null || true
for u in /home/*; do
  [ -d "$u" ] && echo "  $u:" && ls -la "$u" 2>/dev/null || true
done
echo

echo "--- 5. Типичные каталоги проектов ---"
for d in /opt /var/www /srv; do
  [ -d "$d" ] && echo "$d:" && ls -la "$d" 2>/dev/null || true
done
echo

echo "--- 6. Поиск molotok / bot / .env ---"
find /root /home /opt /srv /var/www -maxdepth 4 -type d -name '*molotok*' 2>/dev/null || true
find /root /home /opt /srv /var/www -maxdepth 4 -type f -name '*.py' 2>/dev/null | head -30
find /root /home /opt /srv /var/www -maxdepth 4 -type f -name '.env' 2>/dev/null || true
echo

echo "--- 7. Python (версия и где) ---"
which python3 2>/dev/null; python3 --version 2>/dev/null || true
which python 2>/dev/null; python --version 2>/dev/null || true
echo

echo "--- 8. Git (есть ли репозитории) ---"
find /root /home /opt /srv /var/www -maxdepth 5 -type d -name '.git' 2>/dev/null | head -20
echo

echo "=== КОНЕЦ АУДИТА ==="

# Сервер 193.42.124.206: аудит, нормализация, деплой бота

Пошаговая инструкция: сначала смотрим, что на сервере, приводим всё в порядок (чтобы проекты друг другу не мешали), затем переносим изменения с GitHub и запускаем бота.

---

## Результаты аудита (актуальное состояние сервера)

| Что | Где / как |
|-----|-----------|
| **Telegram-бот «Молоток»** | Запущен как `telegram_bot.service`, процесс: `/opt/venv/bin/python3 /opt/fixed_bot.py` |
| **Код бота** | В `/opt`: `fixed_bot.py`, `bot.py`, `bot_backup.py`, `simple_bot.py` — старая одностраничная версия, без структуры из GitHub |
| **Секреты** | `/opt/.env` (есть) |
| **Второй юнит** | `molotok-bot.service` — включён, но в списке running только `telegram_bot.service` (значит, активен один сервис) |
| **VK-бот** | `/root/vk_bot` — отдельный проект, не трогаем |
| **Порты** | 22 (SSH), 53 (resolve), 443 (xray). Бот порты не слушает — конфликтов нет |
| **Git в /opt** | Нет — код на сервер клали вручную, обновлений с GitHub пока не было |

**Цель:** оставить один сервис для бота, перевести его на код из GitHub (`main.py`, `handlers/`, `storage/`, логи и пересылка админу).

---

## Шаг 0. Подключение к серверу

```bash
ssh root@193.42.124.206
```

(Или свой пользователь, если не root.)

---

## Часть 1. Аудит — что на сервере

### Вариант А: выполнить скрипт аудита

С **локального ПК** (из папки проекта):

```bash
ssh root@193.42.124.206 'bash -s' < scripts/audit-server.sh
```

Вывод сохраните (скопируйте в файл или перенаправьте: `... > audit.txt`).

### Вариант Б: выполнить команды вручную в SSH

Подключитесь к серверу и по очереди выполните:

```bash
# Процессы Python
ps aux | grep python

# Кто слушает порты
ss -tlnp

# Сервисы systemd
systemctl list-units --type=service --state=running
systemctl list-unit-files | grep -iE 'bot|python|molotok'

# Где лежат проекты
ls -la /root /home
ls -la /opt /srv /var/www 2>/dev/null

# Поиск бота и .env
find /root /home /opt /srv -maxdepth 4 \( -name '*molotok*' -o -name '.env' \) 2>/dev/null
find /root /home /opt /srv -maxdepth 4 -name '*.py' -type f 2>/dev/null
```

По результатам смотрите:
- сколько процессов `python`/`python3` и что они запускают;
- нет ли двух ботов на одном аккаунте;
- где лежит текущая версия бота и есть ли рядом `.env`.

---

## Нормализация и деплой (по результатам аудита) — готовые шаги

Выполнять по порядку в SSH на сервере.

### 1. Остановить старый бот и снять дублирующий сервис

```bash
systemctl stop telegram_bot.service
systemctl stop molotok-bot.service
systemctl disable molotok-bot.service
```

(Оба отключены, чтобы не было двух процессов одного бота.)

### 2. Резервная копия текущего /opt и .env

```bash
cp -a /opt /.opt_backup_$(date +%Y%m%d)
cp /opt/.env /root/molotok_env_backup.txt
```

Токен и настройки сохранены в `/root/molotok_env_backup.txt` и в `/.opt_backup_*`.

### 3. Каталог под новый код и клонирование с GitHub

```bash
mkdir -p /opt/molotok-bot
cd /opt/molotok-bot
git clone https://github.com/AlexMuza/molotok-bot.git .
```

Если `git` не установлен: `apt update && apt install -y git`.

Если в репозитории основная ветка — `master`, а не `main`, переключиться: `git checkout master`.

**Важно:** если после `git clone` в каталоге нет файла `main.py` и папок `handlers/`, `storage/` — на GitHub ещё старая версия. Сначала с **локального ПК** (из папки «молотокБот») выполни: `git push origin master` (или `main`), залогинившись в GitHub. После пуша на сервере сделай `cd /opt/molotok-bot && git pull origin main` (или `master`).

### 4. .env (токен и ID админа)

```bash
cp /opt/.env /opt/molotok-bot/.env
nano /opt/molotok-bot/.env
```

Проверь, что в файле есть обе переменные (по одной на строку, без кавычек):

- `TELEGRAM_BOT_TOKEN=...`
- `ADMIN_CHAT_ID=...`

Если `ADMIN_CHAT_ID` не было — добавь (узнать ID: бот [@userinfobot](https://t.me/userinfobot) в Telegram). Сохранить: Ctrl+O, Enter, Ctrl+X.

### 5. Виртуальное окружение и зависимости

```bash
cd /opt/molotok-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### 6. Один systemd-сервис для бота

Создать юнит (заменить старый `telegram_bot.service` на один общий):

```bash
cat > /etc/systemd/system/molotok-bot.service << 'EOF'
[Unit]
Description=Molotok Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/molotok-bot
Environment=PATH=/opt/molotok-bot/venv/bin
ExecStart=/opt/molotok-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Отключить старый юнит, включить новый и запустить:

```bash
systemctl disable telegram_bot.service
systemctl daemon-reload
systemctl enable molotok-bot.service
systemctl start molotok-bot.service
systemctl status molotok-bot.service
```

В статусе должно быть `active (running)`. Логи: `journalctl -u molotok-bot.service -f`.

### 7. Проверка

- В Telegram отправить боту `/start` — меню с кнопками.
- Отправить текст (как заказ) — подтверждение клиенту и сообщение в чат админа.
- На сервере: `ls /opt/molotok-bot/data` — после первого заказа появятся `orders.log` и `orders.db`.

### 8. (По желанию) Убрать старые файлы из /opt

После того как убедишься, что новый бот работает:

```bash
rm -f /opt/fixed_bot.py /opt/bot.py /opt/bot_backup.py /opt/simple_bot.py
rm -f /opt/.env
rm -rf /opt/venv
```

Папку `/opt/molotok-bot` и бэкап `/.opt_backup_*` не удалять.

---

## Часть 2. Нормализация — чтобы ничего друг другу не мешало (общая схема)

Цель: один понятный каталог под бота, один сервис systemd, свои порты/переменные у каждого приложения.

### 2.1. Единый каталог для бота

Рекомендуется держать проект в одном месте, например:

```bash
mkdir -p /opt/molotok-bot
```

Если бот уже был в другом месте (например в `/root/molotok_bot` или `/home/user/bot`):
- решите, где будет «официальная» копия (например `/opt/molotok-bot`);
- старый процесс остановите (см. ниже);
- дальше клонируйте/обновляйте код только в `/opt/molotok-bot`.

### 2.2. Остановить старые процессы бота

Если бот запускался вручную (screen/tmux или просто в консоли):

```bash
# Найти процесс
ps aux | grep -E 'molotok|main.py|molotok_bot'

# Остановить по PID (подставьте свой)
kill <PID>
# или жёстко, если не реагирует:
kill -9 <PID>
```

Если бот был добавлен как systemd-сервис:

```bash
sudo systemctl stop molotok-bot   # или как у вас называется сервис
sudo systemctl disable molotok-bot
```

Проверьте, что порты не заняты лишними процессами: `ss -tlnp`.

### 2.3. Другие приложения на сервере

Если кроме бота есть веб-сервер (nginx/apache), базы и т.д.:
- оставьте их в своих каталогах (`/var/www`, `/opt/...`);
- бота держите отдельно в `/opt/molotok-bot`;
- для бота не нужны порты (он сам ходит в Telegram), конфликтов по портам не будет.

### 2.4. Итог нормализации

- Один каталог проекта: `/opt/molotok-bot`.
- Один способ запуска: systemd (см. шаг 3.4).
- Секреты только в `.env` внутри `/opt/molotok-bot`, не в коде.

---

## Часть 3. Деплой с GitHub на сервер

### 3.1. Установить зависимости (один раз)

На сервере:

```bash
apt update
apt install -y git python3 python3-pip python3-venv
```

### 3.2. Клонировать или обновить репозиторий

**Если в `/opt/molotok-bot` ещё ничего нет:**

```bash
cd /opt
git clone https://github.com/AlexMuza/molotok-bot.git molotok-bot
cd molotok-bot
```

**Если репозиторий уже был клонирован (например старый состав файлов):**

```bash
cd /opt/molotok-bot
git fetch origin
git checkout main
git pull origin main
```

Если основная ветка на GitHub называется `master`:

```bash
git checkout master
git pull origin master
```

После этого в каталоге должны появиться: `main.py`, `config.py`, `bot.py`, папки `handlers/`, `storage/`, `requirements.txt`, `.env.example`.

### 3.3. Виртуальное окружение и .env

```bash
cd /opt/molotok-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создайте `.env` из шаблона и заполните (токен и ID админа):

```bash
cp .env.example .env
nano .env
```

В `.env` обязательно:
- `TELEGRAM_BOT_TOKEN=...`
- `ADMIN_CHAT_ID=...`

Сохраните (в nano: Ctrl+O, Enter, Ctrl+X).

### 3.4. Запуск через systemd (чтобы бот перезапускался после перезагрузки)

Создайте файл сервиса:

```bash
sudo nano /etc/systemd/system/molotok-bot.service
```

Содержимое (путь и пользователь при необходимости замените):

```ini
[Unit]
Description=Molotok Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/molotok-bot
Environment=PATH=/opt/molotok-bot/venv/bin
ExecStart=/opt/molotok-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Включите и запустите:

```bash
sudo systemctl daemon-reload
sudo systemctl enable molotok-bot
sudo systemctl start molotok-bot
sudo systemctl status molotok-bot
```

Логи в журнал systemd:

```bash
journalctl -u molotok-bot -f
```

### 3.5. Проверка

- В Telegram написать боту команду `/start` — должно прийти меню с кнопками.
- Отправить текст (как заказ) — должно прийти подтверждение, в чат админа (ADMIN_CHAT_ID) — уведомление о заказе.
- На сервере: `ls /opt/molotok-bot/data` — после первого заказа появятся `orders.log` и `orders.db`.

---

## Краткий чеклист

| Действие | Команда/шаг |
|----------|-------------|
| Подключиться | `ssh root@193.42.124.206` |
| Аудит | Запустить `scripts/audit-server.sh` или команды из раздела 1 |
| Остановить старый бот | `kill <PID>` или `systemctl stop ...` |
| Каталог проекта | `/opt/molotok-bot` |
| Код с GitHub | `git clone` или `git pull origin main` |
| Зависимости | `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt` |
| Секреты | `cp .env.example .env` и заполнить `.env` |
| Запуск | systemd `molotok-bot.service` |
| Логи | `journalctl -u molotok-bot -f` |

После этого на сервере всё нормализовано, бот работает из одной папки и не мешает другим процессам; обновления с GitHub подтягиваются через `git pull` и перезапуск сервиса.

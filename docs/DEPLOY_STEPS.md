# Перенос обновления Telegram-бота с GitHub на сервер — пошагово

Сервер: **193.42.124.206**. Выполняй шаги по порядку.

---

## Шаг 0 (на своём ПК). Убедиться, что новая версия на GitHub

На GitHub должны быть файлы: `main.py`, папки `handlers/`, `storage/`, `config.py`, `bot.py`.

1. Открой в браузере: https://github.com/AlexMuza/molotok-bot  
2. Посмотри список файлов. Если видишь только `molotok_bot.py`, `README.md`, `requirements.txt` — новой версии ещё нет.
3. Тогда на ПК открой терминал в папке проекта «молотокБот» и выполни (подставится твой логин/пароль или токен GitHub):

```bash
cd "путь\к\папке\молотокБот"
git push -u origin master
```

Если попросит логин — укажи свой GitHub-логин. Пароль: личный токен (Settings → Developer settings → Personal access tokens), не обычный пароль.  
После успешного пуша в репозитории появятся `main.py`, `handlers/`, `storage/` и т.д.

---

## Шаг 1. Подключиться к серверу

На ПК в терминале:

```bash
ssh root@193.42.124.206
```

Введи пароль. Дальше все команды — уже на сервере (приглашение будет `root@jxprmwsyxn:~#`).

---

## Шаг 2. Остановить старый бот

Скопируй и вставь в терминал, Enter:

```bash
systemctl stop telegram_bot.service
systemctl stop molotok-bot.service
systemctl disable molotok-bot.service
```

Проверь, что бот не крутится:

```bash
ps aux | grep -E 'fixed_bot|python.*bot' | grep -v grep
```

Пусто или только системные процессы — норма.

---

## Шаг 3. Сделать бэкап текущего /opt и .env

```bash
cp -a /opt /.opt_backup_$(date +%Y%m%d)
cp /opt/.env /root/molotok_env_backup.txt
```

Токен сохранён в `/root/molotok_env_backup.txt`.

---

## Шаг 4. Создать каталог и клонировать репозиторий с GitHub

```bash
mkdir -p /opt/molotok-bot
cd /opt/molotok-bot
git clone https://github.com/AlexMuza/molotok-bot.git .
```

Если появится ошибка `command not found: git`:

```bash
apt update && apt install -y git
```

и снова выполни блок из шага 4 (mkdir, cd, git clone).

Проверь, что появилась новая структура:

```bash
ls -la
ls handlers storage
```

Должны быть файлы: `main.py`, `config.py`, `bot.py`, папки `handlers/`, `storage/`. Если их нет — на GitHub старая версия, вернись к шагу 0 и сделай push с ПК. Если ветка на GitHub называется `main`, а клонировалось что-то другое:

```bash
git checkout main
```

---

## Шаг 5. Перенести и проверить .env

```bash
cp /opt/.env /opt/molotok-bot/.env
cat /opt/molotok-bot/.env
```

В файле должны быть две строки (подставь свои значения):

```
TELEGRAM_BOT_TOKEN=твой_токен_от_BotFather
ADMIN_CHAT_ID=твой_telegram_id
```

Если `ADMIN_CHAT_ID` нет — добавь вручную:

```bash
nano /opt/molotok-bot/.env
```

Допиши строку `ADMIN_CHAT_ID=число`, сохрани: Ctrl+O, Enter, Ctrl+X. Узнать свой ID: напиши боту @userinfobot в Telegram.

---

## Шаг 6. Виртуальное окружение и зависимости

```bash
cd /opt/molotok-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

Ошибок быть не должно. Если `pip install` ругается — пришли вывод.

---

## Шаг 7. Настроить systemd и запустить бота

Создать файл сервиса:

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

Отключить старый сервис, включить новый и запустить:

```bash
systemctl disable telegram_bot.service
systemctl daemon-reload
systemctl enable molotok-bot.service
systemctl start molotok-bot.service
systemctl status molotok-bot.service
```

В выводе `status` должно быть: **Active: active (running)**. Если есть красная строка **failed** — смотри логи:

```bash
journalctl -u molotok-bot.service -n 50 --no-pager
```

---

## Шаг 8. Проверить бота в Telegram

1. Открой бота в Telegram и отправь **/start** — должно прийти меню с кнопками (Каталог, Заказ, Контакты).
2. Нажми «Заказ» и отправь любой текст (например: «Тест заказа, +79001234567») — должно прийти «Заказ принят!», а тебе в личку (если ADMIN_CHAT_ID твой) — сообщение о новом заказе.
3. На сервере проверь логи заказов:

```bash
ls -la /opt/molotok-bot/data
```

После первого заказа появятся `orders.log` и `orders.db`.

---

## Шаг 9 (по желанию). Удалить старые файлы из /opt

Когда убедишься, что бот работает, можно убрать старый код из `/opt`, чтобы не путаться:

```bash
rm -f /opt/fixed_bot.py /opt/bot.py /opt/bot_backup.py /opt/simple_bot.py
rm -f /opt/.env
rm -rf /opt/venv
```

Папку `/opt/molotok-bot` не трогай — там рабочий бот.

---

## Полезные команды после деплоя

| Действие | Команда |
|----------|---------|
| Логи бота в реальном времени | `journalctl -u molotok-bot.service -f` |
| Статус сервиса | `systemctl status molotok-bot.service` |
| Перезапустить бота | `systemctl restart molotok-bot.service` |
| Обновить код с GitHub | `cd /opt/molotok-bot && git pull origin main` (или `master`), затем `systemctl restart molotok-bot.service` |

Готово. Бот работает из `/opt/molotok-bot`, обновления подтягиваешь с GitHub через `git pull` и перезапуск сервиса.

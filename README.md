# Внимание

- Чат бот не может писать незнакомым людям, для регистрации достаточно написать `/start` в личные сообщения чат-бота.
- Все команды, кроме `/start`, работают только в общих чатах.

# Команды

- `/start` - Начать работу.
- `/help` - Получить список команд.
- `/get_timezone` - Получить часовой пояс.
- `/set_timezone <часовой пояс>` - Установить часовой пояс (см. [доступные пояса](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones))
- `/get_meetings` - Получить список встреч.
- `/create_meeting <ID> <название> <дд.мм.гг или today/сегодня> <чч:мм> <опц. участники...>` - Создать втречу.
- `/remove_meetings <список ID...>` - Отменить встречу.

# Зависимости

- [selenium](https://selenium-python.readthedocs.io)
- [python-telegram-bot-api](https://github.com/python-telegram-bot/python-telegram-bot)

# Пример использования

## Создание

ЛС:

```
$ /start
Теперь чат-бот может уведомлять вас о встречах.
```

В чате:

```
$ /create_meeting sozvon Общее_Собрание today 13:00 @example_user
До втречи осталось 1 часов 2 минут 3 секунд.
```

## Удаление

```
$ /remove_meetings sozvon
```

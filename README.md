# onec-fetch

Аналог fastfetch на языке 1С: ASCII-логотип, цвета, ОС, CPU, память, uptime и рабочий стол.

Логотип выбирается по ОС и дистрибутиву автоматически: 77 вариантов из [fastfetch](https://github.com/fastfetch-cli/fastfetch), включая компактные.

## Быстрый запуск

- **Linux x64:** откройте терминал в папке и выполните `./onec-fetch`.
- **Windows x64:** дважды нажмите `onec-fetch.cmd` — окно останется открытым.

```sh
./onec-fetch --no-color    # без цветов
./onec-fetch --no-logo     # без логотипа
./onec-fetch --json        # JSON
./onec-fetch --logo=1c     # логотип 1С
./onec-fetch --logo=ubuntu # выбрать логотип
./onec-fetch --list-logos  # список логотипов
```

В Windows используйте те же параметры с `onec-fetch.cmd`. Linux проверен; Windows-сборка пока без проверки запуском. Нужны стандартные системные библиотеки ОС. GPU определяется только в Windows; диски не выводятся.

Исходник: `onec-fetch.os` (запуск через `oscript onec-fetch.os`). Рядом со скриптом должен находиться каталог `assets`; без него используется логотип 1С. Модуль для 1С:Предприятия и инструкция — в [docs](docs/1c.md). Переносимые архивы собираются командой `python3 scripts/package.py`.

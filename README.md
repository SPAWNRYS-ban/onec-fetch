# onec-fetch

Аналог fastfetch на языке 1С: ASCII-логотип, цвета, ОС, CPU, память, uptime и рабочий стол.

## Быстрый запуск

Скачай архив своей ОС в [Releases](https://github.com/SPAWNRYS-ban/onec-fetch/releases/latest) и распакуй. **OneScript и .NET уже внутри — отдельно ставить их не нужно.**

- **Linux x64:** открой терминал в папке и выполни `./onec-fetch`.
- **Windows x64:** дважды нажми `onec-fetch.cmd` — окно останется открытым.

```sh
./onec-fetch --no-color    # без цветов
./onec-fetch --no-logo     # без логотипа
./onec-fetch --json        # JSON
```

В Windows используй те же параметры с `onec-fetch.cmd`. Linux проверен; Windows-сборка пока без проверки запуском. Нужны стандартные системные библиотеки ОС. GPU определяется только в Windows; диски не выводятся.

Исходник: `onec-fetch.os` (запуск через `oscript onec-fetch.os`). Модуль для 1С:Предприятия и инструкция — в [docs](docs/1c.md). Переносимые архивы собираются командой `python3 scripts/package.py`.

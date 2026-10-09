> [!WARNING]
> Программа является нейрослопом написанным с использование ChatGPT 6.1 Sol <br>
> (Да нейросети умеют писать на 1С, не спрашивайте)

# onec-fetch

<img width="1016" height="665" alt="изображение" src="https://github.com/user-attachments/assets/6b5d199c-a9d4-4682-b2d6-e0053ef7ee1a" />

Аналог fastfetch на языке 1С / OneScript: системная сводка, 77 ASCII-логотипов и реестр всех 76 модулей fastfetch 2.69.0.

## Запуск

Готовые сборки и пакеты `.pkg.tar.zst` / `.deb`: [Releases](https://github.com/SPAWNRYS-ban/onec-fetch/releases/latest). [Установка пакетов](docs/packages.md).

- **Linux x64:** откройте терминал в папке и выполните `./onec-fetch`.
- **Windows x64:** дважды нажмите `onec-fetch.cmd` — окно останется открытым.

```sh
./onec-fetch                      # обычная сводка
./onec-fetch --all --debug        # все модули и причины недоступности
./onec-fetch -s CPU:GPU:Memory    # выбранные модули
./onec-fetch -c config/example.jsonc
./onec-fetch --json               # данные, статусы и источники
./onec-fetch --logo=ubuntu        # выбранный логотип; auto — по ОС
./onec-fetch --no-color --no-logo
./onec-fetch --list-modules       # список модулей
./onec-fetch --list-logos         # список логотипов
```

В Windows используйте те же параметры с `onec-fetch.cmd`. Linux проверен на Arch/KDE/Wayland; Windows-сборка требует проверки на Windows. Дополнительные аппаратные/API-модули используют доступные системные утилиты и права; регистрация 76 модулей не означает полный паритет всех полей fastfetch. macOS/BSD пока имеют только общие модули. Подробности: [модули и ограничения](docs/modules.md), [конфигурация и JSON](docs/configuration.md).

Исходники запускаются через `oscript onec-fetch.os`; рядом необходим каталог `lib`, для логотипов — `assets`, для Windows API — `helpers`. Готовые архивы собираются командой `python3 scripts/package.py`. Отдельный исходник формы для 1С:Предприятия: [инструкция](docs/1c.md).

Логотипы, реестр и отдельные алгоритмы адаптированы из [fastfetch](https://github.com/fastfetch-cli/fastfetch) под MIT; уведомления находятся в [licenses](licenses/README.md).

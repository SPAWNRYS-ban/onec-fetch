# Системные пакеты Linux

Готовые пакеты x86_64 находятся в [Releases](https://github.com/SPAWNRYS-ban/onec-fetch/releases/latest). Они устанавливают команду `onec-fetch`, исходники и отдельный встроенный runtime в `/opt/onec-fetch`. Системные OneScript/.NET не требуются. Системные библиотеки и основные утилиты задаются зависимостями пакета.

## Arch и производные

Установите скачанный файл:

```sh
sudo pacman -U ./onec-fetch-2.0.0-1-x86_64.pkg.tar.zst
onec-fetch
```

PKGBUILD и `.SRCINFO` находятся в [`packaging/arch`](../packaging/arch). Для самостоятельной сборки выполните `makepkg -si` в этой папке. Рецепт использует опубликованный Linux-архив и проверяет SHA256; ELF/.NET-файлы не проходят strip. Пакет не опубликован в AUR и не требует стороннего pacman-репозитория.

## Debian, Ubuntu и производные

Установите скачанный файл через APT, чтобы разрешить зависимости:

```sh
sudo apt install ./onec-fetch_2.0.0-1_amd64.deb
onec-fetch
```

Целевые версии: Debian 12/13, Ubuntu 22.04/24.04/26.04 и совместимые производные на amd64. В зависимости указаны альтернативы ICU/OpenSSL для этих выпусков. Поддержка старых выпусков с OpenSSL 1.1 не заявляется. Список библиотек согласован с [зависимостями .NET 8](https://github.com/dotnet/core/blob/main/release-notes/8.0/os-packages.md); Arch — с [пакетом runtime 8](https://archlinux.org/packages/extra/x86_64/dotnet-runtime-8.0/).

## Использование и удаление

```sh
onec-fetch --all --debug
onec-fetch -s CPU:GPU:Memory
onec-fetch --json
man onec-fetch
```

Пример настройки: `/opt/onec-fetch/config/example.jsonc`. Параметры и причины недоступности модулей описаны в [конфигурации](configuration.md) и [матрице модулей](modules.md). Дополнительные утилиты для графических API, медиа, Bluetooth и аппаратных сведений остаются необязательными.

Удаление: `sudo pacman -R onec-fetch` или `sudo apt remove onec-fetch`.

## Сборка

```sh
python3 scripts/package_linux.py           # оба формата
python3 scripts/package_linux.py --format=arch
python3 scripts/package_linux.py --format=deb
python3 tests/test_linux_packages.py
```

Нужны `makepkg`/`fakeroot`/`zstd` для Arch и `dpkg-deb` для Debian. Сборщик использует опубликованный архив с закреплённой контрольной суммой и сохраняет результаты в `outputs/`. Архив берётся локально или загружается из релиза; отдельный runtime повторно не собирается.

Проверка пакетов включает метаданные, root-владельцев `.deb`, зависимости, сохранность всех runtime-файлов и запуск реального установленного пути `/opt/onec-fetch` в изолированном пространстве монтирования. Проверены установка и удаление через pacman с копией метаданных зависимостей в отдельном корне. В изолированных Debian 12 и Ubuntu 24.04 прошли `apt install` с разрешением зависимостей, запуск встроенного runtime, сбор OS/CPU/RAM/Packages и удаление пакета. Эти проверки не изменяют установленные пакеты основной ОС. Debian 13 и Ubuntu 22.04/26.04 пока являются целевыми версиями по зависимостям, без отдельного прогона.

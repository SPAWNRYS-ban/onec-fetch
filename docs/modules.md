# Модули и ограничения

Реестр включает все **76 модулей fastfetch 2.69.0**. У каждого есть сборщик или явно описанный статус. Полный паритет всех полей и платформ ещё не достигнут. Сверка реестра: [upstream schema](https://github.com/fastfetch-cli/fastfetch/blob/1e0ec1004a8a4c4410163b146db27b8c163bf1f6/doc/json_schema.json), commit `1e0ec1004a8a4c4410163b146db27b8c163bf1f6`.

Основная логика выполняется на языке 1С. Linux проверен на Arch/KDE/Wayland с Ryzen 5 5500 и GTX 1050 Ti. Windows-провайдеры написаны, синтаксис PowerShell и встроенный C# проверены; запуск Windows API не проверен. macOS/BSD пока имеют общие модули; остальные возвращают unsupported. Часть Linux fallback для других дистрибутивов и окружений тоже требует проверки на соответствующих системах.

Обычный профиль соответствует основным строкам приведённой сводки fastfetch: пакеты, дисплеи, DE/WM и оформление, CPU/GPU, RAM/swap, диски, IP и локаль. Исполнитель дополнительно показывает OneScript и onec-fetch. Названия модулей в CLI сохраняют английские идентификаторы fastfetch, подписи вывода русские.

В таблице перечислены реально реализованные источники и текущие ограничения. «output» означает сырой текст в JSON, а не полный разбор каждого поля. Необязательная утилита не включена в архив; при её отсутствии возвращается unavailable. Ограничение прав не обходится повышением привилегий.

| Модуль | Linux | Windows | Ограничение |
|---|---|---|---|
| `Battery` | power_supply sysfs | Win32_Battery | Linux базовые энергия/заряд/мощность при наличии; Windows адаптер имеет только сведения батареи, watts=null |
| `BIOS` | DMI sysfs | WMI: ComputerSystem/BaseBoard/BIOS/SystemEnclosure | Доступные базовые поля; OEM-заглушки Linux очищаются |
| `Bluetooth` | bluetoothctl Connected/list | PNP Bluetooth | Linux строки; Windows present/paired не доказывает Connected, сведения подключения пока неполные |
| `BluetoothRadio` | bluetoothctl Connected/list | PNP Bluetooth | Linux строки; Windows present/paired не доказывает Connected, сведения подключения пока неполные |
| `Board` | DMI sysfs | WMI: ComputerSystem/BaseBoard/BIOS/SystemEnclosure | Доступные базовые поля; OEM-заглушки Linux очищаются |
| `Bootmgr` | bootctl status | bcdedit current | Сырой output, возможен отказ доступа; установленный загрузчик не выдаётся за активный |
| `Break` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `Brightness` | backlight sysfs → ddcutil | WmiMonitorBrightness | DDC/внешние экраны зависят от прав; Linux DDC пока output |
| `Btrfs` | btrfs filesystem show / zpool list | unsupported | Сырой output; нужны утилиты и доступ |
| `Camera` | V4L2 sysfs | PNP Camera | Перечисление без съёмки; режимы/разрешения пока нет |
| `Chassis` | DMI sysfs | WMI: ComputerSystem/BaseBoard/BIOS/SystemEnclosure | Доступные базовые поля; OEM-заглушки Linux очищаются |
| `Codec` | vainfo → vdpauinfo | vainfo при наличии | Сырой API-output; без подходящего провайдера unavailable |
| `Colors` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `Command` | OneScript Process + /bin/sh | OneScript Process + cmd.exe | Только явно заданная команда; timeout и остановка дерева |
| `CPU` | cpuinfo, cpufreq, hwmon | Win32_Processor | Физические/логические ядра и частоты; температура зависит от датчика |
| `CPUCache` | sysfs + shared_cpu_list | Win32_CacheMemory | Linux устраняет повторы; Windows WMI может не раскрывать все кеши |
| `CPUUsage` | Два общих снимка /proc | Win32_PerfFormattedData | Linux: один interval; Top — CPU и RSS, без отдельной сортировки по RAM/IO |
| `Cursor` | KDE/GTK config + gsettings | Реестр оформления/шрифтов/курсора | Не все Qt/GTK версии и динамические переопределения; Windows Icons unavailable |
| `Custom` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `DateTime` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `DE` | XDG_CURRENT_DESKTOP; версии KDE/GNOME/Xfce | Windows Desktop | Дополнительные DE без собственного version-провайдера |
| `Disk` | df -l -B1 | Win32_LogicalDisk | Linux локальные тома, включая /boot; free отдельно пока нет; bind одного источника не дублируется |
| `DiskIO` | Два общих снимка /proc | Win32_PerfFormattedData | Linux: один interval; Top — CPU и RSS, без отдельной сортировки по RAM/IO |
| `Display` | KScreen JSON → wlr-randr → xrandr; EDID | EnumDisplayDevices/EnumDisplaySettings | Текущий режим; Linux KScreen — scale/диагональ/HDR/предпочитаемые ID; Windows без HDR/scale/EDID |
| `DNS` | resolvectl → resolv.conf | Get-DnsClientServerAddress | resolvectl пока output; resolv.conf может содержать локальный stub |
| `Editor` | VISUAL → EDITOR | То же через адаптер | Команда редактора, без определения версии |
| `Font` | KDE/GTK config + gsettings | Реестр оформления/шрифтов/курсора | Не все Qt/GTK версии и динамические переопределения; Windows Icons unavailable |
| `Gamepad` | /proc/bus/input/devices | WMI/PNP | Метаданные, без чтения ввода; Windows Gamepad — фильтр имени HID |
| `GPU` | lspci + PCI sysfs; nvidia-smi | Win32_VideoController | VRAM/нагрузка/температура на Linux для NVIDIA при доступе; тип остальных неизвестен; WMI VRAM не используется |
| `Host` | DMI sysfs | WMI: ComputerSystem/BaseBoard/BIOS/SystemEnclosure | Доступные базовые поля; OEM-заглушки Linux очищаются |
| `Icons` | KDE/GTK config + gsettings | Реестр оформления/шрифтов/курсора | Не все Qt/GTK версии и динамические переопределения; Windows Icons unavailable |
| `InitSystem` | PID 1 + --version | unsupported | Только применимый Unix модуль |
| `Kernel` | /proc/sys/kernel + uname | Win32_OperatingSystem | Имя, release, архитектура |
| `Keyboard` | /proc/bus/input/devices | WMI/PNP | Метаданные, без чтения ввода; Windows Gamepad — фильтр имени HID |
| `LM` | systemctl show display-manager | Winlogon | Linux сырой output, без версии LM |
| `Loadavg` | /proc/loadavg | unsupported | Средние за 1/5/15 минут; не подменяется загрузкой CPU |
| `Locale` | LC_ALL → LC_CTYPE → LANG | Окружение процесса | При отсутствии переменных — C; отдельного Windows culture API пока нет |
| `LocalIp` | ip JSON + default route | Get-NetIPConfiguration | Linux JSON хранит все интерфейсы; обычный вывод — IPv4 default route |
| `Logo` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `Media` | MPRIS через qdbus6/qdbus → playerctl | WinRT media session | Linux все обнаруженные сеансы, включая paused; без позиции; Windows текущий сеанс |
| `Memory` | meminfo, поправка ZFS ARC | Win32_OperatingSystem | Linux использует MemAvailable с fallback; вычисления на 1С |
| `Monitor` | KScreen JSON → wlr-randr → xrandr; EDID | EnumDisplayDevices/EnumDisplaySettings | Текущий режим; Linux KScreen — scale/диагональ/HDR/предпочитаемые ID; Windows без HDR/scale/EDID |
| `Mouse` | /proc/bus/input/devices | WMI/PNP | Метаданные, без чтения ввода; Windows Gamepad — фильтр имени HID |
| `NetIO` | Два общих снимка /proc | Win32_PerfFormattedData | Linux: один interval; Top — CPU и RSS, без отдельной сортировки по RAM/IO |
| `OpenCL` | clinfo --raw | clinfo при наличии | Linux список устройств/API; ICD без платформ не означает поддержку GPU |
| `OpenGL` | glxinfo -B → eglinfo -B | glinfo при наличии | Версия/renderer из реального API, не из названия GPU; EGL fallback частичный |
| `OS` | os-release + uname | Win32_OperatingSystem | Базовые имя/ID/версия/архитектура; не все варианты ОС |
| `Packages` | Базы pacman/dpkg/apk; rpm, xbps-query, nix-env, flatpak, snap | Uninstall registry + Appx | Nix — текущий профиль, без всей NixOS; Windows списки могут пересекаться, общий итог не суммируется |
| `PhysicalDisk` | lsblk JSON | Win32_DiskDrive | Модель/размер/тип; SMART/NVMe health пока нет |
| `PhysicalMemory` | dmidecode --type 17 | Win32_PhysicalMemory | Linux пока сырой output; обычно нужны права |
| `Player` | MPRIS через qdbus6/qdbus → playerctl | WinRT media session | Linux все обнаруженные сеансы, включая paused; без позиции; Windows текущий сеанс |
| `PowerAdapter` | power_supply sysfs | Win32_Battery | Linux базовые энергия/заряд/мощность при наличии; Windows адаптер имеет только сведения батареи, watts=null |
| `Processes` | /proc status | Win32_Process | Количество процессов и потоков |
| `PublicIp` | HTTP OneScript: ipify/wttr.in | Тот же HTTP-сборщик | Только явное allowNetwork; внешние сервисы не проверены в приёмочном прогоне |
| `Separator` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `Shell` | Цепочка родительских процессов; shell --version | Win32_Process + версия EXE | Shell fallback из SHELL; результат зависит от настоящего контекста запуска |
| `Sound` | pactl JSON: PipeWire/PulseAudio | Core Audio | Windows только default endpoint volume/mute, без полного списка/описаний |
| `Swap` | meminfo + /proc/swaps | Win32_PageFileUsage | Общий объём/занято и отдельные устройства |
| `Terminal` | Цепочка родительских процессов; shell --version | Win32_Process + версия EXE | Shell fallback из SHELL; результат зависит от настоящего контекста запуска |
| `TerminalFont` | Файлы профиля Konsole/kitty | unavailable | Linux ограничен профилем по умолчанию; встроенный/изменённый профиль может быть недоступен |
| `TerminalSize` | stty /dev/tty | Console API | Без TTY unavailable; пиксельный размер пока нет |
| `TerminalTheme` | Файлы профиля Konsole/kitty | unavailable | Linux ограничен профилем по умолчанию; встроенный/изменённый профиль может быть недоступен |
| `Theme` | KDE/GTK config + gsettings | Реестр оформления/шрифтов/курсора | Не все Qt/GTK версии и динамические переопределения; Windows Icons unavailable |
| `Title` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `Top` | Два общих снимка /proc | Win32_PerfFormattedData | Linux: один interval; Top — CPU и RSS, без отдельной сортировки по RAM/IO |
| `TPM` | tpm2_getcap → версия из sysfs | Win32_Tpm | Linux sysfs fallback не раскрывает производителя; tpm2_getcap пока output |
| `Uptime` | /proc/uptime | GetTickCount64 | Секунды; Windows через API-адаптер |
| `Users` | who | quser | Сырой output активных сеансов |
| `Version` | OneScript, ANSI, конфигурация | Тот же движок | Logo отдаёт выбор; Version — версию onec-fetch/OneScript |
| `Vulkan` | vulkaninfo --summary | vulkaninfo при наличии | Linux instanceVersion и API каждого устройства; Windows пока output |
| `Wallpaper` | Plasma config → GNOME gsettings | Control Panel/Desktop | Статические настройки; профиль может отличаться от активного |
| `Weather` | HTTP OneScript: ipify/wttr.in | Тот же HTTP-сборщик | Только явное allowNetwork; внешние сервисы не проверены в приёмочном прогоне |
| `Wifi` | nmcli, только активные сети, без рескана | netsh wlan show interfaces | Пока строки источника вместо единой структуры; Windows локализованный output |
| `WM` | Список процессов + версия WM | DWM | Обнаружение процесса; несколько графических сеансов не полностью разделены |
| `WMTheme` | KWin config | Реестр Personalize | Linux пока только KWin |
| `Zpool` | btrfs filesystem show / zpool list | unsupported | Сырой output; нужны утилиты и доступ |

## Приёмочная проверка

Проверены реестр 76 модулей, реальные локальные источники, общий интервал CPU/IO/Top, JSONC и форматы, явное включение Command/сети, timeout дерева процессов, ограничение stdout/stderr, буквальная передача аргументов и все 77 логотипов. Интеграционная сверка с fastfetch проверяет OS/ядро/модель CPU и топологию, частоты, память/swap, пакеты, дисплей и диски. Нагрузки и свободная память могут меняться между запусками.

В настоящем Konsole совпали shell, terminal, locale и размер TTY. Код и переносимый Linux-архив запускаются из другого рабочего каталога, включая путь с пробелами и кириллицей, без установленного oscript. Структура Windows-архива и контрольные суммы проверяются отдельно; это не заменяет запуск на Windows.

Непроверенные источники и ограничения в таблице сохраняются после успешного Linux-прогона. Для сравнения на Вашей машине используйте `--all --json` и `--all --debug`; подробности схемы и настроек находятся в [configuration.md](configuration.md).

// Windows: WMI на языке 1С, системный PowerShell только для низкоуровневых API.
Перем Настройки;

Процедура Начать(Параметры) Экспорт
    Настройки = Параметры;
КонецПроцедуры

Функция WMI(Класс, Поля, Пространство = "root\cimv2")
    Локатор = Новый COMОбъект("WbemScripting.SWbemLocator");
    Служба = Локатор.ConnectServer(".", Пространство);
    Результат = Новый Массив;
    Для Каждого Запись Из Служба.ExecQuery("SELECT " + Поля + " FROM " + Класс) Цикл
        Объект = Новый Структура;
        Для Каждого Поле Из СтрРазделить(Поля, ",") Цикл
            Поле = СокрЛП(Поле); Значение = Запись.Properties_.Item(Поле).Value;
            Если Значение = Неопределено Тогда Значение = Неопределено; КонецЕсли;
            Объект.Вставить(Поле, Значение);
        КонецЦикла;
        Результат.Добавить(Объект);
    КонецЦикла;
    Возврат Результат;
КонецФункции

Функция Собрать(Модуль) Экспорт
    Если Модуль = "OS" Или Модуль = "Kernel" Тогда
        Данные = WMI("Win32_OperatingSystem", "Caption,Version,BuildNumber,OSArchitecture");
        Если Данные.Количество() = 0 Тогда Возврат Core.Нет("OS WMI пуст", "WMI"); КонецЕсли;
        ОС = Данные[0];
        Возврат Core.Успех(Новый Структура("name,version,build,architecture,id,idLike", ОС.Caption, ОС.Version, ОС.BuildNumber, ОС.OSArchitecture, "windows", ""), ?(Модуль = "OS", ОС.Caption + " " + ОС.OSArchitecture, "Windows NT " + ОС.Version), "Win32_OperatingSystem");
    ИначеЕсли Модуль = "CPU" Тогда
        Записи = WMI("Win32_Processor", "Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed");
        Ядра = 0; Потоки = 0; Частота = 0; Имя = ""; Vendor = "";
        Для Каждого ЦП Из Записи Цикл
            Имя = СокрЛП(ЦП.Name); Vendor = ЦП.Manufacturer; Ядра = Ядра + ЦП.NumberOfCores; Потоки = Потоки + ЦП.NumberOfLogicalProcessors; Частота = Макс(Частота, ЦП.MaxClockSpeed * 1000000);
        КонецЦикла;
        Возврат Core.Успех(Новый Структура("name,vendor,physicalCores,logicalCores,maxFrequency", Имя, Vendor, Ядра, Потоки, Частота), Имя + " (" + Core.ФорматЧисла(Потоки) + ") @ " + Core.ФорматЧисла(Частота / 1000000000, 2) + " GHz", "Win32_Processor");
    ИначеЕсли Модуль = "Memory" Тогда
        Записи = WMI("Win32_OperatingSystem", "TotalVisibleMemorySize,FreePhysicalMemory");
        Всего = Число(Записи[0].TotalVisibleMemorySize) * 1024; Свободно = Число(Записи[0].FreePhysicalMemory) * 1024;
        Возврат Core.Успех(Новый Структура("total,available,used,percentage", Всего, Свободно, Всего - Свободно, Core.Процент(Всего - Свободно, Всего)), Core.Размеры(Всего - Свободно, Всего), "Win32_OperatingSystem");
    ИначеЕсли Модуль = "Swap" Тогда
        Записи = WMI("Win32_PageFileUsage", "Name,AllocatedBaseSize,CurrentUsage,PeakUsage"); Всего = 0; Занято = 0;
        Для Каждого Запись Из Записи Цикл Всего = Всего + Запись.AllocatedBaseSize * 1048576; Занято = Занято + Запись.CurrentUsage * 1048576; КонецЦикла;
        Возврат Core.Успех(Новый Структура("total,used,percentage,devices", Всего, Занято, Core.Процент(Занято, Всего), Записи), Core.Размеры(Занято, Всего), "Win32_PageFileUsage");
    ИначеЕсли Модуль = "Disk" Тогда
        Записи = WMI("Win32_LogicalDisk", "DeviceID,DriveType,FileSystem,Size,FreeSpace,VolumeName"); Данные = Новый Массив; Линии = Новый Массив;
        Для Каждого Запись Из Записи Цикл
            Если Запись.Size = Неопределено Или Запись.DriveType <> 3 Тогда Продолжить; КонецЕсли;
            Всего = Число(Запись.Size); Свободно = Число(Запись.FreeSpace);
            Данные.Добавить(Новый Структура("mountpoint,filesystem,total,used,available,percentage", Запись.DeviceID, Запись.FileSystem, Всего, Всего - Свободно, Свободно, Core.Процент(Всего - Свободно, Всего)));
            Линии.Добавить(Запись.DeviceID + ": " + Core.Размеры(Всего - Свободно, Всего) + " — " + Запись.FileSystem);
        КонецЦикла;
        Возврат Core.Успех(Данные, Линии, "Win32_LogicalDisk");
    ИначеЕсли Модуль = "GPU" Тогда
        Данные = WMI("Win32_VideoController", "Name,AdapterCompatibility,DriverVersion,PNPDeviceID,VideoProcessor"); Линии = Новый Массив;
        Для Каждого Запись Из Данные Цикл Линии.Добавить(Запись.Name); КонецЦикла;
        // AdapterRAM намеренно не используется: WMI может обрезать VRAM до 32 бит.
        Возврат Core.Успех(Данные, Линии, "Win32_VideoController (VRAM not inferred)");
    ИначеЕсли Модуль = "Host" Тогда Класс = "Win32_ComputerSystem"; Поля = "Manufacturer,Model";
    ИначеЕсли Модуль = "Board" Тогда Класс = "Win32_BaseBoard"; Поля = "Manufacturer,Product,Version";
    ИначеЕсли Модуль = "BIOS" Тогда Класс = "Win32_BIOS"; Поля = "Manufacturer,SMBIOSBIOSVersion,ReleaseDate";
    ИначеЕсли Модуль = "Chassis" Тогда Класс = "Win32_SystemEnclosure"; Поля = "Manufacturer,Model,ChassisTypes";
    ИначеЕсли Модуль = "PhysicalDisk" Тогда Класс = "Win32_DiskDrive"; Поля = "Model,Size,InterfaceType,MediaType";
    ИначеЕсли Модуль = "PhysicalMemory" Тогда Класс = "Win32_PhysicalMemory"; Поля = "Manufacturer,Capacity,Speed,DeviceLocator,PartNumber,SMBIOSMemoryType";
    ИначеЕсли Модуль = "Battery" Тогда Класс = "Win32_Battery"; Поля = "Name,EstimatedChargeRemaining,BatteryStatus,EstimatedRunTime";
    ИначеЕсли Модуль = "Processes" Тогда
        Данные = WMI("Win32_Process", "ProcessId,ThreadCount"); Потоки = 0; Для Каждого Запись Из Данные Цикл Потоки = Потоки + Запись.ThreadCount; КонецЦикла;
        Возврат Core.Успех(Новый Структура("processes,threads", Данные.Количество(), Потоки), Core.ФорматЧисла(Данные.Количество()) + " процессов", "Win32_Process");
    ИначеЕсли Модуль = "Uptime" Тогда
        Возврат СистемныйAPI(Модуль);
    ИначеЕсли Модуль = "Loadavg" Или Модуль = "Btrfs" Или Модуль = "Zpool" Или Модуль = "InitSystem" Тогда
        Возврат Core.Нет("Linux/Unix модуль неприменим к обычной Windows", Модуль, "unsupported");
    Иначе Возврат СистемныйAPI(Модуль); КонецЕсли;
    Данные = WMI(Класс, Поля); Линии = Новый Массив;
    Для Каждого Запись Из Данные Цикл
        Текст = "";
        Для Каждого Поле Из Запись Цикл
            Если Поле.Значение <> Неопределено И ТипЗнч(Поле.Значение) <> Тип("Массив") Тогда Текст = Текст + ?(Текст = "", "", " ") + Строка(Поле.Значение); КонецЕсли;
        КонецЦикла;
        Линии.Добавить(Текст);
    КонецЦикла;
    Возврат Core.Успех(Данные, Линии, Класс);
КонецФункции

Функция СистемныйAPI(Модуль)
    Путь = Core.Значение(Настройки, "root") + "/helpers/windows.ps1";
    Аргументы = Core.Арги("-NoLogo|-NoProfile|-NonInteractive|-ExecutionPolicy|Bypass|-File|" + Путь + "|-Module|" + Модуль + "|-ParentPid|" + Core.ФорматЧисла(ТекущийПроцесс().Идентификатор));
    Р = Core.Команда("powershell.exe", Аргументы);
    Если Р.status <> "ok" Тогда Возврат Core.ИзКоманды(Р); КонецЕсли;
    Ответ = Core.JSON(Р.stdout);
    Если Ответ.status <> "ok" Тогда Возврат Core.Нет(Core.Значение(Ответ, "error"), "Windows API", Ответ.status); КонецЕсли;
    Данные = Ответ.data; Линии = Core.Значение(Ответ, "display", "");
    Если Модуль = "Uptime" Тогда
        Секунды = Данные.milliseconds / 1000;
        Данные = Новый Структура("seconds", Секунды); Линии = Core.Время(Секунды);
    ИначеЕсли Модуль = "Packages" Тогда
        Счетчики = Новый Структура("registry,appx", Данные.programs.Количество(), Данные.appx.Количество());
        Линии = Core.ФорматЧисла(Счетчики.registry) + " (uninstall registry), " + Core.ФорматЧисла(Счетчики.appx) + " (Appx)";
        Данные = Новый Структура("managers,programs,appx", Счетчики, Данные.programs, Данные.appx);
    ИначеЕсли Модуль = "Display" Или Модуль = "Monitor" Тогда
        Линии = Новый Массив;
        Для Каждого Экран Из Данные Цикл Линии.Добавить(Экран.name + ": " + Core.ФорматЧисла(Экран.width) + "x" + Core.ФорматЧисла(Экран.height) + ", " + Core.ФорматЧисла(Экран.refreshRate, 2) + " Hz"); КонецЦикла;
    ИначеЕсли Модуль = "Sound" Тогда
        Линии = Core.ФорматЧисла(Данные.volumeScalar * 100) + "%" + ?(Данные.mute, " (mute)", "");
    ИначеЕсли Модуль = "LocalIp" Тогда
        Линии = Новый Массив;
        Для Каждого Адаптер Из Данные Цикл
            Для Каждого Адрес Из Адаптер.ipv4 Цикл Линии.Добавить(Адаптер.name + ": " + Адрес.IPAddress + "/" + Core.ФорматЧисла(Адрес.PrefixLength)); КонецЦикла;
        КонецЦикла;
    КонецЕсли;
    Если Линии = "" Тогда Линии = Core.ВJSON(Данные); КонецЕсли;
    Возврат Core.Успех(Данные, Линии, Core.Значение(Ответ, "source", "Windows API"));
КонецФункции

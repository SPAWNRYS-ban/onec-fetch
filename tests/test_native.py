"""Native JSONC/text correctness, lazy loading and cached script instances."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = sys.argv[1] if len(sys.argv) > 1 else 'oscript'


def run(script, *args):
    result = subprocess.run([ENGINE, str(script), *args], cwd='/tmp',
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0 and not result.stderr, (result.stdout, result.stderr)
    return result.stdout


with tempfile.TemporaryDirectory(prefix='onec-fetch native проверка ') as directory:
    folder = Path(directory)
    shutil.copytree(ROOT / 'lib', folder / 'lib')
    cases = []
    for text in ('https://example.test/* */', ',}', ',]', 'quote " and \\',
                 '\\"//literal', 'Русский текст 😀', '\r\n\t', ''):
        expected = {'text': text, 'items': [1, {'value': text}, None, True]}
        encoded = json.dumps(expected, ensure_ascii=False)
        # Add a comment and trailing commas at known structural positions,
        # without rewriting any quoted content.
        jsonc = '// leading comment\r\n' + encoded[:-1] + ', /* end */ }\n// eof'
        cases.append({'input': jsonc, 'expected': expected})
    cases.extend([
        {'input': '[1, // line\n 2, /* block */ 3,\r\n]', 'expected': [1, 2, 3]},
        {'input': '{"nested":[{"a":1,},],}', 'expected': {'nested': [{'a': 1}]}},
    ])
    fixture = folder / 'cases.json'
    fixture.write_text(json.dumps(cases, ensure_ascii=False))
    script = folder / 'native.os'
    script.write_text('''#Использовать "lib"
Чтение = Новый ЧтениеJSON;
Чтение.УстановитьСтроку(Core.Текст(ТекущийСценарий().Каталог + "/cases.json"));
Тесты = ПрочитатьJSON(Чтение); Чтение.Закрыть();
Парсер = Core.НативныйМодуль("JSONC");
Результаты = Новый Массив;
Для Каждого Тест Из Тесты Цикл
    Чтение = Новый ЧтениеJSON;
    Чтение.УстановитьСтроку(Парсер.Очистить(Тест.input));
    Результаты.Добавить(ПрочитатьJSON(Чтение)); Чтение.Закрыть();
КонецЦикла;
Текст = Core.НативныйМодуль("Text");
Числа = Новый Массив;
Для Каждого Значение Из Core.Арги("12.34|12,34|-5|bad| 0 ") Цикл
    Числа.Добавить(Текст.ЧислоБезопасно(Значение, -99));
КонецЦикла;
Слова = Текст.Слова("  один" + Символы.Таб + "два   три" + Символы.ВК);
Поле = Текст.Поле("Other: x" + Символы.ПС + " VmRSS:  123 kB", "VmRSS");
УдалитьФайлы(ТекущийСценарий().Каталог + "/lib/native/JSONC.os");
Повтор = Core.НативныйМодуль("JSONC").Очистить("[1,]");
Сообщить(Core.ВJSON(Новый Структура("results,numbers,words,field,cached", Результаты, Числа, Слова, Поле, Повтор)));
''')
    result = json.loads(run(script))
    assert result['results'] == [case['expected'] for case in cases]
    assert result['numbers'] == [12.34, 12.34, -5, -99, 0]
    assert result['words'] == ['один', 'два', 'три']
    assert result['field'] == '123 kB'
    assert json.loads(result['cached']) == [1], 'Native script must be reused after load'

    # No native code may be loaded for CLI metadata or an ordinary profile.
    shutil.rmtree(folder / 'lib/native')
    shutil.copy2(ROOT / 'onec-fetch.os', folder / 'onec-fetch.os')
    shutil.copytree(ROOT / 'assets', folder / 'assets')
    assert 'Запуск:' in run(folder / 'onec-fetch.os', '--help')
    assert run(folder / 'onec-fetch.os', '--version').strip() == 'onec-fetch 2.1.0'
    selected = json.loads(run(folder / 'onec-fetch.os', '-s', 'CPU:Memory:Uptime', '--json'))
    assert all(item['status'] == 'ok' for item in selected['modules'])

print('PASS: native JSONC literals/comments/trailing commas/Unicode, numeric guards, text parsing, cached modules, lazy loading and Unicode paths.')

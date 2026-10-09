"""Integration checks for module selection, data, JSONC and process boundaries."""
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = sys.argv[1] if len(sys.argv) > 1 else 'oscript'
SCRIPT = ROOT / 'onec-fetch.os'


def run(*arguments, env=None, expected=0):
    p = subprocess.run([ENGINE, str(SCRIPT), *arguments], cwd='/tmp',
                       env=env, capture_output=True, text=True, timeout=100)
    assert p.returncode == expected, (arguments, p.returncode, p.stdout, p.stderr)
    assert not p.stderr, p.stderr
    return p.stdout


catalog = json.loads((ROOT / 'assets/modules.json').read_text())
names = run('--list-modules').splitlines()
assert len(names) == 76 and len(set(names)) == 76
assert set(names) == {x['name'] for x in catalog.values()}
all_data = json.loads(run('--all', '--json'))
assert all_data['schemaVersion'] == 2
assert [x['type'] for x in all_data['modules']] == names
valid = {'ok', 'unsupported', 'unavailable', 'permission_denied', 'timeout', 'error', 'disabled'}
for item in all_data['modules']:
    assert set(item) == {'type', 'key', 'status', 'source', 'data', 'display', 'error'}, item
    assert item['status'] in valid and item['source'], item
    if item['status'] != 'ok':
        assert item['error'], item
    assert 'Ошибка в строке' not in item['error'] and 'Свойство объекта не обнаружено' not in item['error'], item
by_name = {x['type']: x for x in all_data['modules']}
for name in ('PublicIp', 'Weather', 'Command'):
    assert by_name[name]['status'] == 'disabled'
assert by_name['Uptime']['data']['seconds'] > 0
assert by_name['CPU']['data']['logicalCores'] > 0
assert by_name['CPU']['data']['currentFrequency'] > 0
assert by_name['Memory']['data']['total'] > 0
for name in ('CPUUsage', 'DiskIO', 'NetIO', 'Top'):
    data = by_name[name]['data']
    assert data['intervalSeconds'] == by_name['CPUUsage']['data']['intervalSeconds']
    assert 0.2 <= data['intervalSeconds'] < 5, data
assert all(0 <= x['percentage'] <= 100 for x in by_name['CPUUsage']['data']['items'])
for name in ('DiskIO', 'NetIO'):
    assert all(x['readBytesPerSecond'] >= 0 and x['writeBytesPerSecond'] >= 0 for x in by_name[name]['data']['items'])
assert by_name['Top']['data']['items'] and by_name['Top']['data']['items'][0]['memory'] > 0

chosen = json.loads(run('-s', 'cpu:Uptime', '--json'))
assert [x['type'] for x in chosen['modules']] == ['CPU', 'Uptime']
assert chosen['gpu'] == chosen['memory'] == chosen['host'] == ''
assert 'modules' not in json.loads(run('-s', 'CPU', '--json=legacy'))
for args in (('--unknown',), ('-s', 'Bogus'), ('-s', ''), ('--interval=0',), ('--timeout=abc',), ('--json=bogus',), ('-s',), ('--format=text',)):
    run(*args, expected=2)

with tempfile.TemporaryDirectory(prefix='onec-fetch тест ') as folder:
    folder = Path(folder)
    config = folder / 'настройки.jsonc'
    # Literal comment markers inside a quoted string must survive.
    config.write_text('''{
// comment
"modules":["Title",{"type":"Custom","key":"Ваш ключ","text":"https://example.test/* */",},
{"type":"Memory","key":"RAM","format":"{total}: {value}"},], /* comment */
"interval":300,
}''')
    result = json.loads(run('-c', str(config), '--json'))
    assert [x['type'] for x in result['modules']] == ['Title', 'Custom', 'Memory']
    assert result['modules'][1]['display'] == 'https://example.test/* */'
    assert result['modules'][1]['key'] == 'Ваш ключ'
    assert result['modules'][2]['display'].startswith(str(result['modules'][2]['data']['total']) + ': ')
    assert [x['type'] for x in json.loads(run('-c', str(config), '-s', 'CPU', '--json'))['modules']] == ['CPU']
    assert max(map(len, run('-c', str(config), '--width=40', '--no-color').splitlines())) <= 40
    marker = folder / 'should-not-exist'
    (folder / 'fastfetch').write_text('#!/bin/sh\n: > ' + shlex.quote(str(marker)) + '\n')
    (folder / 'fastfetch').chmod(0o755)
    env = dict(os.environ, PATH=str(folder) + os.pathsep + os.environ['PATH'])
    run('-s', 'CPU:Memory:GPU', '--json', env=env)
    assert not marker.exists(), 'fastfetch must not be the data collector'
    command = "printf 'Ваш текст\\n'"
    result = json.loads(run('-s', 'Command', '--command', command, '--json'))['modules'][0]
    assert result['status'] == 'ok' and result['data']['output'] == 'Ваш текст'
    disabled = json.loads(run('-s', 'CPU', '--command', ': > ' + shlex.quote(str(marker)), '--json'))
    assert not marker.exists(), 'Unselected Command must not run'

    def core(body):
        script = folder / 'core.os'
        script.write_text('#Использовать "' + str(ROOT / 'lib') + '"\n' + body)
        p = subprocess.run([ENGINE, str(script)], text=True, capture_output=True, timeout=15)
        assert p.returncode == 0 and not p.stderr, (p.stdout, p.stderr)
        return json.loads(p.stdout)

    args = ['', 'путь с пробелами', '"quote"', '$HOME;$(touch X)', 'back\\slash\\', 'line\nbreak']
    expression = json.dumps(['-c', 'import json,sys;print(json.dumps(sys.argv[1:],ensure_ascii=False))', *args], ensure_ascii=False).replace('"', '""')
    value = core('Core.Настроить(3000);\nР = Core.Команда("' + sys.executable + '", Core.JSON("' + expression + '"));\nСообщить(Core.ВJSON(Р));')
    assert value['status'] == 'ok' and json.loads(value['stdout']) == args, value
    assert core('Сообщить(Core.ВJSON(Core.ЧислоБезопасно("12.34")));') == 12.34
    assert core('Сообщить(Core.ВJSON(Core.ЧислоБезопасно("12,34")));') == 12.34

    child = folder / 'child.py'
    child.write_text('import time,sys\nfrom pathlib import Path\ntime.sleep(1.5)\nPath(sys.argv[1]).write_text("alive")\n')
    parent = folder / 'parent.py'
    parent.write_text('import subprocess,sys,time\np=subprocess.Popen([sys.executable,sys.argv[1],sys.argv[2]])\nprint(p.pid,flush=True)\ntime.sleep(10)\n')
    expression = json.dumps([str(parent), str(child), str(marker)], ensure_ascii=False).replace('"', '""')
    value = core('Core.Настроить(200);\nР=Core.Команда("' + sys.executable + '",Core.JSON("' + expression + '"));\nСообщить(Core.ВJSON(Р));')
    assert value['status'] == 'timeout' and value['stdout'].strip().isdigit(), value
    time.sleep(1.6)
    assert not marker.exists(), 'Timed out descendant was left running'
    expression = json.dumps(['-c', 'import sys;sys.stdout.write("x"*5000000);sys.stderr.write("y"*5000000)']).replace('"', '""')
    value = core('Core.Настроить(5000);\nР=Core.Команда("' + sys.executable + '",Core.JSON("' + expression + '"));\nСообщить(Core.ВJSON(Новый Структура("status,error",Р.status,Р.stderr)));')
    assert value['status'] == 'error' and value['error'] == 'Output limit exceeded', value
    expression = json.dumps(['-c', 'import sys;print("out");print("err",file=sys.stderr);sys.exit(7)']).replace('"', '""')
    value = core('Core.Настроить(3000);\nСообщить(Core.ВJSON(Core.Команда("' + sys.executable + '",Core.JSON("' + expression + '"))));')
    assert value['exitCode'] == 7 and value['stdout'].strip() == 'out' and value['stderr'].strip() == 'err', value

print('PASS: 76 modules, local collectors, one shared sample, selection, JSONC/format, CLI, no implicit network/commands, literal argv, process-tree timeout and output limit.')

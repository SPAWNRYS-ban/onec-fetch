"""Compare independently collected values with fastfetch on the same Linux host."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = sys.argv[1] if len(sys.argv)>1 else 'oscript'
modules = 'OS:Host:Kernel:CPU:GPU:Memory:Swap:Packages:Display:Disk:Uptime'
ff = json.loads(subprocess.check_output(['fastfetch','--format','json','--structure',modules],text=True))
ours = json.loads(subprocess.check_output([ENGINE,str(ROOT/'onec-fetch.os'),'-s',modules,'--json'],text=True))
f = {x['type']:x.get('result') for x in ff}
o = {x['type']:x['data'] for x in ours['modules'] if x['status']=='ok'}
assert o['OS']['id'] == f['OS']['id']
assert o['Host']['name'] == f['Host']['name']
assert o['Kernel']['release'] == f['Kernel']['release']
assert o['Kernel']['architecture'] == f['Kernel']['architecture']
assert o['CPU']['name'] == f['CPU']['cpu']
assert o['CPU']['logicalCores'] == f['CPU']['cores']['logical']
assert o['CPU']['physicalCores'] == f['CPU']['cores']['physical']
assert abs(o['CPU']['maxFrequency']/1e6-f['CPU']['frequency']['max']) < 2
assert o['Memory']['total'] == f['Memory']['total']
assert abs(o['Memory']['used']-f['Memory']['used']) < o['Memory']['total']*.15
assert o['Swap']['total'] == sum(x['total'] for x in f['Swap'])
assert abs(o['Swap']['used']-sum(x['used'] for x in f['Swap'])) < 128*1024**2
assert o['Packages']['total'] == f['Packages']['all']
assert abs(o['Uptime']['seconds']-f['Uptime']['uptime']/1000) < 15
for gpu in f['GPU']:
    name = gpu['name'].lower()
    match = next(x for x in o['GPU'] if name in x['name'].lower())
    if gpu['type'] == 'Discrete' and 'nvidia' in match['vendor'].lower():
        assert match['type'] == gpu['type']
for display in f['Display']:
    matches = [x for x in o['Display'] if x['width']==display['output']['width'] and x['height']==display['output']['height']]
    assert any(abs(x['refreshRate']-display['output']['refreshRate'])<.1 for x in matches)
for disk in f['Disk']:
    match = next(x for x in o['Disk'] if x['mountpoint']==disk['mountpoint'])
    assert match['total'] == disk['bytes']['total']
    assert match['filesystem'] == disk['filesystem']
    assert abs(match['used']-disk['bytes']['used']) < 256*1024**2
print('PASS: fastfetch parity for OS, host, kernel/architecture, CPU model/cores/frequency, GPU, RAM, swap, packages, displays, disks and uptime (dynamic values with tolerances).')

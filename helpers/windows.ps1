# Raw Windows API adapter. Selection, formulas and rendering live in OneScript.
param([string]$Module,[int]$ParentPid)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
function Ok($data,$display='',$source='Windows API') {
    @{status='ok';data=$data;display=$display;source=$source} | ConvertTo-Json -Depth 12 -Compress
}
function Unavailable($reason) { @{status='unavailable';error=$reason} | ConvertTo-Json -Compress }
try {
    switch ($Module) {
        'Uptime' {
            Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public static class FetchTick { [DllImport("kernel32.dll")] public static extern ulong GetTickCount64(); }'
            Ok @{milliseconds=[FetchTick]::GetTickCount64()} '' 'GetTickCount64';break
        }
        'CPUUsage' { $d=@(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Select-Object Name,PercentProcessorTime); Ok $d; break }
        'CPUCache' { Ok @(Get-CimInstance Win32_CacheMemory | Select-Object Purpose,InstalledSize,Level,CacheType); break }
        'DiskIO' { Ok @(Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk | Select-Object Name,DiskReadBytesPerSec,DiskWriteBytesPerSec); break }
        'NetIO' { Ok @(Get-CimInstance Win32_PerfFormattedData_Tcpip_NetworkInterface | Select-Object Name,BytesReceivedPerSec,BytesSentPerSec); break }
        'Top' { Ok @(Get-CimInstance Win32_PerfFormattedData_PerfProc_Process | Where-Object Name -notin '_Total','Idle' | Sort-Object PercentProcessorTime -Descending | Select-Object -First 5 Name,IDProcess,PercentProcessorTime,WorkingSetPrivate,IODataBytesPersec); break }
        'LocalIp' { Ok @(Get-NetIPConfiguration | ForEach-Object { @{name=$_.InterfaceAlias;ipv4=@($_.IPv4Address | Select-Object IPAddress,PrefixLength);ipv6=@($_.IPv6Address | Select-Object IPAddress,PrefixLength);gateway=@($_.IPv4DefaultGateway.NextHop)} }); break }
        'DNS' { Ok @(Get-DnsClientServerAddress | Select-Object InterfaceAlias,AddressFamily,ServerAddresses); break }
        'Wifi' { $output=netsh wlan show interfaces 2>&1 | Out-String;if($LASTEXITCODE -ne 0){Unavailable $output}else{Ok @{output=$output} $output 'netsh wlan'};break }
        'Bootmgr' { $output=bcdedit /enum '{current}' 2>&1 | Out-String;if($LASTEXITCODE -ne 0){Unavailable $output}else{Ok @{output=$output} $output 'bcdedit'};break }
        'Users' { $output=quser 2>&1 | Out-String;if($LASTEXITCODE -ne 0){Unavailable $output}else{Ok @{output=$output} $output 'quser'};break }
        'TPM' { Ok (Get-CimInstance -Namespace root/cimv2/security/microsofttpm -ClassName Win32_Tpm | Select-Object ManufacturerIdTxt,ManufacturerVersion,SpecVersion,IsEnabled_InitialValue); break }
        'Packages' {
            $keys='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
            $programs=@(Get-ItemProperty $keys -ErrorAction SilentlyContinue | Where-Object DisplayName | Sort-Object PSChildName -Unique | Select-Object DisplayName,DisplayVersion,Publisher,PSChildName)
            $appx=@(Get-AppxPackage | Select-Object Name,Version,PackageFullName)
            Ok @{programs=$programs;appx=$appx}; break
        }
        {$_ -in 'Shell','Terminal'} {
            $list=@();$idToRead=$ParentPid;$seen=@{}
            while($idToRead -gt 0 -and !$seen.ContainsKey($idToRead) -and $list.Count -lt 40) {
                $seen[$idToRead]=$true;$p=Get-CimInstance Win32_Process -Filter "ProcessId=$idToRead"
                if(!$p){break};$list+=@{name=$p.Name;pid=$p.ProcessId;exe=$p.ExecutablePath};$idToRead=$p.ParentProcessId
            }
            $patterns=if($Module -eq 'Shell'){'^(powershell|pwsh|cmd|bash|zsh|fish)\.exe$'}else{'^(WindowsTerminal|OpenConsole|conhost|mintty|alacritty|wezterm-gui|Code)\.exe$'}
            $p=$list | Where-Object {$_.name -match $patterns} | Select-Object -First 1
            if(!$p){Unavailable 'No matching process in parent chain';break}
            $v=if($p.exe){(Get-Item $p.exe).VersionInfo.ProductVersion}else{''};$p.version=$v
            Ok $p "$($p.name) $v" 'Win32_Process parent chain';break
        }
        'Editor' { $name=if($env:VISUAL){$env:VISUAL}else{$env:EDITOR};if(!$name){Unavailable 'VISUAL and EDITOR not set'}else{Ok @{name=$name} $name};break }
        'DE' { Ok @{name='Windows Desktop'} 'Windows Desktop';break }
        'WM' { Ok @{name='DWM';version=[Environment]::OSVersion.Version.ToString()} 'DWM';break }
        'LM' { Ok @{name='Winlogon'} 'Winlogon';break }
        {$_ -in 'Theme','WMTheme'} { $p=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize';Ok @{appsUseLightTheme=$p.AppsUseLightTheme;systemUsesLightTheme=$p.SystemUsesLightTheme};break }
        'Icons' { Unavailable 'Windows has no universal named icon theme';break }
        'Font' { Ok (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes' | Select-Object 'MS Shell Dlg','MS Shell Dlg 2');break }
        'Cursor' { Ok (Get-ItemProperty 'HKCU:\Control Panel\Cursors' | Select-Object '(default)',CursorBaseSize,Arrow);break }
        'Wallpaper' { $p=Get-ItemProperty 'HKCU:\Control Panel\Desktop';Ok @{path=$p.Wallpaper} $p.Wallpaper;break }
        'TerminalSize' { Ok @{columns=[Console]::WindowWidth;rows=[Console]::WindowHeight};break }
        {$_ -in 'TerminalFont','TerminalTheme'} { Unavailable 'Runtime terminal profile API not exposed by this adapter';break }
        'Brightness' { Ok @(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select-Object InstanceName,CurrentBrightness);break }
        {$_ -in 'Display','Monitor'} {
            Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class FetchDisplay {
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] public struct DEVMODE {
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string dmDeviceName;
  public short dmSpecVersion,dmDriverVersion,dmSize,dmDriverExtra; public int dmFields;
  public int dmPositionX,dmPositionY,dmDisplayOrientation,dmDisplayFixedOutput;
  public short dmColor,dmDuplex,dmYResolution,dmTTOption,dmCollate;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string dmFormName;
  public short dmLogPixels; public int dmBitsPerPel,dmPelsWidth,dmPelsHeight,dmDisplayFlags,dmDisplayFrequency,dmICMMethod,dmICMIntent,dmMediaType,dmDitherType,dmReserved1,dmReserved2,dmPanningWidth,dmPanningHeight;
 }
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] public struct DEVICE {
  public int cb; [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)] public string DeviceName;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=128)] public string DeviceString;
  public int StateFlags; [MarshalAs(UnmanagedType.ByValTStr,SizeConst=128)] public string DeviceID;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=128)] public string DeviceKey;
 }
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern bool EnumDisplayDevices(string name,uint index,ref DEVICE dev,uint flags);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern bool EnumDisplaySettings(string name,int mode,ref DEVMODE dev);
}
'@
            $out=@();for([uint32]$i=0;$i -lt 32;$i++){
                $d=[FetchDisplay+DEVICE]::new();$d.cb=[Runtime.InteropServices.Marshal]::SizeOf($d)
                if(![FetchDisplay]::EnumDisplayDevices($null,$i,[ref]$d,0)){break};if(!($d.StateFlags -band 1)){continue}
                $m=[FetchDisplay+DEVMODE]::new();$m.dmSize=[Runtime.InteropServices.Marshal]::SizeOf($m)
                if([FetchDisplay]::EnumDisplaySettings($d.DeviceName,-1,[ref]$m)){$out+=@{name=$d.DeviceString;connector=$d.DeviceName;width=$m.dmPelsWidth;height=$m.dmPelsHeight;refreshRate=$m.dmDisplayFrequency;rotation=$m.dmDisplayOrientation}}
            }
            Ok $out 'Active display modes (see JSON)' 'EnumDisplayDevices/EnumDisplaySettings';break
        }
        'PowerAdapter' { Ok @{batteryStatus=@(Get-CimInstance Win32_Battery | Select-Object Name,BatteryStatus);adapterWatts=$null};break }
        'Keyboard' { Ok @(Get-CimInstance Win32_Keyboard | Select-Object Name,Description,PNPDeviceID);break }
        'Mouse' { Ok @(Get-CimInstance Win32_PointingDevice | Select-Object Name,Description,PNPDeviceID);break }
        {$_ -in 'Camera','Gamepad','Bluetooth','BluetoothRadio'} {
            $class= switch($Module){'Camera'{'Camera'} 'Gamepad'{'HIDClass'} default{'Bluetooth'}}
            $d=@(Get-PnpDevice -Class $class -PresentOnly | Select-Object FriendlyName,InstanceId,Status)
            if($Module -eq 'Gamepad'){$d=@($d | Where-Object {$_.FriendlyName -match 'game|controller|joystick'})}
            if($Module -eq 'BluetoothRadio'){$d=@($d | Where-Object {$_.InstanceId -match '^USB|^PCI'})}
            Ok $d;break
        }
        'Sound' {
            Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class FetchAudio {
 [ComImport,Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] public class Enumerator {}
 [ComImport,Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)] public interface IEnumerator {
 [PreserveSig] int EnumAudioEndpoints(int flow,int state,out IntPtr devices); [PreserveSig] int GetDefaultAudioEndpoint(int flow,int role,out IDevice device);
 }
 [ComImport,Guid("D666063F-1587-4E43-81F1-B948E807363F"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)] public interface IDevice {
 [PreserveSig] int Activate(ref Guid iid,int clsctx,IntPtr parameters,[MarshalAs(UnmanagedType.IUnknown)] out object obj);
 }
 [ComImport,Guid("5CDF2C82-841E-4546-9722-0CF74078229A"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)] public interface IVolume {
 [PreserveSig] int RegisterControlChangeNotify(IntPtr p); [PreserveSig] int UnregisterControlChangeNotify(IntPtr p); [PreserveSig] int GetChannelCount(out uint count);
 [PreserveSig] int SetMasterVolumeLevel(float value,IntPtr ctx); [PreserveSig] int SetMasterVolumeLevelScalar(float value,IntPtr ctx);
 [PreserveSig] int GetMasterVolumeLevel(out float value); [PreserveSig] int GetMasterVolumeLevelScalar(out float value);
 [PreserveSig] int SetChannelVolumeLevel(uint ch,float value,IntPtr ctx); [PreserveSig] int SetChannelVolumeLevelScalar(uint ch,float value,IntPtr ctx);
 [PreserveSig] int GetChannelVolumeLevel(uint ch,out float value); [PreserveSig] int GetChannelVolumeLevelScalar(uint ch,out float value);
 [PreserveSig] int SetMute(bool value,IntPtr ctx); [PreserveSig] int GetMute(out bool value);
 }
 public static object[] Read() { IDevice device; Marshal.ThrowExceptionForHR(((IEnumerator)new Enumerator()).GetDefaultAudioEndpoint(0,1,out device));
 object obj; var id=typeof(IVolume).GUID; Marshal.ThrowExceptionForHR(device.Activate(ref id,23,IntPtr.Zero,out obj));
 float volume;bool mute;var v=(IVolume)obj;Marshal.ThrowExceptionForHR(v.GetMasterVolumeLevelScalar(out volume));Marshal.ThrowExceptionForHR(v.GetMute(out mute));return new object[]{volume,mute}; }
}
'@
            $v=[FetchAudio]::Read();Ok @{volumeScalar=$v[0];mute=$v[1]} 'Default endpoint (volumeScalar/mute in JSON)' 'Core Audio';break
        }
        {$_ -in 'Media','Player'} {
            [void][Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            function Await($op,$type){$m=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.IsGenericMethod})[0];$task=$m.MakeGenericMethod($type).Invoke($null,@($op));if(!$task.Wait(2000)){throw 'WinRT timeout'};$task.Result}
            $manager=Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
            $s=$manager.GetCurrentSession();if(!$s){Ok @();break}
            if($Module -eq 'Player'){Ok @{name=$s.SourceAppUserModelId} $s.SourceAppUserModelId;break}
            [void][Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties,Windows.Media.Control,ContentType=WindowsRuntime]
            $p=Await ($s.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
            Ok @{title=$p.Title;artist=$p.Artist;album=$p.AlbumTitle;player=$s.SourceAppUserModelId} "$($p.Artist) — $($p.Title)";break
        }
        {$_ -in 'Vulkan','OpenGL','OpenCL','Codec'} {
            $exe=switch($Module){'Vulkan'{'vulkaninfo'} 'OpenGL'{'glinfo'} 'OpenCL'{'clinfo'} 'Codec'{'vainfo'}}
            $providerArguments=switch($Module){'Vulkan'{@('--summary')} 'OpenCL'{@('--raw')} default{@()}}
            $tool=Get-Command $exe -ErrorAction SilentlyContinue
            if(!$tool){Unavailable "Required graphics API provider not installed: $exe";break}
            $output=& $tool.Source @providerArguments 2>&1 | Out-String
            if($LASTEXITCODE -ne 0){Unavailable $output}else{Ok @{output=$output} $output $exe};break
        }
        default { Unavailable "No Windows provider for $Module" }
    }
} catch {
    $status=if($_.Exception -is [UnauthorizedAccessException]){'permission_denied'}else{'unavailable'}
    @{status=$status;error=$_.Exception.Message} | ConvertTo-Json -Compress
}

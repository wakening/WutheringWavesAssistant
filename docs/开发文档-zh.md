## 如何翻译gui：
打开命令行，激活python环境，在项目根目录下执行命令  

### 生成待翻译ts文件

使用pyside6-lupdate工具  
-locations absolute 表示生成location信息，行号使用绝对定位（第几行）  
-no-obsolete 删除无用的条目，表示删除所有标记为 obsolete 或 vanished 的条目。建议第一次更新旧文件时，先不要加 -no-obsolete，避免旧翻译直接丢失。确认新文件中的翻译都正常后，再决定是否清理。  

- 方法1  
根据清单批量生成，每种待翻译语言生成一个.ts  
在 src/gui/sources.txt 内逐行配置需要扫描的待翻译的py文件  
在 src/gui/ts_list.txt 内逐行配置需要生成的ts翻译文件，每种语言配置一个，源语言为英文，不用翻译不用配置  
```cmd
pyside6-lupdate -locations absolute @src/gui/sources.txt -ts @src/gui/ts_list.txt

pyside6-lupdate -locations absolute @src/gui/sources.txt -ts @src/gui/ts_list.txt -no-obsolete
```

- 方法2  
逐个生成  
需要指定待翻译的py文件，翻译后的文件名，每次生成一个ts  
```cmd
pyside6-lupdate -locations absolute src/gui/view/gallery_interface.py -ts src/gui/resource/i18n/gallery.zh_CN.ts
```

### 用可视化工具对.ts文件逐个打开翻译  
生成ts文件后，执行qt命令打开qt翻译器，逐条翻译并保存
```cmd
pyside6-linguist
```

打开Qt语言家后，打开.ts文件，选择语言：  
- 源语言：  
  语言选：English 国家/地区选：United States，有重复的选第一个  
  对应 en_US  
- 翻译简体中文 gallery.zh_CN.ts：  
  语言选：Chinese（简体中文） 国家/地区选：China（中国），有重复的选第一个  
  对应 <TS version="2.1" language="zh_CN" sourcelanguage="en_US">  
- 翻译繁体中文 gallery.zh_HK.ts：  
  语言选：Chinese（简体中文） 国家/地区选：Hong Kong（中国香港），有重复的选第一个  
  对应 <TS version="2.1" language="zh_HK" sourcelanguage="en_US">  

选完后确定，保存，.ts里会生成语言配置：<TS version="2.1" language="zh_CN" sourcelanguage="en_US">  
关闭，重新打开，一次打开所有.ts，可以批量翻译  
开始翻译，从左侧 上下文 中选一个，再从旁边的 字符串 源文 中选一个，在下方输入译文，保存  
全部翻译完后，再回到 字符串 源文 ，逐条确认，正确后，在字段旁将问号？打勾✅
点击菜单文件-发布，会生成.qm文件，结束  

编译ts为qm命令：  
单个命令：
```cmd
pyside6-lrelease src/gui/resource/i18n/gallery.zh_CN.ts -qm src/gui/resource/i18n/gallery.zh_CN.qm
```
批量cmd命令：  
```cmd
for /f "usebackq delims=" %i in ("src/gui/ts_list.txt") do pyside6-lrelease "%i"
```
批量PowerShell命令：  
```powershell
Get-Content src/gui/ts_list.txt | % { pyside6-lrelease $_ }
```

## 如何更新qt资源文件，编译resource.qrc为resource.py
打开命令行，激活python环境，在项目根目录下执行命令  
```cmd
pyside6-rcc src/gui/resource/resource.qrc -o src/gui/common/resource.py
```


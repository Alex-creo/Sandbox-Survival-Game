# Run PyInstaller on Windows for a Windows executable. No cross-compilation.
from PyInstaller.utils.hooks import collect_all
from pathlib import Path

root = Path(SPECPATH)
datas = [(str(root / 'assets'), 'assets')]
binaries = []
hiddenimports = ['panda3d.bullet', 'panda3d.core', 'numpy', 'PIL.Image']
for package in ('panda3d', 'direct', 'gltf', 'simplepbr'):
    pd, pb, ph = collect_all(package)
    datas += pd
    binaries += pb
    hiddenimports += ph
analysis = Analysis([str(root/'main.py')], pathex=[str(root)], binaries=binaries,
                    datas=datas, hiddenimports=hiddenimports, noarchive=False)
archive = PYZ(analysis.pure)
executable = EXE(archive, analysis.scripts, [], exclude_binaries=True,
                 name='PhysicsSandbox', debug=False, strip=False, upx=False, console=True)
collection = COLLECT(executable, analysis.binaries, analysis.datas,
                     strip=False, upx=False, name='PhysicsSandbox')

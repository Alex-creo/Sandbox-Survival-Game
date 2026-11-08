# Email source edition

Gmail blocks Windows .bat command files inside archives. This edition omits launch_windows.bat and build_windows.bat. No files are disguised or encrypted. All Python source, shaders, requirements, tests and PyInstaller spec are included.

To launch on Windows, open Command Prompt inside the extracted PhysicsSandbox3D folder and run:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.venv\Scripts\python.exe main.py
```

To package on Windows:

```bat
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean PhysicsSandbox.spec
```

The original documentation follows; references to the omitted .bat launch/build scripts should be replaced with these manual commands.

---

# Physics Sandbox 3D — first playable

A native Python 3.12 / Panda3D desktop sandbox with Bullet physics. Explore a procedural desert, place physical parts, join constructions, drive a dune car and save blueprints locally. Runs independently of Roblox. No web server or paid services.

## Start on Windows

1. Install **64-bit Python 3.12** from python.org, including the Python launcher (`py`).
2. Extract this entire folder to a writable location.
3. Double-click **launch_windows.bat**. On first launch it creates `.venv` and installs the pinned dependencies; this requires internet access. Later launches use the local environment.
4. Click the game window to focus it. Press **TAB** for the catalog.

Or run in Command Prompt:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.venv\Scripts\python.exe main.py
```

If installation was interrupted, repeat the pip command. A graphics driver with OpenGL 3.2+ support is recommended. Start with medium quality; low reduces scenery distance, high enables 1024px directional shadows. Python 3.13/3.14 are not the target runtime.

## Play

A car and a falling block are already on the construction pad. Walk up to the car and press **E**. Use **TAB → TRANSPORT → Cars** to place another car.

| Action | Control |
| --- | --- |
| Walk / sprint | WASD / hold Shift |
| Look / jump | Mouse / Space |
| Enter nearby car / exit | E, within 4.5 metres |
| Drive / steer | W accelerates, S brakes then reverses; A/D steer |
| Parking brake | Space while driving |
| Catalog / close catalog | Tab |
| Pause and settings | Escape |
| Select object | Left mouse, aiming at it |
| Move selected part / release | G; right mouse also releases |
| Rotate selected part or placement preview | R, in 15° increments |
| Placement / move distance | Mouse wheel |
| Enable/disable selected object's physics | F |
| Delete selected object | Delete |
| Fixed joint | Select first part, J; select second part, J |
| Hinge joint | Select first part, H; select second part, H |
| Quicksave / load Quicksave | F5 / F9 |

### Place and customize

Open a catalog category, click an item, choose its color/material/mass and click **PLACE IN WORLD**. Aim the translucent preview, rotate with R, confirm with left mouse or cancel with right mouse. Ground clearance, player distance and Bullet overlap tests prevent invalid placements. Placement is disabled while driving. The object cap is 250.

Select an existing part, then reopen the catalog to use **APPLY COLOR**. `Standard`, `Rubber` and `Ice` change friction and restitution for newly placed objects. Physics can be disabled at placement or toggled with F. Frozen parts retain their configured dynamic mass.

### Construct

Spawn blocks, plates, wheels, axles, engines, seats, hinges and boosters. Move parts near each other, then join them with J or H. A join captures both local frames, so the parts keep their relative transforms through real Bullet constraints. Connections require parts to be within 8 metres. A fixed joint locks all six axes; a hinge permits ±90° rotation. Deleting a part removes its connections.

The standalone component models are structural prototypes. Their engines, boosters, turbines and electrical components **do not produce power or thrust**. The complete Dune runner is the functional vehicle, using BulletVehicle with four raycast wheels, suspension, steering, drive force, braking and reverse. Building powered custom vehicles from individual parts is a future iteration.

### Save and load

**TAB → MY BUILDS** saves all spawned parts and their joints as one named scene/construction blueprint. Loading replaces the current spawned scene. Saving with an existing name replaces that save. Delete asks for confirmation. Terrain and player position are not included. Velocities are reset on load.

Blueprints contain IDs, types, positions, rotations, scales, colors, mass, friction, restitution, physics switches and connection frames. IDs survive loading. Input is validated for size, finite numbers, bounds, allowed types, unique IDs and valid endpoints. Loading stages a replacement before clearing the existing scene; malformed files leave it intact. Missing files produce an in-game message.

Windows runtime data is stored in `%USERPROFILE%\PhysicsSandbox`:

- `saves\*.json` — blueprints
- `settings.json` — resolution, FOV, quality and fog
- `game.log` — startup errors and gameplay messages

Set `PHYSICS_SANDBOX_DATA` to use another folder. SQLite is unnecessary for this prototype.

## Implemented and planned

Implemented: native perspective 3D view, mouse capture, Bullet capsule player with gravity/jumping/sprint, flat collidable textured sand, mountain scenery, cactus/rock scenery with distance LOD, blue sky, ambient/sun lighting, GLSL materials, high-quality shadows on standard scene materials, fog, configurable resolution/FOV, FPS meter, dark DirectGUI catalog with search/scrolling/icons/rotating preview, part registry and tools, fixed/hinge connections, drivable car, clear/simple rain, JSON blueprints, pause/settings and Windows launch/build scripts.

Planned: Survival Mode, multiplayer, mobs, trucks, motorcycles, bicycles, aircraft, boats, active component power networks, powered modular vehicles, storms and a day/night cycle. Those categories are labeled as planned or empty. There were no reference screenshots attached, so the interface uses an original dark layout.

Prototype limits: flat terrain; decorative scenery has no collision; no undo or joint-detach UI; rotation uses yaw only; simple geometric models; no audio; the infinite collision plane extends beyond the visible desert. Avoid driving beyond the mountain ring. The optional custom sand shader currently does not receive directional shadow maps; the construction pad and ordinary parts do. The player resets to the pad if walking outside the mapped area. A 60 FPS target on a suitable desktop GPU is a goal, not a measured hardware guarantee.

## Project layout

- `engine/` — application lifecycle, settings, input bindings, fixed 120 Hz physics accumulator, meshes, optional glTF loader
- `world/` — procedural desert, lighting, quality and clear/rain weather
- `player/` — Bullet character and first-person/vehicle cameras
- `sandbox/` — catalog, registry, manipulation, placement and JSON persistence
- `vehicles/` — Bullet raycast car
- `components/` — reusable physical part class
- `ui/` — DirectGUI catalog, preview, settings and saves
- `assets/` — GLSL shaders and asset notes
- `saves/` — runtime save-location documentation
- `tests/` — real renderer/Bullet integration tests

Future game modes can be added beside `world/` and orchestrated by the application without changing the part/save contracts. Weather owns a separate update boundary for future storm and day/night implementations. Optional glTF assets can be loaded through `engine/assets.py`; all shipped geometry is procedural.

## Test

Install requirements, then:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe main.py --smoke-test
```

Tests use offscreen rendering (`p3headlessgl`) and actual Bullet simulation. On machines without that backend, run the native window smoke test instead. For Linux CI with Mesa/EGL, add `--offscreen` to the smoke test. The screenshot is written to the runtime data folder.

Validated in a Python 3.12 Linux cloud environment using Mesa software OpenGL: startup/rendering, player collision/movement/jump, falling bodies, placement overlap rejection, object tools, both joints, blueprint roundtrip and invalid-file rollback, all menu tabs, settings, rain, vehicle enter/exit, acceleration, steering, braking and reverse. Windows x64/Python 3.12 wheel resolution was checked before delivery. A native Windows runtime/package test is still required; no Windows executable is included.

## Build a Windows executable

Run **build_windows.bat on Windows**. It uses `PhysicsSandbox.spec` and PyInstaller to create `dist\PhysicsSandbox\PhysicsSandbox.exe`. Distribute the **whole** `PhysicsSandbox` folder, including `_internal`; end users then do not need Python. The console is retained to make prototype failures visible. PyInstaller is platform-specific, so a Linux build is not a Windows executable.

All dependencies are free/open-source: Panda3D (BSD), panda3d-gltf and simplepbr (BSD), Pillow (HPND), NumPy (BSD) and PyInstaller (GPL with a distribution exception). simplepbr is already required by panda3d-gltf; this game uses its GLSL lighting/shadow path explicitly. Source and procedural assets in this project are MIT-licensed; see LICENSE. Dependency license files remain with their packages when bundled.

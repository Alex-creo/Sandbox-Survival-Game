# Validation

Environment: Python 3.12.14, Panda3D 1.10.16, Linux x64, Mesa llvmpipe OpenGL 4.5, EGL offscreen rendering.

Final result: **6 tests passed in 49.092 seconds**.

The integration tests use actual Panda3D rendering and Bullet, including:

1. Ground contact, falling rigid bodies, character grounding/jump, WASD input dispatch.
2. GUI tabs, cursor state, object preview, category/search, settings and rain.
3. Bullet overlap rejection during placement.
4. Placement, ray selection, color changes, grab/release, rotation, physics toggles and deletion.
5. Fixed and hinge constraints, preserved IDs and joint frames through JSON roundtrips, malformed-save rollback and save deletion.
6. Vehicle ground contact, entry, acceleration, steering, braking, reverse and exit.

Additional checks:

- Source entry point rendered 120 frames and exited through --offscreen --smoke-test.
- High-quality shadows and rain paths rendered without uncaught errors.
- PyInstaller spec built a Linux bundle; its native executable rendered 120 frames through the smoke-test entry point and exited successfully. That binary is a validation artifact and is not included in the Windows source archive.
- pip check: no broken requirements.
- Python compileall: passed.
- Windows x64 / CPython 3.12 binary-wheel resolution: passed using pip --dry-run --ignore-installed --platform win_amd64 --python-version 3.12 --implementation cp --abi cp312 --only-binary=:all:.

This is not native Windows runtime verification. Build and test on Windows before distributing an executable. FPS in automated screenshots uses a deterministic test clock and is not a performance benchmark.

The cloud emits EGL default-display and /dev/input warnings before its offscreen fallback initializes successfully. There are no corresponding game exceptions. See README.md for the feature limits and planned work.

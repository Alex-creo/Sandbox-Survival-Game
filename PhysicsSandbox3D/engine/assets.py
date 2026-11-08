"""Optional glTF loading. Missing/custom assets safely retain procedural geometry."""
import logging
from pathlib import Path
import gltf
from panda3d.core import NodePath
from engine.geometry import primitive


def load_model(path, fallback='box'):
    try:
        path=Path(path)
        if path.suffix.lower() not in ('.gltf','.glb') or not path.is_file():
            raise ValueError('Missing glTF asset')
        return NodePath(gltf.load_model(str(path)))
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        logging.warning('Using procedural asset for %s: %s',path,exc)
        return NodePath(primitive(fallback).node().makeCopy())

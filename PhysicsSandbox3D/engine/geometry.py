"""Small, cached procedural meshes; all assets are generated locally."""
import math
from functools import lru_cache
from panda3d.core import (GeomVertexData, GeomVertexFormat, GeomVertexWriter,
                         GeomTriangles, Geom, GeomNode, NodePath, Vec3)


def mesh(name, faces):
    data = GeomVertexData(name, GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
    v, n, uv = (GeomVertexWriter(data, key) for key in ('vertex', 'normal', 'texcoord'))
    tris = GeomTriangles(Geom.UHStatic)
    index = 0
    for points in faces:
        normal = (Vec3(*points[1]) - Vec3(*points[0])).cross(Vec3(*points[2]) - Vec3(*points[0]))
        normal.normalize()
        for j, point in enumerate(points):
            v.addData3(*point); n.addData3(normal); uv.addData2((j in (1, 2)), (j >= 2))
        for j in range(1, len(points)-1):
            tris.addVertices(index, index+j, index+j+1)
        index += len(points)
    geom = Geom(data); geom.addPrimitive(tris)
    node = GeomNode(name); node.addGeom(geom)
    return NodePath(node)


@lru_cache(maxsize=8)
def primitive(kind='box', segments=16):
    if kind == 'box':
        return mesh('box', [
            [(-.5,-.5,-.5),(-.5,.5,-.5),(.5,.5,-.5),(.5,-.5,-.5)],
            [(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],
            [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5)],
            [(.5,.5,-.5),(-.5,.5,-.5),(-.5,.5,.5),(.5,.5,.5)],
            [(-.5,.5,-.5),(-.5,-.5,-.5),(-.5,-.5,.5),(-.5,.5,.5)],
            [(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5),(.5,-.5,.5)]])
    faces = []
    for i in range(segments):
        a, b = i*math.tau/segments, (i+1)*math.tau/segments
        x, y, u, w = math.cos(a)*.5, math.sin(a)*.5, math.cos(b)*.5, math.sin(b)*.5
        faces.extend([[(x,y,-.5),(u,w,-.5),(u,w,.5),(x,y,.5)],
                      [(0,0,.5),(x,y,.5),(u,w,.5)],
                      [(0,0,-.5),(u,w,-.5),(x,y,-.5)]])
    return mesh('cylinder', faces)


def shape(parent, kind='box', pos=(0,0,0), scale=(1,1,1), color=(1,1,1,1), hpr=(0,0,0)):
    node = primitive(kind).copyTo(parent)
    node.setPos(*pos); node.setScale(*scale); node.setHpr(*hpr); node.setColor(*color)
    return node

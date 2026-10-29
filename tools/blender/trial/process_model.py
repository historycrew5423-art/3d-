"""Trial step 1: tidy up an outside model the way we would tidy a Tripo export.

Imports a rigged, animated GLB, reports its size, scales it to a target height,
stands it on the ground at the origin, reduces faces, and re-exports a GLB.
Checks that the skeleton and animation survive the round trip.

Usage: blender-py process_model.py <in.glb> <out.glb> [height_m] [decimate_ratio]
"""
import sys

import bpy
from mathutils import Vector

src, dst = sys.argv[1], sys.argv[2]
height = float(sys.argv[3]) if len(sys.argv) > 3 else 1.75
ratio = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

# The glTF importer adds helper objects (bone display shapes) to a "glTF_not_exported"
# collection. They are not part of the model, so leave them out of every measurement.
def real(o):
    return all(c.name != "glTF_not_exported" for c in o.users_collection)


meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and real(o)]
arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
roots = [o for o in bpy.context.scene.objects if o.parent is None and real(o)]


def stats():
    deps = bpy.context.evaluated_depsgraph_get()
    faces = 0
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        ev = o.evaluated_get(deps)
        me = ev.to_mesh()
        faces += len(me.polygons)
        for v in me.vertices:
            w = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        ev.to_mesh_clear()
    return faces, lo, hi


bpy.context.scene.frame_set(0)
faces0, lo, hi = stats()
size0 = hi - lo
print(f"BEFORE faces={faces0} size(x,y,z)={size0.x:.3f},{size0.y:.3f},{size0.z:.3f} "
      f"meshes={len(meshes)} armatures={len(arms)} bones={sum(len(a.data.bones) for a in arms)} "
      f"actions={[a.name for a in bpy.data.actions]}")

# Scale every root so the model is `height` tall, then put its feet at z=0 centred on the origin
scale = height / size0.z
for r in roots:
    r.scale = r.scale * scale
bpy.context.view_layer.update()
_, lo, hi = stats()
offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
for r in roots:
    r.location -= offset
bpy.context.view_layer.update()

# Reduce faces (keeps the armature modifier, so skinning still works)
for o in meshes:
    mod = o.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = ratio
    # apply decimate before the armature modifier, so it acts on the rest pose
    bpy.context.view_layer.objects.active = o
    while o.modifiers.find("Decimate") > 0:
        bpy.ops.object.modifier_move_up(modifier="Decimate")
    bpy.ops.object.modifier_apply(modifier="Decimate")

faces1, lo, hi = stats()
size1 = hi - lo
print(f"AFTER  faces={faces1} size(x,y,z)={size1.x:.3f},{size1.y:.3f},{size1.z:.3f} "
      f"feet_z={lo.z:.3f}")

bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_animations=True,
                          export_skins=True, export_apply=False)

# Round trip check: re-import the result and confirm skeleton + animation are there
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=dst)
arms2 = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
acts = list(bpy.data.actions)
rng = [tuple(int(f) for f in a.frame_range) for a in acts]
print(f"ROUNDTRIP armatures={len(arms2)} bones={sum(len(a.data.bones) for a in arms2)} "
      f"actions={[a.name for a in acts]} frame_ranges={rng}")

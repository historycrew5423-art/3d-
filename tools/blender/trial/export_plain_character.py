"""Re-export the tidied character with its textures removed (plain colour material).

The sample model's texture carries a company logo we may not reuse, so the copy we
publish in the web demo has no texture at all. Skeleton and animation are kept.

Usage: blender-py export_plain_character.py <in.glb> <out.glb>
"""
import sys

import bpy

src, dst = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

plain = bpy.data.materials.new("plain_cloth")
plain.use_nodes = True
bsdf = plain.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.22, 0.25, 0.28, 1)
bsdf.inputs["Roughness"].default_value = 0.8

for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.data.materials.clear()
        o.data.materials.append(plain)
for img in list(bpy.data.images):
    bpy.data.images.remove(img)

# drop the importer's helper objects (bone display shapes) so they are not exported
for o in list(bpy.context.scene.objects):
    if any(c.name == "glTF_not_exported" for c in o.users_collection):
        bpy.data.objects.remove(o)

bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_animations=True,
                          export_skins=True, export_image_format="NONE")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=dst)
print("CHECK images:", len(bpy.data.images),
      "bones:", sum(len(o.data.bones) for o in bpy.context.scene.objects if o.type == "ARMATURE"),
      "actions:", [(a.name, tuple(int(f) for f in a.frame_range)) for a in bpy.data.actions])

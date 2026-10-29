"""Blender headless test: build a tiny scene, export GLB, render a preview with Cycles on CPU."""
import time
import bpy

import os, sys
OUT = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith(".py") else "."
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Ground, a crate and a barrel (neutral test objects)
bpy.ops.mesh.primitive_plane_add(size=6)
ground = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.8, 0, 0.5))
crate = bpy.context.active_object
bpy.ops.object.modifier_add(type="BEVEL")
crate.modifiers["Bevel"].width = 0.05
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.4, depth=1.0, location=(0.8, 0.2, 0.5))
barrel = bpy.context.active_object


def material(name, rgb, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m


ground.data.materials.append(material("sand", (0.76, 0.65, 0.45), 0.9))
crate.data.materials.append(material("wood", (0.45, 0.28, 0.12), 0.7))
barrel.data.materials.append(material("barrel", (0.30, 0.18, 0.08), 0.6))

# Low warm sun + camera behind and above, like a third-person view
bpy.ops.object.light_add(type="SUN", rotation=(1.2, 0.0, 0.8))
bpy.context.active_object.data.energy = 4.0
bpy.context.active_object.data.color = (1.0, 0.85, 0.65)
bpy.ops.object.camera_add(location=(0, -5, 2.5), rotation=(1.2, 0, 0))
scene.camera = bpy.context.active_object
world = bpy.data.worlds.new("sky")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world

# Export GLB (what a web game would load)
bpy.ops.export_scene.gltf(filepath=f"{OUT}/blender_test.glb", export_format="GLB", export_apply=True)
t1 = time.time()

# Render a preview on CPU
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.filepath = f"{OUT}/blender_test.png"
bpy.ops.render.render(write_still=True)
t2 = time.time()

print(f"RESULT scene+export {t1 - t0:.1f}s, render {t2 - t1:.1f}s, blender {bpy.app.version_string}")

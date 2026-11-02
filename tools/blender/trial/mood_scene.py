"""Trial step 2: can code-built Blender scenes get a moody, cinematic look on CPU?

Builds an abandoned room: sun through a window, light shafts in dusty air, wooden
props, leaves creeping in, and a walking character seen from behind (over-the-shoulder).
Then renders a few frames of the character's walk on a plain background to check the
skeleton animation still works.

Usage: blender-py mood_scene.py <character.glb> <out_dir> [samples]
Not a game asset: the theme is deliberately unrelated to the competition entry.
"""
import math
import os
import random
import sys
import time

import bpy
from mathutils import Vector

char_path, out = sys.argv[1], sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 64
os.makedirs(out, exist_ok=True)
random.seed(7)


# ---------- helpers ----------
def box(name, size, loc, mat=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def principled(name, color, rough=0.6, noise_scale=None, noise_mix=0.25, bump=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    if noise_scale is None:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        return m
    # colour variation + small bumps so flat boxes stop looking like plastic
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = noise_scale
    tex.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    dark = [c * (1 - noise_mix) for c in color]
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*color, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    if bump:
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        nt.links.new(tex.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def import_character(frame):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=char_path)
    new = [o for o in bpy.context.scene.objects if o not in before]
    roots = [o for o in new if o.parent is None
             and all(c.name != "glTF_not_exported" for c in o.users_collection)]
    # The sample model's texture carries a company logo we have no right to reuse,
    # so paint the character a plain colour instead.
    plain = principled("plain_cloth", (0.22, 0.25, 0.28), 0.8, noise_scale=40, noise_mix=0.2)
    for o in new:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(plain)
    bpy.context.scene.frame_set(frame)
    return roots


def render(path, x, y, samp):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samp
    s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = x, y
    s.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


# ---------- shot 1: the room ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

wood = principled("old_wood", (0.32, 0.20, 0.11), 0.75, noise_scale=18, noise_mix=0.45, bump=0.25)
plank = principled("pale_wood", (0.50, 0.36, 0.22), 0.7, noise_scale=25, noise_mix=0.4, bump=0.2)
plaster = principled("plaster", (0.55, 0.57, 0.50), 0.9, noise_scale=4, noise_mix=0.35, bump=0.1)
leaf = principled("leaf", (0.12, 0.30, 0.06), 0.5, noise_scale=30, noise_mix=0.4)
jug = principled("jug", (0.55, 0.30, 0.18), 0.35)

W, D, H, T = 6.0, 6.0, 3.0, 0.2           # room width, depth, height, wall thickness
wx0, wx1, wz0, wz1 = -0.4, 1.2, 1.0, 2.3   # window opening on the back wall (y = +D/2)
by = D / 2
box("floor", (W, D, T), (0, 0, -T / 2), wood)
box("ceiling", (W, D, T), (0, 0, H + T / 2), plaster)
box("wall_left", (T, D, H), (-W / 2, 0, H / 2), plaster)
box("wall_right", (T, D, H), (W / 2, 0, H / 2), plaster)
box("wall_front", (W, T, H), (0, -D / 2, H / 2), plaster)
box("back_l", (wx0 + W / 2, T, H), ((-W / 2 + wx0) / 2, by, H / 2), plaster)
box("back_r", (W / 2 - wx1, T, H), ((W / 2 + wx1) / 2, by, H / 2), plaster)
box("back_b", (wx1 - wx0, T, wz0), ((wx0 + wx1) / 2, by, wz0 / 2), plaster)
box("back_t", (wx1 - wx0, T, H - wz1), ((wx0 + wx1) / 2, by, (H + wz1) / 2), plaster)
box("mullion_v", (0.06, 0.1, wz1 - wz0), ((wx0 + wx1) / 2, by, (wz0 + wz1) / 2), wood)
box("mullion_h", (wx1 - wx0, 0.1, 0.06), ((wx0 + wx1) / 2, by, (wz0 + wz1) / 2), wood)

# props: a table, a crate stack, planks leaning on the wall, a jug
box("table_top", (1.4, 0.8, 0.06), (-1.7, 1.6, 0.78), wood)
for dx in (-0.62, 0.62):
    for dy in (-0.32, 0.32):
        box("leg", (0.06, 0.06, 0.75), (-1.7 + dx, 1.6 + dy, 0.375), wood)
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.09, depth=0.25, location=(-1.4, 1.5, 0.94))
bpy.context.active_object.data.materials.append(jug)
for i, (x, y, z, r) in enumerate([(2.0, 2.2, 0.3, 0.1), (2.05, 2.15, 0.9, -0.15), (1.3, 2.4, 0.3, 0.4)]):
    c = box(f"crate{i}", (0.6, 0.6, 0.6), (x, y, z), plank, rot=(0, 0, r))
    bev = c.modifiers.new("bevel", "BEVEL")
    bev.width = 0.02
for i in range(5):
    box(f"plank{i}", (0.18, 0.03, 2.2), (-2.6 + i * 0.22, by - 0.25, 1.05), plank, rot=(math.radians(-12), 0, 0))
for i in range(6):  # boards fallen on the floor
    box(f"debris{i}", (0.15, 1.1, 0.025),
        (random.uniform(-1.5, 1.5), random.uniform(-1.0, 1.0), 0.013), plank,
        rot=(0, 0, random.uniform(0, math.pi)))

# leaves creeping in under the window and up the left corner
bpy.ops.mesh.primitive_plane_add(size=0.12)
leaf_proto = bpy.context.active_object
leaf_proto.data.materials.append(leaf)
spots = [((wx0 - 0.3, wx1 + 0.3), (by - 0.15, by - 0.05), (0.0, wz0 + 0.1)),
         ((-W / 2 + 0.05, -W / 2 + 0.15), (1.0, by), (0.0, 2.6)),
         ((wx0, wx1), (by - 0.6, by - 0.1), (0.0, 0.05))]
for (xs, ys, zs), count in zip(spots, (140, 50, 120)):
    for _ in range(count):
        o = leaf_proto.copy()
        o.location = (random.uniform(*xs), random.uniform(*ys), random.uniform(*zs))
        o.rotation_euler = [random.uniform(0, 6.28) for _ in range(3)]
        o.scale = [random.uniform(0.6, 1.6)] * 3
        scene.collection.objects.link(o)
bpy.data.objects.remove(leaf_proto)

# dusty air so the sunlight shows up as shafts
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2))
air = bpy.context.active_object
air.scale = (W - 0.3, D - 0.3, H - 0.1)
fog = bpy.data.materials.new("dust")
fog.use_nodes = True
nt = fog.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"])
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.05
vol.inputs["Anisotropy"].default_value = 0.4
vol.inputs["Color"].default_value = (1.0, 0.95, 0.88, 1)
nt.links.new(vol.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
air.data.materials.append(fog)

# low warm sun coming through the window, plus a cool sky
bpy.ops.object.light_add(type="SUN", location=(0, 6, 6))
sun = bpy.context.active_object
sun.data.energy = 9.0
sun.data.angle = math.radians(1.0)
sun.data.color = (1.0, 0.82, 0.6)
sun.rotation_euler = Vector((0.35, -1.0, -0.55)).to_track_quat("-Z", "Y").to_euler()
world = bpy.data.worlds.new("sky")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.65, 0.85, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.2
scene.world = world

# the character, walking towards the window, seen from behind
roots = import_character(frame=12)
for r in roots:
    r.location = (0.15, 0.1, 0)
    r.rotation_euler[2] += math.radians(float(os.environ.get("CHAR_TURN", "0")))
# soft bounce light inside, so the dark corners keep some detail
bpy.ops.object.light_add(type="AREA", location=(0.4, 2.2, 0.4))
bounce = bpy.context.active_object
bounce.data.energy = 30
bounce.data.size = 2.5
bounce.data.color = (1.0, 0.85, 0.7)
look_at(bounce, (0.4, 0.0, 2.0))
bpy.ops.object.camera_add(location=(0.75, -2.6, 1.75))
cam = bpy.context.active_object
cam.data.lens = 28
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = 2.4
cam.data.dof.aperture_fstop = 2.8
look_at(cam, (0.1, 2.5, 1.25))
scene.camera = cam
scene.view_settings.exposure = 0.6
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass

t_room = render(f"{out}/mood_room.png", 960, 540, samples)
print(f"RESULT room render {t_room:.1f}s at 960x540, {samples} samples")

# ---------- shot 2: walk cycle check ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.context.active_object.data.materials.append(principled("ground", (0.4, 0.4, 0.4), 0.8))
roots = import_character(frame=0)
bpy.ops.object.light_add(type="SUN", rotation=(0.8, 0.2, 0.6))
bpy.context.active_object.data.energy = 3.0
world = bpy.data.worlds.new("grey")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
scene.world = world
bpy.ops.object.camera_add(location=(4.5, 0, 1.0))
cam = bpy.context.active_object
look_at(cam, (0, 0, 0.9))
scene.camera = cam
frames = [0, 12, 24, 36]
t_walk = 0.0
for f in frames:
    scene.frame_set(f)
    t_walk += render(f"{out}/walk_{f:02d}.png", 300, 400, 16)
print(f"RESULT walk frames {frames} rendered in {t_walk:.1f}s total")

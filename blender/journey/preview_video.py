"""
Joins the journey frame sequences into one preview video (Blender's own FFmpeg).

    blender -b --factory-startup --python blender/journey/preview_video.py -- [portrait]

Output: blender/renders/journey/journey_preview[-p].mp4
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "renders", "journey"))
ORDER = ["exterior", "living", "bedroom", "storage"]
HOLD = 24  # frames: hold the last image of each glide (the interactive room)

portrait = "portrait" in sys.argv
s = bpy.context.scene
s.sequence_editor_create()
start = 1
for ch, seg in enumerate(ORDER):
    d = os.path.join(SRC, f"{seg}-p" if portrait else seg)
    files = sorted(f for f in os.listdir(d) if f.startswith("f_") and f.endswith(".png"))
    strip = s.sequence_editor.sequences.new_image(seg, os.path.join(d, files[0]), channel=1 + ch % 2, frame_start=start)
    for f in files[1:]:
        strip.elements.append(f)
    strip.frame_final_duration = len(files) + HOLD
    start += len(files) + HOLD
s.frame_start, s.frame_end = 1, start - 1
s.render.fps = 24
w, h = (540, 960) if portrait else (960, 540)
s.render.resolution_x, s.render.resolution_y = w, h
s.render.image_settings.file_format = "FFMPEG"
s.render.ffmpeg.format = "MPEG4"
s.render.ffmpeg.codec = "H264"
s.render.ffmpeg.constant_rate_factor = "HIGH"
s.render.filepath = os.path.join(SRC, f"journey_preview{'-p' if portrait else ''}.mp4")
bpy.ops.render.render(animation=True)
print("[ORDEN] video", s.render.filepath)

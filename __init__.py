bl_info = {
    "name": "Bone Parent Type Changer RKNZ",
    "author": "Rikokenz",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > RKNZ",
    "description": "Manage bone parent connections (Connected/Offset) in Pose and Edit Mode.",
    "category": "Animation",
}

import bpy
from bpy.props import FloatProperty


TAB = "RKNZ"


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_selected_bone_names(context):
    obj = context.active_object
    if context.mode == 'POSE':
        return [pb.name for pb in context.selected_pose_bones]
    else:
        return [b.name for b in obj.data.edit_bones if b.select]


def run_in_edit_mode(context, func):
    original_mode = context.mode
    if original_mode == 'POSE':
        bpy.ops.object.mode_set(mode='EDIT')
    result = func(context.active_object)
    if original_mode == 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    return result


# ── Operators ─────────────────────────────────────────────────────────────────

class ARMATURE_OT_rknz_auto_parent_connected(bpy.types.Operator):
    bl_idname = "armature.rknz_auto_parent_connected"
    bl_label = "Auto Parent Connected"
    bl_description = (
        "For each selected bone, find the selected bone whose tail is "
        "closest to this bone's head and parent it as Connected"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object must be an armature")
            return {'CANCELLED'}
        if context.mode not in {'EDIT_ARMATURE', 'POSE'}:
            self.report({'ERROR'}, "Must be in Edit or Pose Mode")
            return {'CANCELLED'}
        threshold = context.scene.rknz_bpc_apc_threshold
        selected_names = get_selected_bone_names(context)
        if len(selected_names) < 2:
            self.report({'WARNING'}, "Select at least 2 bones")
            return {'CANCELLED'}
        count = [0]

        def do_parent(obj):
            bones = obj.data.edit_bones
            selected = [bones[n] for n in selected_names if n in bones]
            for bone in selected:
                closest = None
                min_dist = float('inf')
                for other in selected:
                    if other == bone:
                        continue
                    dist = (other.tail - bone.head).length
                    if dist < min_dist:
                        min_dist = dist
                        closest = other
                if closest and min_dist <= threshold:
                    bone.parent = closest
                    bone.use_connect = True
                    count[0] += 1

        run_in_edit_mode(context, do_parent)
        self.report({'INFO'}, f"Connected {count[0]} bone(s)")
        return {'FINISHED'}


class ARMATURE_OT_rknz_set_parent_connected(bpy.types.Operator):
    bl_idname = "armature.rknz_set_parent_connected"
    bl_label = "Set Parent: Connected"
    bl_description = "Switch selected bones parent type from Offset to Connected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object must be an armature")
            return {'CANCELLED'}
        if context.mode not in {'EDIT_ARMATURE', 'POSE'}:
            self.report({'ERROR'}, "Must be in Edit or Pose Mode")
            return {'CANCELLED'}
        selected_names = get_selected_bone_names(context)
        count = [0]

        def do_connect(obj):
            bones = obj.data.edit_bones
            for name in selected_names:
                bone = bones.get(name)
                if bone and bone.parent and not bone.use_connect:
                    bone.use_connect = True
                    count[0] += 1

        run_in_edit_mode(context, do_connect)
        self.report({'INFO'}, f"Set {count[0]} bone(s) to Connected")
        return {'FINISHED'}


class ARMATURE_OT_rknz_set_parent_offset(bpy.types.Operator):
    bl_idname = "armature.rknz_set_parent_offset"
    bl_label = "Set Parent: Offset"
    bl_description = "Switch selected bones parent type from Connected to Offset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object must be an armature")
            return {'CANCELLED'}
        if context.mode not in {'EDIT_ARMATURE', 'POSE'}:
            self.report({'ERROR'}, "Must be in Edit or Pose Mode")
            return {'CANCELLED'}
        selected_names = get_selected_bone_names(context)
        count = [0]

        def do_offset(obj):
            bones = obj.data.edit_bones
            for name in selected_names:
                bone = bones.get(name)
                if bone and bone.parent and bone.use_connect:
                    bone.use_connect = False
                    count[0] += 1

        run_in_edit_mode(context, do_offset)
        self.report({'INFO'}, f"Set {count[0]} bone(s) to Offset")
        return {'FINISHED'}


# ── Panels ────────────────────────────────────────────────────────────────────

def _draw_parent_type_changer(layout, context):
    box = layout.box()
    box.label(text="Auto Parent by Distance", icon='BONE_DATA')
    col = box.column(align=True)
    col.prop(context.scene, "rknz_bpc_apc_threshold", text="Distance Threshold")
    col.operator("armature.rknz_auto_parent_connected", icon='LINKED')
    layout.separator()
    box = layout.box()
    box.label(text="Switch Parent Type", icon='ARROW_LEFTRIGHT')
    col = box.column(align=True)
    row = col.row(align=True)
    row.operator("armature.rknz_set_parent_connected", text="→ Connected", icon='LINKED')
    row.operator("armature.rknz_set_parent_offset", text="→ Offset", icon='UNLINKED')
    col.label(text="Works on selected bones only", icon='INFO')


class POSE_PT_rknz_bone_parent(bpy.types.Panel):
    bl_label = "Bone Parent Type Changer"
    bl_idname = "POSE_PT_rknz_bone_parent"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB
    bl_context = "posemode"

    def draw(self, context):
        _draw_parent_type_changer(self.layout, context)


class EDIT_PT_rknz_bone_parent(bpy.types.Panel):
    bl_label = "Bone Parent Type Changer"
    bl_idname = "EDIT_PT_rknz_bone_parent"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB
    bl_context = "armature_edit"

    def draw(self, context):
        _draw_parent_type_changer(self.layout, context)


# ── Register ──────────────────────────────────────────────────────────────────

classes = (
    ARMATURE_OT_rknz_auto_parent_connected,
    ARMATURE_OT_rknz_set_parent_connected,
    ARMATURE_OT_rknz_set_parent_offset,
    POSE_PT_rknz_bone_parent,
    EDIT_PT_rknz_bone_parent,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.rknz_bpc_apc_threshold = FloatProperty(
        name="Distance Threshold",
        description="Max distance between bone head and potential parent tail to connect",
        default=0.01,
        min=0.0,
        soft_max=1.0,
        precision=4,
        unit='LENGTH',
    )


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.rknz_bpc_apc_threshold

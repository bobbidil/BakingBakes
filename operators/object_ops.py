"""
Object management operators for BakingBakes addon
"""

import bpy
from bpy.types import Operator

class BAKINGBAKES_OT_AddObject(Operator):
    """Add selected object to bake list"""
    bl_idname = "bakingbakes.add_object"
    bl_label = "Add Object"
    bl_description = "Add selected object to bake list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects

        # Get selected objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Add objects to bake list
        for obj in selected_objects:
            # Check if object is already in list
            if not any(item.object == obj for item in bake_objects.objects):
                item = bake_objects.objects.add()
                item.object = obj

        return {'FINISHED'}

class BAKINGBAKES_OT_RemoveObject(Operator):
    """Remove object from bake list"""
    bl_idname = "bakingbakes.remove_object"
    bl_label = "Remove Object"
    bl_description = "Remove selected object from bake list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects

        if bake_objects.objects:
            # Remove active item
            index = bake_objects.active_index
            if 0 <= index < len(bake_objects.objects):
                bake_objects.objects.remove(index)
                # Adjust active index
                bake_objects.active_index = min(index, len(bake_objects.objects) - 1)

        return {'FINISHED'}

class BAKINGBAKES_OT_ClearObjects(Operator):
    """Clear all objects from bake list"""
    bl_idname = "bakingbakes.clear_objects"
    bl_label = "Clear All"
    bl_description = "Remove all objects from bake list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects

        bake_objects.objects.clear()
        bake_objects.active_index = 0

        return {'FINISHED'}

class BAKINGBAKES_OT_RefreshObjects(Operator):
    """Refresh bake objects list"""
    bl_idname = "bakingbakes.refresh_objects"
    bl_label = "Refresh"
    bl_description = "Refresh the bake objects list"

    def execute(self, context):
        # For now, just report success
        self.report({'INFO'}, "Bake objects list refreshed")
        return {'FINISHED'}

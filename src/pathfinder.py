"""
Pathfinder Maya Tool v1.8

Retargets animation to a path without foot sliding.

Compatible with Maya 2022+ and Python 3.
"""

import maya.cmds as cmds
import maya.OpenMaya as om
import math

def retarget_to_path(character_root, start_frame=None, end_frame=None):
    """
    Retargets the character's animation to follow a created path curve with offsets.

    Args:
        character_root (str): Name of the character root joint or control.
        start_frame (int): Start frame.
        end_frame (int): End frame.
    """
    if not cmds.objExists(character_root):
        cmds.error("Character root does not exist: " + character_root)
        return

    if start_frame is None or end_frame is None:
        start_frame = int(cmds.playbackOptions(query=True, minTime=True))
        end_frame = int(cmds.playbackOptions(query=True, maxTime=True))

    # Create a straight curve
    curve_points = [(0, 0, 0), (0, 0, 10)]
    path_curve = cmds.curve(name='pathfinder_curve', p=curve_points)

    # Create locator1 and attach to the curve
    locator1 = cmds.spaceLocator(name='pathfinder_locator1')[0]
    motion_path = cmds.pathAnimation(locator1, curve=path_curve, follow=True, followAxis='z', upAxis='y')

    # Animate uValue
    cmds.setKeyframe(motion_path + ".uValue", value=0.0, time=start_frame)
    cmds.setKeyframe(motion_path + ".uValue", value=1.0, time=end_frame)

    # Create locator2 parented under locator1
    locator2 = cmds.spaceLocator(name='pathfinder_locator2')[0]
    cmds.parent(locator2, locator1)

    # Constrain locator2 to character_root
    cmds.parentConstraint(character_root, locator2, maintainOffset=True)

    # Bake animation on locator2
    cmds.bakeResults(locator2, time=(start_frame, end_frame), simulation=True)

    # Delete the constraint
    constraints = cmds.listRelatives(locator2, type='constraint')
    if constraints:
        cmds.delete(constraints)

    # Constrain character_root to locator2
    cmds.parentConstraint(locator2, character_root, maintainOffset=True)

    cmds.warning("Retargeting complete. Deform the curve to adjust the path.")

def bake_to_layer(character_root, layer_name="Pathfinder_Baked"):
    """
    Bakes the animation to a new layer.
    """
    # TODO: Implement baking
    cmds.warning("Baking not yet implemented.")

def delete_retarget(character_root):
    """
    Deletes the retargeting by removing the locators, curve, and constraints.
    """
    # Remove constraints on character_root
    constraints = cmds.listRelatives(character_root, type='constraint')
    if constraints:
        cmds.delete(constraints)

    # Delete locators and curve
    to_delete = ['pathfinder_locator1', 'pathfinder_locator2', 'pathfinder_curve']
    for obj in to_delete:
        if cmds.objExists(obj):
            cmds.delete(obj)

    cmds.warning("Retargeting deleted.")

def pick_object(text_field):
    """
    Sets the text field to the first selected object.
    """
    selection = cmds.ls(selection=True)
    if selection:
        cmds.textField(text_field, edit=True, text=selection[0])
    else:
        cmds.warning("No object selected.")

def create_curve_with_controls(num_points):
    """
    Creates a straight curve with the specified number of points,
    each with a locator control that can deform the curve.
    """
    if num_points < 2:
        cmds.error("Number of points must be at least 2.")
        return

    # Create points for a straight line along Z
    spacing = 1.0
    points = [(0, 0, i * spacing) for i in range(num_points)]

    # Create the curve
    curve = cmds.curve(name='custom_curve', p=points)

    # Create locators and connect to cv positions
    for i in range(num_points):
        locator = cmds.spaceLocator(name=f'curve_control_{i}')[0]
        cmds.xform(locator, translation=points[i])

        # Add expressions to drive cv positions
        cmds.expression(name=f'cv_{i}_x', string=f'{curve}.controlPoints[{i}].xValue = {locator}.translateX')
        cmds.expression(name=f'cv_{i}_y', string=f'{curve}.controlPoints[{i}].yValue = {locator}.translateY')
        cmds.expression(name=f'cv_{i}_z', string=f'{curve}.controlPoints[{i}].zValue = {locator}.translateZ')

    cmds.select(curve)
    cmds.warning(f"Curve created with {num_points} controls.")

# UI for the tool
def create_ui():
    """
    Creates the UI for Pathfinder tool.
    """
    if cmds.window("pathfinderWindow", exists=True):
        cmds.deleteUI("pathfinderWindow")

    window = cmds.window("pathfinderWindow", title="Pathfinder v1.8", widthHeight=(400, 300))
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Character Root:")
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 50))
    character_field = cmds.textField(text="character_root")
    cmds.button(label="Pick", command=lambda x: pick_object(character_field))
    cmds.setParent('..')

    cmds.text(label="Start Frame:")
    start_field = cmds.intField(value=1)

    cmds.text(label="End Frame:")
    end_field = cmds.intField(value=100)

    cmds.button(label="Retarget Animation", command=lambda x: retarget_to_path(
        cmds.textField(character_field, query=True, text=True),
        cmds.intField(start_field, query=True, value=True),
        cmds.intField(end_field, query=True, value=True)
    ))

    cmds.button(label="Bake to Layer", command=lambda x: bake_to_layer(
        cmds.textField(character_field, query=True, text=True)
    ))

    cmds.button(label="Delete Retarget", command=lambda x: delete_retarget(
        cmds.textField(character_field, query=True, text=True)
    ))

    cmds.text(label="Number of Points:")
    num_points_field = cmds.intField(value=5)

    cmds.button(label="Create Curve with Controls", command=lambda x: create_curve_with_controls(
        cmds.intField(num_points_field, query=True, value=True)
    ))

    cmds.showWindow(window)

# To run the tool
if __name__ == "__main__":
    create_ui()
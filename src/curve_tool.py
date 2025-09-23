"""
Curve Builder Tool

Creates an EP curve with NURBS controls for deformation.
"""

import maya.cmds as cmds

def create_ep_curve_with_controls(num_points):
    """
    Creates an EP curve (linear NURBS) with the specified number of points,
    each with a NURBS curve control that can deform the curve.
    Adds a master control and organizes everything under a top group.
    The main path curve is non-selectable, and the master control size is reduced by 50%.
    """
    if num_points < 2:
        cmds.error("Number of points must be at least 2.")
        return

    # Create points for a straight line along Z
    spacing = 1.0
    points = [(0, 0, i * spacing) for i in range(num_points)]

    # Create the EP curve (degree 3 for smoother curves)
    curve = cmds.curve(name='creaturePath', p=points, degree=3)  # Renamed to 'creaturePath'

    if not cmds.objExists(curve):
        cmds.error("Failed to create the EP curve. Please try again.")
        return

    # Make the curve non-selectable
    cmds.setAttr(f'{curve}.overrideEnabled', 1)
    cmds.setAttr(f'{curve}.overrideDisplayType', 2)  # 2 = Reference, making it non-selectable

    # Create a top-level group
    top_group = cmds.group(empty=True, name='creaturePathTool')

    # Create a root group to contain all controls
    root_group = cmds.group(empty=True, name='curve_controls_grp', parent=top_group)

    # Create NURBS controls for each point
    for i in range(num_points):
        # Create a small circle as control, rotated 90 in X (normal Z-up)
        control = cmds.circle(name=f'curve_control_{i}', radius=0.1, normal=(0,0,1))[0]
        cmds.xform(control, translation=points[i])
        # Freeze transformations to zero out rotation while keeping translate
        cmds.makeIdentity(control, apply=True, rotate=True, scale=True)

        # Parent the control under the root group
        cmds.parent(control, root_group)

        # Add expressions to drive cv positions
        cmds.expression(name=f'cv_{i}_x', string=f'{curve}.controlPoints[{i}].xValue = {control}.translateX')
        cmds.expression(name=f'cv_{i}_y', string=f'{curve}.controlPoints[{i}].yValue = {control}.translateY')
        cmds.expression(name=f'cv_{i}_z', string=f'{curve}.controlPoints[{i}].zValue = {control}.translateZ')

    # Create a master control
    master_control = cmds.circle(name='master_control', radius=0.5, normal=(0,1,0))[0]  # Reduced size by 50%
    cmds.xform(master_control, translation=(0, 0, 0))
    cmds.makeIdentity(master_control, apply=True, rotate=True, scale=True)

    # Parent the curve and root group under the master control
    cmds.parent(curve, root_group, master_control)

    # Parent the master control under the top group
    cmds.parent(master_control, top_group)

    cmds.select(curve)
    cmds.warning(f"EP Curve created with {num_points} NURBS controls, a master control, and organized under 'creaturePathTool'.")

def create_ui():
    """
    Creates the UI for the Curve Builder tool.
    Adds functionality to add an object to a field and connect it to the EP curve.
    """
    if cmds.window("curveBuilderWindow", exists=True):
        cmds.deleteUI("curveBuilderWindow")

    window = cmds.window("curveBuilderWindow", title="Curve Builder", widthHeight=(300, 200))
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Number of Points:")
    num_points_field = cmds.intField(value=5)

    cmds.button(label="Create EP Curve with Controls", command=lambda x: create_ep_curve_with_controls(
        cmds.intField(num_points_field, query=True, value=True)
    ))

    cmds.separator(height=10, style="in")

    # Add object field and buttons
    cmds.text(label="Object to Connect:")
    object_field = cmds.textField()

    cmds.button(label="Add Selected Object", command=lambda x: cmds.textField(object_field, edit=True, text=cmds.ls(selection=True)[0] if cmds.ls(selection=True) else ""))

    cmds.button(label="Connect to EP Curve", command=lambda x: connect_object_to_curve(cmds.textField(object_field, query=True, text=True)))

    cmds.showWindow(window)

def connect_object_to_curve(object_name):
    """
    Connects the specified object to the EP curve using the pathAnimation command.
    """
    if not object_name or not cmds.objExists(object_name):
        cmds.error("Please specify a valid object to connect.")
        return

    # Find the EP curve
    ep_curve = cmds.ls("creaturePath", type="nurbsCurve") or cmds.ls("creaturePath", type="transform")
    if not ep_curve:
        cmds.error("EP curve not found. Please create one first.")
        return

    ep_curve = ep_curve[0]  # Use the first found curve

    # Run the pathAnimation command
    cmds.pathAnimation(object_name, c=ep_curve, fractionMode=True, follow=True, followAxis="x", upAxis="y",
                       worldUpType="vector", worldUpVector=(0, 1, 0), inverseUp=False, inverseFront=False, bank=False,
                       startTimeU=cmds.playbackOptions(query=True, minTime=True),
                       endTimeU=cmds.playbackOptions(query=True, maxTime=True))

    cmds.warning(f"Connected {object_name} to {ep_curve} with path animation.")

# To run the tool
if __name__ == "__main__":
    create_ui()
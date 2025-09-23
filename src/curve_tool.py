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
    curve = cmds.curve(name='ep_curve', p=points, degree=3)

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

    cmds.showWindow(window)

# To run the tool
if __name__ == "__main__":
    create_ui()
"""
Curve Builder Tool

Creates an EP curve with NURBS controls for deformation.
"""

import maya.cmds as cmds

def create_ep_curve_with_controls(num_points, spacing=1.0, curve_name='ep_curve'):
    """
    Creates an EP curve with the specified number of points,
    each with a NURBS curve control that can deform the curve.
    All controls are parented under a root group for organization.
    """
    if num_points < 2:
        cmds.error("Number of points must be at least 2.")
        return

    # Create points for a straight line along Z
    points = [(0, 0, i * spacing) for i in range(num_points)]

    # Flatten the points list for fitBspline
    flat_points = [coord for point in points for coord in point]

    # Create the EP curve (degree 3 for smoother curves)
    curve = cmds.curve(name=curve_name, p=points, degree=3)

    # Create a root group to contain everything
    root_grp = cmds.group(empty=True, name=f'{curve_name}_controls_grp')

    # Parent the curve under the root
    cmds.parent(curve, root_grp)

    # Create NURBS controls for each point
    control_grp = cmds.group(empty=True, name=f'{curve_name}_controls', parent=root_grp)
    controls = []
    for i in range(num_points):
        # Create a small circle as control, rotated 90 in X (normal Z-up)
        control = cmds.circle(name=f'{curve_name}_control_{i}', radius=0.1, normal=(0,0,1))[0]
        cmds.xform(control, translation=points[i])
        # Freeze transformations to zero out rotation while keeping translate
        cmds.makeIdentity(control, apply=True, rotate=True, scale=True)
        cmds.parent(control, control_grp)
        controls.append(control)

        # Add expressions to drive CV positions
        cmds.expression(name=f'{curve_name}_cv_{i}_x', string=f'{curve}.controlPoints[{i}].xValue = {control}.translateX')
        cmds.expression(name=f'{curve_name}_cv_{i}_y', string=f'{curve}.controlPoints[{i}].yValue = {control}.translateY')
        cmds.expression(name=f'{curve_name}_cv_{i}_z', string=f'{curve}.controlPoints[{i}].zValue = {control}.translateZ')

    # Create script node for dynamic refitting
    script_code = f'''
import maya.cmds as cmds

def refit_curve(curve_name, control_names):
    points = []
    for ctrl in control_names:
        pos = cmds.xform(ctrl, query=True, translation=True)
        points.append(pos)
    # Get the root grp
    root_grp = cmds.listRelatives(curve_name, parent=True)[0]
    # Delete old curve
    cmds.delete(curve_name)
    # Create new curve
    new_curve = cmds.fitBspline(points)
    # Rename
    cmds.rename(new_curve, curve_name)
    # Parent back
    cmds.parent(curve_name, root_grp)
'''
    cmds.scriptNode(name=f'{curve_name}_refit_script', scriptType='python', sourceType='embedded', beforeScript=script_code)

    # Create dummy locator to trigger refit
    dummy = cmds.spaceLocator(name=f'{curve_name}_refit_trigger')[0]
    cmds.parent(dummy, root_grp)
    cmds.setAttr(f'{dummy}.visibility', 0)  # Hide it

    # Create expression to trigger refit when controls move
    control_list_str = str(controls)
    trigger_sum = ' + '.join([f'{ctrl}.translateX + {ctrl}.translateY + {ctrl}.translateZ' for ctrl in controls])
    expression_string = f'python("refit_curve(\'{curve_name}\', {control_list_str})"); {trigger_sum}'
    cmds.expression(name=f'{curve_name}_refit_expr', string=expression_string, object=dummy)

    cmds.select(root_grp)
    cmds.warning(f"EP Curve '{curve_name}' created with {num_points} NURBS controls under '{root_grp}'.")

def create_ui():
    """
    Creates a professional UI for the Curve Builder tool.
    """
    if cmds.window("curveBuilderWindow", exists=True):
        cmds.deleteUI("curveBuilderWindow")

    window = cmds.window("curveBuilderWindow", title="Curve Builder v1.0", widthHeight=(350, 250), sizeable=False)
    cmds.columnLayout(adjustableColumn=True)

    # Header
    cmds.frameLayout(label="Curve Builder", collapsable=False)
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Create customizable EP curves with NURBS controls", align='center')
    cmds.separator(height=10)

    # Options
    cmds.frameLayout(label="Options", collapsable=True, collapse=False)
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Curve Name:")
    curve_name_field = cmds.textField(text="ep_curve")

    cmds.text(label="Number of Points:")
    num_points_field = cmds.intField(value=5, minValue=2)

    cmds.text(label="Spacing:")
    spacing_field = cmds.floatField(value=1.0, minValue=0.1)

    cmds.setParent('..')
    cmds.setParent('..')

    # Create button
    cmds.separator(height=15)
    cmds.button(label="Create EP Curve with Controls", height=40, command=lambda x: create_ep_curve_with_controls(
        cmds.intField(num_points_field, query=True, value=True),
        cmds.floatField(spacing_field, query=True, value=True),
        cmds.textField(curve_name_field, query=True, text=True)
    ))

    cmds.showWindow(window)

# To run the tool
if __name__ == "__main__":
    create_ui()
# Pathfinder Maya Tool

This is a Maya tool for retargeting animations to paths without foot sliding.

## Description

Pathfinder Home Edition is an Autodesk Maya tool that allows animators to retarget their animation into a path.

Lightweight and easy to set up, this tool is much more powerful than the inbuilt Maya’s Motion Path tool. Pathfinder delivers a final result with no foot sliding and preserving the animation as intact as possible.

Pathfinder has been successfully used in feature film productions such as Alpha and The Lion King, being a great time saver for animators!

Key features:

- No foot sliding.
- Easy to setup.
- Easy to delete at any point without damaging the animation.
- Easy to bake into a different layer.
- Results are in real time.

## Files

- `src/pathfinder.py`: Full UI-based tool for retargeting.
- `src/simple_retarget.py`: Simple script to retarget motion to a curve with offsets.
- `src/curve_tool.py`: Tool to create EP curves with NURBS controls for deformation.

## Installation

1. Ensure you have Autodesk Maya 2022+ installed.
2. Copy the desired script file to your Maya scripts directory (e.g., `C:\Users\<username>\Documents\maya\scripts` on Windows, or `~/maya/scripts` on macOS/Linux).
3. Alternatively, load the script in Maya's script editor and run it.

## Usage

### Full Tool (pathfinder.py)

1. In Maya, select your character rig or joint hierarchy.
2. Create or select a NURBS curve as the path.
3. Run the script: `import pathfinder; pathfinder.create_ui()`
4. In the UI:
   - Enter the name of the character root (e.g., the top joint or control).
   - Enter the name of the path curve.
   - Set the start and end frames (or leave default to use playback range).
   - Click "Retarget Animation".
5. The tool will create an animation layer with the retargeted motion.
6. To delete the retargeting, click "Delete Retarget".
7. To bake, click "Bake to Layer" (currently placeholder).

### Curve Builder Tool (curve_tool.py)

1. Run `import curve_tool; curve_tool.create_ui()`
2. Enter the number of points.
3. Click "Create EP Curve with Controls" to create a linear EP curve with NURBS circle controls at each point.
4. Move the controls to deform the curve dynamically.

## Requirements

- Autodesk Maya 2022+
- Python 3 (included with Maya 2022+)

## Notes

- The tool assumes the character root is the top-level object whose world translation defines the motion.
- The path curve should be a NURBS curve.
- The retargeting preserves relative animations, preventing foot sliding.
- For best results, ensure your original animation has the character moving in a straight line or simple path.

## Limitations

- Currently, only adjusts translate and Y rotation of the root.
- Baking functionality is not fully implemented.
- Tested on basic rigs; complex rigs may need adjustments.

If you have a video or screenshot of a similar tool, it could help refine this implementation.
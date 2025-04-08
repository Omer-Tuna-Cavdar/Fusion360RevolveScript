# Fusion 360 API Python script

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math

def run(context):
    ui = None
    try:
        # Get the application and user interface
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the active design
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design', 'Error')
            return

        # Get the root component of the active design
        rootComp = design.rootComponent

        # Create a new component
        allOccs = rootComp.occurrences
        transform = adsk.core.Matrix3D.create()
        newOcc = allOccs.addNewComponent(transform)
        comp = newOcc.component

        # Create a new sketch on the x-y plane
        sketches = comp.sketches
        xyPlane = comp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Get user input for the function, interval, and axis of revolution
        # For the function, we'll ask for an expression in terms of 'x'
        functionDialog = ui.inputBox('Enter the function in terms of x (e.g., x+2):', 'Function Input', 'x+2')
        if functionDialog[1]:
            return  # User canceled
        functionExpr = functionDialog[0].strip()

        intervalDialog = ui.inputBox('Enter the interval for x as start,end (e.g., 0,5):', 'Interval Input', '0,5')
        if intervalDialog[1]:
            return  # User canceled
        intervalInput = intervalDialog[0].strip().split(',')
        if len(intervalInput) != 2:
            ui.messageBox('Invalid interval input. Use start,end format.', 'Error')
            return
        x_start = float(intervalInput[0])
        x_end = float(intervalInput[1])

        axisDialog = ui.inputBox('Enter axis of revolution (e.g., x=0, y=0, x=1):', 'Axis of Revolution', 'x=0')
        if axisDialog[1]:
            return  # User canceled
        axisInput = axisDialog[0].strip()

        # Parse the axis input
        axisType = None
        axisValue = 0
        if axisInput.startswith('x='):
            axisType = 'x'
            axisValue = float(axisInput[2:])
        elif axisInput.startswith('y='):
            axisType = 'y'
            axisValue = float(axisInput[2:])
        else:
            ui.messageBox('Invalid axis input. Use x=... or y=...', 'Error')
            return

        # Create points along the function
        numPoints = 100  # Number of points to plot
        deltaX = (x_end - x_start) / (numPoints - 1)
        points = []
        for i in range(numPoints):
            x = x_start + i * deltaX
            # Evaluate the function expression
            try:
                y = eval(functionExpr, {'x': x, 'math': math})
            except Exception as e:
                ui.messageBox('Error evaluating function at x={}: {}'.format(x, e), 'Error')
                return
            points.append(adsk.core.Point3D.create(x, y, 0))

        # Draw the curve
        # Corrected section starts here
        sketchPoints = sketch.sketchPoints
        fitPoints = adsk.core.ObjectCollection.create()
        for pt in points:
            fitPoints.add(pt)
        spline = sketch.sketchCurves.sketchFittedSplines.add(fitPoints)
        # Corrected section ends here

        # Create a line to close the profile
        lines = sketch.sketchCurves.sketchLines
        if axisType == 'x':
            startLine = lines.addByTwoPoints(points[0], adsk.core.Point3D.create(points[0].x, axisValue, 0))
            endLine = lines.addByTwoPoints(points[-1], adsk.core.Point3D.create(points[-1].x, axisValue, 0))
            baseLine = lines.addByTwoPoints(adsk.core.Point3D.create(points[0].x, axisValue, 0), adsk.core.Point3D.create(points[-1].x, axisValue, 0))
        elif axisType == 'y':
            startLine = lines.addByTwoPoints(points[0], adsk.core.Point3D.create(axisValue, points[0].y, 0))
            endLine = lines.addByTwoPoints(points[-1], adsk.core.Point3D.create(axisValue, points[-1].y, 0))
            baseLine = lines.addByTwoPoints(adsk.core.Point3D.create(axisValue, points[0].y, 0), adsk.core.Point3D.create(axisValue, points[-1].y, 0))

        # Get the profile to revolve
        prof = sketch.profiles.item(0)

        # Create the axis of revolution
        if axisType == 'x':
            axisLine = sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(-1000, axisValue, 0),
                adsk.core.Point3D.create(1000, axisValue, 0)
            )
        elif axisType == 'y':
            axisLine = sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(axisValue, -1000, 0),
                adsk.core.Point3D.create(axisValue, 1000, 0)
            )

        # Create the revolve feature
        revolves = comp.features.revolveFeatures
        revInput = revolves.createInput(prof, axisLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        angle = adsk.core.ValueInput.createByString('360 deg')
        revInput.setAngleExtent(False, angle)
        revolves.add(revInput)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

import math
import maya.cmds as cmds
import maya.mel as mel
import re

# Global Variables
TOLERANCE = 10
INITIALISATION_DISTANCE = 2 ** 32 - 1


def get_magnitude(point_a, point_b):
    """This function returns the magnitude of a vector.

    :param point_a: point a (type: tuple)
    :param point_b: point b (type: tuple)
    :return norm: magnitude of the vector (type: float)
    """

    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]
    dz = point_a[2] - point_b[2]

    norm = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))

    return norm


def get_shapes(object_, fullPathState=False, noIntermediateState=True):
    """This function returns shapes of the provided object.

    :param object_: current object (type:string)
    :param fullPathState: current full path state (type:  boolean)
    :param noIntermediateState: current no intermediate state (type: boolean)
    :return: objects shapes (type: list)
    """

    object_shapes = []
    shapes = cmds.listRelatives(object_, fullPath=fullPathState, shapes=True, noIntermediate=noIntermediateState)
    if shapes is not None:
        object_shapes = shapes

    return object_shapes


def get_selected_reference_mesh():
    """This function gets the reference object."""

    selection = cmds.ls(sl=True, type="transform")

    if selection:
        cmds.textField("referenceObject_TextField", edit=True, text=selection[0])


def load_plugin(plugin):
    """This function loads a plugin.

    :param plugin: name of plugin (type: string)
    """

    not cmds.pluginInfo(plugin, query=True, loaded=True) and cmds.loadPlugin(plugin)


def snap_to_closest_vertex(referenceObject, vertices, tolerance):
    """This function snaps vertices to onto the reference object.

    :param referenceObject: reference mesh (type: string)
    :param vertices: vertices list (type: list)
    :param tolerance: tolerance (type: float)
    """

    progress_bar = mel.eval("$container = $gMainProgressBar")

    cmds.progressBar(progress_bar, edit=True, beginProgress=True, isInterruptable=True, status="Snapping Vertices ...",
                     maxValue=len(vertices))

    load_plugin("nearestPointOnMesh")

    nearest_point_on_mesh_node = mel.eval("nearestPointOnMesh " + referenceObject)

    for vertex in vertices:
        if cmds.progressBar(progress_bar, query=True, isCancelled=True):
            break

        closest_distance = INITIALISATION_DISTANCE

        vertex_position = cmds.pointPosition(vertex, world=True)
        cmds.setAttr(nearest_point_on_mesh_node + ".inPosition", vertex_position[0], vertex_position[1],
                     vertex_position[2])
        associated_face_id = cmds.getAttr(nearest_point_on_mesh_node + ".nearestFaceIndex")
        vtxs_faces = cmds.filterExpand(cmds.polyListComponentConversion(
            (referenceObject + ".f[" + str(associated_face_id) + "]"), fromFace=True, toVertexFace=True),
            sm=70, expand=True)

        closest_position = []
        for vtxs_face in vtxs_faces:
            associated_vtx = cmds.polyListComponentConversion(vtxs_face, fromVertexFace=True, toVertex=True)
            associated_vtx_position = cmds.pointPosition(associated_vtx, world=True)

            distance = get_magnitude(vertex_position, associated_vtx_position)

            if distance < closest_distance:
                closest_distance = distance
                closest_position = associated_vtx_position

            if closest_distance < tolerance:
                cmds.move(closest_position[0], closest_position[1], closest_position[2], vertex, worldSpace=True)

        cmds.progressBar(progress_bar, edit=True, step=1)

    cmds.progressBar(progress_bar, edit=True, endProgress=True)

    cmds.delete(nearest_point_on_mesh_node)


def snap_it():
    """This function opens online repository."""

    reference_object = cmds.textField("referenceObject_TextField", query=True, text=True)

    reference_object_shapes = cmds.objExists(reference_object) and get_shapes(reference_object) or None

    selection = cmds.ls(sl=True, fl=True)
    selected_vertices = [node for node in selection if re.search("\.vtx\[[0-9]*\]", node)]
    reference_object_shapes and selected_vertices and snap_to_closest_vertex(reference_object_shapes[0],
                                                                             selected_vertices, TOLERANCE)


def main():
    """This function launches snap_vertex_to_closest window."""

    cmds.windowPref(enableAll=False)

    if cmds.window("snapToClosestVertex_Window", exists=True):
        cmds.deleteUI("snapToClosestVertex_Window")

    window = cmds.window(title="Snap To Closest Vertex", iconName='SnapToClosestVert', maximizeButton=False,
                         widthHeight=(200, 50), rtf=True, toolbox=True)

    cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnOffset=["both", 8])

    cmds.rowColumnLayout(numberOfColumns=3, columnAttach=(1, 'both', 0), columnWidth=[(1, 100), (2, 250), (3, 32)])
    cmds.text(label='Ref Mesh')
    cmds.textField("referenceObject_TextField")
    cmds.button("getObject_Button", label="<<<", align="center", command="get_selected_reference_mesh()")

    cmds.setParent(upLevel=True)
    cmds.button("snapIt_Button", label="Snap Verts To Mesh", align="center", command="snap_it()")

    cmds.showWindow(window)

    cmds.windowPref(enableAll=True)


if __name__ == '__main__':
    main()
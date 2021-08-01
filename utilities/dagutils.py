import maya.cmds as mc
import maya.OpenMaya as legacy
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from six import string_types
from collections import deque
from itertools import chain

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getNodeName(dependNode):
    """
    Retrieves the name of the given node object.
    This name will not contains pipes or namespaces.

    :type dependNode: om.MObject
    :rtype: str
    """

    return stripAll(om.MFnDependencyNode(dependNode).name())


def demoteMObject(dependNode):
    """
    Demotes the supplied MObject back into the legacy API type.
    This method only supports Dependency/DAG nodes!

    :type dependNode: om.MObject
    :rtype: legacy.MObject
    """

    # Check value type
    #
    if not isinstance(dependNode, om.MObject):

        raise TypeError('demoteMObject() expects the new MObject type!')

    # Get full path name from node
    #
    fullPathName = ''

    if dependNode.hasFn(om.MFn.kDagNode):

        dagPath = om.MDagPath.getAPathTo(dependNode)
        fullPathName = dagPath.fullPathName()

    elif dependNode.hasFn(om.MFn.kDependencyNode):

        fullPathName = om.MFnDependencyNode(dependNode).absoluteName()

    else:

        raise TypeError('getLegacyMObject() expects a dependency node (%s given)!' % dependNode.apiTypeStr)

    # Add name to legacy selection list
    #
    selectionList = legacy.MSelectionList()
    selectionList.add(fullPathName)

    legacyDependNode = legacy.MObject()
    selectionList.getDependNode(0, legacyDependNode)

    return legacyDependNode


def promoteMObject(dependNode):
    """
    Promotes the supplied MObject back into the new API type.
    This method only supports Dependency/DAG nodes!

    :type dependNode: legacy.MObject
    :rtype: om.MObject
    """

    # Check value type
    #
    if not isinstance(dependNode, legacy.MObject):

        raise TypeError('promoteMObject() expects the legacy MObject type!')

    # Get full path name from node
    #
    fullPathName = ''

    if dependNode.hasFn(legacy.MFn.kDagNode):

        dagPath = legacy.MDagPath()
        legacy.MDagPath.getAPathTo(dependNode, dagPath)

        fullPathName = dagPath.fullPathName()

    elif dependNode.hasFn(legacy.MFn.kDependencyNode):

        fullPathName = om.MFnDependencyNode(dependNode).absoluteName()

    else:

        raise TypeError('promoteLegacyMObject() expects a dependency node (%s given)!' % dependNode.apiTypeStr)

    # Add name to selection list
    #
    selectionList = om.MSelectionList()
    selectionList.add(fullPathName)

    return selectionList.getDependNode(0)


def getMObjectByName(name):
    """
    Method used to retrieve an MObject based on the given node name.
    If a plug is included in the name then a tuple will be returned instead.

    :type name: str
    :rtype: om.MObject
    """

    # Check if string contains an attribute
    #
    strings = name.split('.', 1)
    numStrings = len(strings)

    if numStrings == 1:

        # Try and add node name to selection list
        # If it fails then a RuntimeError will be raised
        #
        try:

            # Append node name to selection list
            #
            selection = om.MSelectionList()
            selection.add(name)

            return selection.getDependNode(0)

        except RuntimeError as exception:

            log.warning(exception)
            return om.MObject.kNullObj

    else:

        # Check node and attribute exist
        #
        try:

            # Append path name to selection list
            #
            selection = om.MSelectionList()
            selection.add(name)

            return selection.getDependNode(0), selection.getPlug(0)

        except RuntimeError as exception:

            log.warning(exception)
            return om.MObject.kNullObj


def getMObjectByMUuid(uuid):
    """
    Method used to retrieve an MObject from the given UUID.
    If multiple nodes are found with the same UUID then a list will be returned!

    :type uuid: om.MUuid
    :rtype: Union[om.MObject, list[om.MObject]]
    """

    # Add UUID to selection list
    #
    try:

        selection = om.MSelectionList()
        selection.add(uuid)

        # Inspect selection count
        #
        selectionCount = selection.length()

        if selectionCount == 0:

            return om.MObject.kNullObj

        elif selectionCount == 1:

            return selection.getDependNode(0)

        else:

            return [selection.getDependNode(x) for x in range(selectionCount)]

    except RuntimeError as exception:

        log.warning(exception)
        return om.MObject.kNullObj


def getMObjectByMObjectHandle(handle):
    """
    Retrieves an MObject from the given MObjectHandle.

    :type handle: om.MObjectHandle
    :rtype: om.MObject
    """

    return handle.object()


def getMObjectByMDagPath(dagPath):
    """
    Retrieves an MObject from the given MDagPath.

    :type dagPath: om.MDagPath
    :rtype: om.MObject
    """

    return dagPath.node()


__getmobject__ = {
    'str': getMObjectByName,
    'unicode': getMObjectByName,  # Leaving this here for backwards compatibility
    'MUuid': getMObjectByMUuid,
    'MObjectHandle': getMObjectByMObjectHandle,
    'MDagPath': getMObjectByMDagPath
}


def getMObject(value):
    """
    Method used to retrieve an MObject from any given value.
    This method expects the value to be derived from a dependency node in order to work.
    Failure to do so will result in a type error!

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: om.MObject
    """

    # Check for redundancy
    #
    if isinstance(value, om.MObject):

        return value

    # Check value type
    #
    typename = type(value).__name__
    method = __getmobject__.get(typename, None)

    if method is not None:

        return method(value)

    else:

        raise TypeError('getMObject() expects %s (%s given)!' % (__getmobject__.keys(), type(value).__name__))


def getMObjectHandle(value):
    """
    Method used to get an MObjectHandle from any given value.

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: om.MObjectHandle
    """

    # Check for redundancy
    #
    if isinstance(value, om.MObjectHandle):

        return value

    else:

        return om.MObjectHandle(getMObject(value))


def getHashCode(value):
    """
    Method used to get the hash code from any given value.

    :type value: Union[int, long, str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: long
    """

    return getMObjectHandle(value).hashCode()


def getMDagPath(value):
    """
    Class method used to retrieve an MDagPath from any given value.
    This method expects the value to be derived from a dag node in order to work.

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: om.MDagPath
    """

    # Check for redundancy
    #
    if isinstance(value, om.MDagPath):

        return value

    else:

        return om.MDagPath.getAPathTo(getMObject(value))


def getAssociatedReferenceNode(dependNode):
    """
    Method used to retrieve the reference node associated with the given dependency node.
    If this node is not referenced then none will be returned!

    :type dependNode: om.MObject
    :rtype: om.MObject
    """

    # Check if node is referenced
    #
    fnDependNode = om.MFnDependencyNode(dependNode)

    if not fnDependNode.isFromReferencedFile:

        return None

    # Iterate through reference nodes
    #
    fnReference = om.MFnReference()

    for reference in iterNodes(apiType=om.MFn.kReference):

        # Check if reference contains node
        #
        fnReference.setObject(reference)

        if fnReference.containsNodeExactly(dependNode):

            return reference

        else:

            continue


def getComponentFromString(value):
    """
    Method used to retrieve an object and component based on the supplied string value.

    :type value: str
    :rtype: om.MDagPath, om.MObject
    """

    # Check value type
    #
    if not isinstance(value, string_types):

        raise TypeError('getComponentFromString() expects a str (%s given)!' % type(value).__name__)

    # Check if object exists
    #
    if not mc.objExists(value):

        raise TypeError('getComponentFromString() expects a valid string object!')

    # Add value to selection list
    #
    selection = om.MSelectionList()
    selection.add(value)

    return selection.getComponent(0)


def getActiveSelection(apiType=om.MFn.kDependencyNode):
    """
    Method used to retrieve the active selection.
    An optional api type can be supplied to narrow down the selection.

    :type apiType: int
    :rtype: list[om.MObject]
    """

    return list(iterActiveSelection(apiType=apiType))


def iterActiveSelection(apiType=om.MFn.kDependencyNode):
    """
    Generator method used to iterate through the active selection.
    An optional api type can be supplied to narrow down the selection.

    :type apiType: int
    :rtype: iter
    """

    # Get active selection
    #
    selection = om.MGlobal.getActiveSelectionList()
    selectionCount = selection.length()

    for i in range(selectionCount):

        # Check api type
        #
        dependNode = selection.getDependNode(i)

        if dependNode.hasFn(apiType):

            yield dependNode

        else:

            continue


def getRichSelection(apiType=om.MFn.kMeshVertComponent):
    """
    Just like get component selection this function returns a list of tuples but with a dictionary instead.
    The dictionary value contains a series of vertex index keys that correlate with their soft selection weight.
    MItSelectionList will automatically convert any mesh component back to vertices unless overrided.

    :type apiType: int
    :rtype: list[tuple[om.MDagPath, dict[int: float]]]
    """

    # Get rich selection from MGlobal
    #
    softSelection = om.MGlobal.getRichSelection()

    selection = softSelection.getSelection()
    numSelected = selection.length()

    if numSelected > 0:

        # Initialize selection iterator
        #
        iterSelection = om.MItSelectionList(selection, apiType)

        # Iterate through selection
        #
        dagPath, component = None, None
        softWeights = {}

        fnComponent = om.MFnSingleIndexedComponent()

        # Define lambda expression
        #
        getWeight = lambda x: fnComponent.weight(x).influence if fnComponent.hasWeights else 1.0

        while not iterSelection.isDone():

            # Get mesh and vertex component
            #
            dagPath, component = iterSelection.getComponent()
            fnComponent.setObject(component)

            for i in range(fnComponent.elementCount):

                element = fnComponent.element(i)
                softWeights[element] = getWeight(i)

            # Increment iterator
            #
            iterSelection.next()

        return dagPath, softWeights

    else:

        return None, None


def getComponentSelection():
    """
    Retrieves the current active component selection.
    Since multiple shape nodes can be edited at different component levels tuples must be returned in a list.

    :rtype: list[tuple[om.MDagPath, om.MObject]]
    """

    # Access the Maya global selection list
    #
    selection = om.MGlobal.getActiveSelectionList()
    numSelected = selection.length()

    if numSelected == 0:

        return []

    # Initialize selection iterator
    #
    iterSelection = om.MItSelectionList(selection, om.MFn.kMeshComponent)
    componentSelection = []

    # Iterate through selection
    #
    while not iterSelection.isDone():

        # Check if item has a valid component
        #
        dagPath, component = iterSelection.getComponent()

        if dagPath.isValid() and not component.isNull():

            componentSelection.append(tuple([dagPath, component]))

        else:

            log.debug('Skipping invalid component selection on %s.' % dagPath.partialPathName())

        # Go to next selection
        #
        iterSelection.next()

    return componentSelection


def iterChildren(dagPath, apiType=om.MFn.kTransform):
    """
    Generator method used to iterate through this dag node's children.
    An optional api type can be supplied to narrow down the children.

    :type dagPath: om.MDagPath
    :type apiType: int
    :rtype: iter
    """

    # Initialize function set
    #
    fnDagNode = om.MFnDagNode(dagPath)
    childCount = fnDagNode.childCount()

    for i in range(childCount):

        # Check child api type
        #
        child = fnDagNode.child(i)

        if child.hasFn(apiType):

            yield child

        else:

            continue


def iterDescendants(dagPath, apiType=om.MFn.kTransform):
    """
    Generator method used to iterate through all of the descendants for the supplied node.

    :type dagPath: om.MDagPath
    :type apiType: int
    :rtype: iter
    """

    # Iterate through queue
    #
    queue = deque([dagPath])

    while len(queue):

        # Iterate through children
        #
        item = queue.popleft()

        for child in iterChildren(item, apiType=apiType):

            queue.append(child)
            yield child


def iterShapes(dagPath, apiType=om.MFn.kShape):
    """
    Generator method used to iterate through this dag node's shapes.

    :type dagPath: om.MDagPath
    :type apiType: int
    :rtype: iter
    """

    # Iterate through children
    #
    fnDagNode = om.MFnDagNode()

    for child in iterChildren(dagPath, apiType=apiType):

        # Check if child is intermediate object
        #
        fnDagNode.setObject(child)

        if not fnDagNode.isIntermediateObject:

            yield child

        else:

            continue


def iterIntermediateObjects(dagPath, apiType=om.MFn.kShape):
    """
    Generator method used to iterate through this dag node's intermediate objects.

    :type dagPath: om.MDagPath
    :type apiType: int
    :rtype: iter
    """

    # Iterate through children
    #
    fnDagNode = om.MFnDagNode()

    for child in iterChildren(dagPath, apiType=apiType):

        # Check if child is intermediate object
        #
        fnDagNode.setObject(child)

        if fnDagNode.isIntermediateObject:

            yield child

        else:

            continue


def iterDeformersFromSelection(apiType=om.MFn.kGeometryFilt):
    """
    Generator method used to iterate through the deformers associated with the active selection.
    An optional api type can be provided to narrow down the deformers.

    :type apiType: int
    :rtype: iter
    """

    # Iterate through selection
    #
    for dependNode in iterActiveSelection(apiType=om.MFn.kDagNode):

        # Check if this is a transform
        #
        if dependNode.hasFn(om.MFn.kTransform):

            # Check if transform has any shapes
            #
            dagPath = om.MDagPath.getAPathTo(dependNode)

            shapes = list(iterShapes(dagPath))
            numShapes = len(shapes)

            if numShapes == 0:

                continue

            elif numShapes == 1:

                dependNode = shapes[0]

            else:

                log.warning('Multiple shape nodes found @ %s' % dagPath.partialPathName())
                continue

        # Check if this is a shape
        #
        if not dependNode.hasFn(om.MFn.kShape):

            continue

        # Iterate through dependencies
        #
        for dependency in iterDependencies(dependNode, apiType, direction=om.MItDependencyGraph.kUpstream):

            yield dependency


def iterFunctionSets():
    """
    Generator method used to iterate through all available function sets derived from MFnDependencyNode.
    This does not include function sets from the OpenMayaAnim module.

    :rtype: iter
    """

    # Iterate through dictionary
    #
    for (key, value) in chain(om.__dict__.items(), oma.__dict__.items()):

        # Check if pair matches criteria
        #
        if key.startswith('MFn') and issubclass(value, om.MFnDependencyNode):

            yield value


def iterNodes(apiType=om.MFn.kDependencyNode):
    """
    Generator method used to iterate through dependency nodes.
    These nodes can be limited to a specific type by changing the "apiType" keyword.

    :type apiType: int
    :rtype: iter
    """

    # Initialize dependency node iterator
    #
    iterDependNodes = om.MItDependencyNodes(apiType)

    while not iterDependNodes.isDone():

        # Get current node
        #
        currentNode = iterDependNodes.thisNode()
        yield currentNode

        # Increment iterator
        #
        iterDependNodes.next()


def iterPluginNodes(typeName):
    """
    Generator method used to iterate through user plugin nodes based on the given type name.
    This method will not respect sub-classes on user plugins! But these are SUPER rare...
    The type name is defined through the "MFnPlugin::registerNode()" method as the first argument.

    :type typeName: str
    :rtype: iter
    """

    # Initialize dependency node iterator
    #
    iterDependNodes = om.MItDependencyNodes(om.MFn.kPluginDependNode)
    fnDependNode = om.MFnDependencyNode()

    while not iterDependNodes.isDone():

        # Get current node
        #
        currentNode = iterDependNodes.thisNode()
        fnDependNode.setObject(currentNode)

        if fnDependNode.typeName == typeName:

            yield currentNode

        # Increment iterator
        #
        iterDependNodes.next()


def iterNodesByNamespace(namespace, recurse=False):
    """
    Generator method used to retrieve the nodes that reside within the supplied namespace.

    :type namespace: str
    :type recurse: bool
    :rtype: iter
    """

    # Check if namespace exists
    #
    if om.MNamespace.namespaceExists(namespace):

        log.warning('"%s" namespace does not exist!' % namespace)
        return

    # Iterate through namespace objects
    #
    namespace = om.MNamespace.getNamespaceFromName(namespace)

    for namespaceObject in namespace.getNamespaceObjects(recurse=recurse):

        yield namespaceObject


def iterNodesByUuid(uuid):
    """
    Generator method used to retrieve all of dependency nodes with the given UUID.
    If you're looking to take advantage of unique identifiers then there are alternate methods.
    The base "getNodeByUuid" method will limit its search to the parent namespace.
    Whereas the overload method from the reference class will limit its scope to referenced nodes only

    :type uuid: str
    :rtype: iter
    """

    # Check if uuid requires initializing
    #
    if isinstance(uuid, string_types):

        uuid = om.MUuid(uuid)

    # Add uuid to selection list
    #
    selection = om.MSelectionList()
    selection.add(uuid)

    for i in range(selection.length()):

        yield selection.getDependNode(i)


def iterDependencies(dependNode, apiType, direction=om.MItDependencyGraph.kDownstream, traversal=om.MItDependencyGraph.kDepthFirst):
    """
    Generator method used for collecting dependencies based on the supplied filters.

    :param dependNode: The dependency node to iterate from.
    :type dependNode: om.MObject
    :param apiType: The specific api type to collect.
    :type apiType: int
    :param direction: The direction to traverse in the node graph.
    :type direction: int
    :param traversal: The order of traversal.
    :type traversal: int
    :rtype: iter
    """

    # Initialize dependency graph iterator
    #
    iterDepGraph = om.MItDependencyGraph(
        dependNode,
        filter=apiType,
        direction=direction,
        traversal=traversal,
        level=om.MItDependencyGraph.kNodeLevel
    )

    while not iterDepGraph.isDone():

        # Get current node
        #
        currentNode = iterDepGraph.currentNode()
        yield currentNode

        # Increment iterator
        #
        iterDepGraph.next()


def stripDagPath(name):
    """
    Method used to remove any pipe characters from the supplied name.

    :type name: str
    :rtype: str
    """

    return name.split('|')[-1]


def stripNamespace(name):
    """
    Method used to remove any colon characters from the supplied name.

    :type name: str
    :rtype: str
    """

    return name.split(':')[-1]


def stripAll(name):
    """
    Method used to remove any unwanted characters from the supplied name.

    :type name: str
    :rtype: str
    """

    name = stripDagPath(name)
    name = stripNamespace(name)

    return name


def createDependencyNode(typeName, name=''):
    """
    Creates a node based on the supplied typename or type ID.
    If you wanna create a dag node in world space then supply a null MObject.

    :type typeName: Union[str, int]
    :type name: str
    :rtype: om.MObject
    """

    # Add node to the modifier stack
    #
    dagModifier = om.MDGModifier()
    dependNode = dagModifier.createNode(typeName)

    # Check if a name was supplied
    #
    if len(name) > 0:

        dagModifier.renameNode(dependNode, name)

    # Execute stack
    #
    dagModifier.doIt()
    return dependNode


def createDagNode(typeName, name='', parent=om.MObject.kNullObj):
    """
    Creates a dag node using the supplied type name.

    :type typeName: str
    :type name: str
    :type parent: om.MObject
    :rtype: om.MObject
    """

    # Add node to the modifier stack
    #
    dagModifier = om.MDagModifier()
    dependNode = dagModifier.createNode(typeName, parent=parent)

    # Check if a name was supplied
    #
    if len(name) > 0:

        dagModifier.renameNode(dependNode, name)

    # Execute stack
    #
    dagModifier.doIt()
    return dependNode


def createComponent(indices, apiType=om.MFn.kSingleIndexedComponent):
    """
    Method used to create a component object based on a list of elements and an api enumerator constant.

    :type indices: om.MIntArray
    :type apiType: int
    :rtype: om.MObject
    """

    # Check value type
    #
    if isinstance(indices, om.MIntArray):

        # Create component from function set
        #
        fnSingleIndexComponent = om.MFnSingleIndexedComponent()
        component = fnSingleIndexComponent.create(apiType)

        # Add elements to component
        #
        fnSingleIndexComponent.addElements(indices)

        return component

    elif isinstance(indices, (list, set, tuple, deque)):

        return createComponent(om.MIntArray(indices), apiType=apiType)

    elif isinstance(indices, int):

        return createComponent(om.MIntArray([indices]), apiType=apiType)

    elif indices is None:

        return createComponent(om.MIntArray(), apiType=apiType)

    else:

        raise TypeError('createComponent() expects a list (%s given)!' % type(indices).__name__)


def deleteNode(dependNode):
    """
    Deletes the supplied dependency node from the scene file.
    This operation must be done in chunks starting with breaking connections before deleting the node.

    :type dependNode: om.MObject
    :rtype: None
    """

    # Initialize function set
    #
    fnDependNode = om.MFnDependencyNode(dependNode)
    dagModifier = om.MDagModifier()

    # Break all connections to node
    #
    plugs = fnDependNode.getConnections()

    for plug in plugs:

        # Check if this plug has a source connection
        #
        source = plug.source()

        if not source.isNull:

            log.info('Breaking connection: %s and %s' % (source.info, plug.info))
            dagModifier.disconnect(source, plug)

        # Check if this plug has any destination connections
        #
        destinations = plug.destinations()

        for destination in destinations:

            log.info('Breaking connection: %s and %s' % (plug.info, destination.info))
            dagModifier.disconnect(plug, destination)

    dagModifier.doIt()

    # Finally delete the node
    #
    log.info('Deleting node: %s' % fnDependNode.name())

    dagModifier.deleteNode(dependNode)
    dagModifier.doIt()

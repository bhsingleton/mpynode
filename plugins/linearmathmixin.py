from maya.api import OpenMaya as om
from enum import IntEnum
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Operation(IntEnum):
    """
    Enum class of all available operations.
    """

    ADD = 0
    SUBTRACT = 1
    MULTIPLY = 2
    DIVIDE = 3
    ABSOLUTE = 4
    NEGATE = 5
    HALF = 6
    MIN = 7
    MAX = 8
    AVERAGE = 9
    POW = 10
    ROOT = 11
    SIN = 12
    COS = 13
    TAN = 14
    ASIN = 15
    ACOS = 16
    ATAN = 17
    FLOOR = 18
    CEIL = 19
    ROUND = 20
    TRUNC = 21


class LinearMathMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with linear-math nodes.
    """

    # region Dunderscores
    __plugin__ = 'linearMath'
    # endregion

    # region Enums
    Operation = Operation
    # endregion

    # region Attributes
    operation = mpyattribute.MPyAttribute('operation')
    inFloatA = mpyattribute.MPyAttribute('inFloatA')
    inFloatB = mpyattribute.MPyAttribute('inFloatB')
    inDistanceA = mpyattribute.MPyAttribute('inDistanceA')
    inDistanceB = mpyattribute.MPyAttribute('inDistanceB')
    inAngleA = mpyattribute.MPyAttribute('inAngleA')
    inAngleB = mpyattribute.MPyAttribute('inAngleB')
    inTimeA = mpyattribute.MPyAttribute('inTimeA')
    inTimeB = mpyattribute.MPyAttribute('inTimeB')
    output = mpyattribute.MPyAttribute('output')
    # endregion

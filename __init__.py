
import typing
import logging
import math
import bpy
import mathutils

DEBUG: bool = True
STRICT: bool = False
LOGGER: typing.Optional[logging.Logger] = None
LOG_ERRORS: bool = True

ROTATION_MODE_ITEMS = [
    ('AUTO'         , "Auto Euler"       , "Euler using the rotation order of the target"                                  ),
    ('XYZ'          , "XYZ Euler"        , "Euler using the XYZ rotation order"                                            ),
    ('XZY'          , "XZY Euler"        , "Euler using the XZY rotation order"                                            ),
    ('YXZ'          , "YXZ Euler"        , "Euler using the YXZ rotation order"                                            ),
    ('YZX'          , "YZX Euler"        , "Euler using the YZX rotation order"                                            ),
    ('ZXY'          , "ZXY Euler"        , "Euler using the ZXY rotation order"                                            ),
    ('ZYX'          , "ZYX Euler"        , "Euler using the ZYX rotation order"                                            ),
    ('QUATERNION'   , "Quaternion"       , "Quaternion rotation"                                                           ),
    ('SWING_TWIST_X', "Swing and X Twist", "Decompose into a swing rotation to aim the X axis, followed by twist around it"),
    ('SWING_TWIST_Y', "Swing and Y Twist", "Decompose into a swing rotation to aim the Y axis, followed by twist around it"),
    ('SWING_TWIST_Z', "Swing and Z Twist", "Decompose into a swing rotation to aim the Z axis, followed by twist around it"),
    ]


ROTATION_MODE_INDEX = [
    _item[0] for _item in ROTATION_MODE_ITEMS
    ]

ROTATION_MODE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(ROTATION_MODE_ITEMS)
    }

TRANSFORM_SPACE_ITEMS = [
    ('WORLD_SPACE'    , "World Space"    , "Transforms include effects of parenting/restpose and constraints"    ),
    ('TRANSFORM_SPACE', "Transform Space", "Transforms don't include parenting/restpose or constraints"          ),
    ('LOCAL_SPACE'    , "Local Space"    , "Transforms include effects of constraints but not parenting/restpose"),
    ]

TRANSFORM_SPACE_INDEX = [
    _item[0] for _item in TRANSFORM_SPACE_ITEMS
    ]

TRANSFORM_SPACE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(TRANSFORM_SPACE_ITEMS)
    }

TRANSFORM_TYPE_ITEMS = [
    ('LOC_X'  , "X Location", ""),
    ('LOC_Y'  , "Y Location", ""),
    ('LOC_Z'  , "Z Location", ""),
    ('ROT_W'  , "W Rotation", ""),
    ('ROT_X'  , "X Rotation", ""),
    ('ROT_Y'  , "Y Rotation", ""),
    ('ROT_Z'  , "Z Rotation", ""),
    ('SCALE_X', "X Scale"   , ""),
    ('SCALE_Y', "Y Scale"   , ""),
    ('SCALE_Z', "Z Scale"   , ""),
    ]

TRANSFORM_TYPE_INDEX = [
    _item[0] for _item in TRANSFORM_TYPE_ITEMS
    ]

TRANSFORM_TYPE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(TRANSFORM_TYPE_ITEMS)
    }

def transform_target(object: typing.Optional[bpy.types.Object], bone_target: typing.Optional[str]="") -> typing.Optional[typing.Union[bpy.types.Object, bpy.types.PoseBone]]:

    if object is not None and object.type == 'ARMATURE' and bone_target:
        return object.pose.bones.get(bone_target)
    return object

def transform_matrix(target: typing.Optional[typing.Union[bpy.types.ID, bpy.types.PoseBone]]=None, transform_space: str='WORLD_SPACE') -> mathutils.Matrix:

    if DEBUG:
        if STRICT:
            assert (target is None
                    or isinstance(target, (bpy.types.Object, bpy.types.PoseBone)))

        if not isinstance(transform_space, str):
            message = (f'transform_matrix(target, transform_space): '
                       f'Expected transform_space to be str, '
                       f'not {transform_space.__class__.__name__}')

            if LOG_ERRORS and isinstance(LOGGER, logging.Logger):
                LOGGER.error(message)
            
            raise TypeError(message)

        if transform_space not in TRANSFORM_SPACE_TABLE:
            message = (f'transform_matrix(target, transform_space): '
                       f'transform_space {transform_space} '
                       f'not found in {tuple(TRANSFORM_SPACE_TABLE)}.')

            if LOG_ERRORS and isinstance(LOGGER, logging.Logger):
                LOGGER.error(message)

            raise ValueError(message)

    if isinstance(target, bpy.types.PoseBone):
        if transform_space == 'TRANSFORM_SPACE':
            return target.matrix_channel

        to_space = transform_space[:5]
        if to_space in ('LOCAL', 'WORLD'):
            return target.id_data.convert_space(pose_bone=target,
                                                matrix=target.matrix,
                                                from_space='POSE',
                                                to_space=to_space)

    elif isinstance(target, bpy.types.Object):
        if transform_space == 'TRANSFORM_SPACE' : return target.matrix_basis
        if transform_space == 'WORLD_SPACE'     : return target.matrix_world
        if transform_space == 'LOCAL_SPACE'     : return target.matrix_local

    return mathutils.Matrix.Identity(4)

def transform_matrix_element(matrix: mathutils.Matrix, transform_type: str, rotation_mode: typing.Optional[str]='AUTO', driver: typing.Optional[bool]=False) -> float:

    if DEBUG:
        if STRICT:
            assert isinstance(matrix, mathutils.Matrix)
            assert isinstance(transform_type, str)
            assert isinstance(rotation_mode, str)
            assert isinstance(driver, bool)

        if len(matrix) != 4:
            message = (f'transform_matrix_element(matrix, transform_type, rotation_mode="AUTO", driver=False): '
                       f'Expected matrix to be 4x4, not {len(matrix)}x{len(matrix)}.')

            if LOG_ERRORS and isinstance(LOGGER, logging.Logger):
                LOGGER.error(message)

            raise ValueError(message)

        if transform_type not in TRANSFORM_TYPE_TABLE:
            message = (f'transform_matrix_element(matrix, transform_type, rotation_mode="AUTO", driver=False): '
                       f'transform_type {transform_type} not found in {tuple(TRANSFORM_TYPE_TABLE)}.')

            if LOG_ERRORS and isinstance(LOGGER, logging.Logger):
                LOGGER.error(message)

            raise ValueError(message)

        if rotation_mode not in ROTATION_MODE_TABLE:
            message = (f'transform_matrix_element(matrix, transform_type, rotation_mode="AUTO", driver=False): '
                       f'rotation_mode {rotation_mode} not found in {tuple(ROTATION_MODE_TABLE)}.')

            if LOG_ERRORS and isinstance(LOGGER, logging.Logger):
                LOGGER.error(message)

            raise ValueError(message)

    axis = transform_type[-1]

    if transform_type.startswith('LOC'):
        return matrix.to_translation()['XYZ'.index(axis)]

    if transform_type.startswith('ROT'):

        if rotation_mode == 'AUTO':
            return 0.0 if axis == 'W' else matrix.to_euler()['XYZ'.index(axis)]
        
        if len(rotation_mode) == 3:
            return matrix.to_euler(rotation_mode)['XYZ'.index(axis)]
        
        if rotation_mode == 'QUATERNION':
            return matrix.to_quaternion()['WXYZ'.index(axis)]
        
        twist_axis = rotation_mode[-1]
        swing, twist = matrix.to_quaternion().to_swing_twist(twist_axis)
        
        if axis == twist_axis:
            return twist
        
        value = swing['WXYZ'.index(axis)]
        if driver:
            value = (math.acos if axis == 'W' else math.asin)(value) * 2.0

        return value

    if transform_type.startswith('SCALE'):
        return matrix.to_scale()['XYZ'.index(axis)]

    return 0.0

def transform_matrix_flatten(matrix: mathutils.Matrix) -> typing.Tuple[float, float, float, float,
                                                                       float, float, float, float,
                                                                       float, float, float, float,
                                                                       float, float, float, float]:
    return sum((matrix.col[i].to_tuple() for i in range(4)), tuple())

def transform_matrix_compose(location: typing.Optional[typing.Tuple[float, float, float]]=(0., 0., 0.),
                             rotation: typing.Optional[typing.Tuple[float, float, float, float]]=(1., 0., 0., 0.),
                             scale: typing.Optional[typing.Tuple[float, float, float]]=(1., 1., 1.)) -> None:

    matrix = mathutils.Matrix.Identity(3)
    matrix[0][0] = scale[0]
    matrix[1][1] = scale[1]
    matrix[2][2] = scale[2]

    matrix = (rotation.to_matrix() @ matrix).to_4x4()
    matrix[0][3] = location[0]
    matrix[1][3] = location[1]
    matrix[2][3] = location[2]

    return matrix

def transform_target_distance(target_1: typing.Union[bpy.types.ID, bpy.types.PoseBone, None],
                              target_2: typing.Union[bpy.types.ID, bpy.types.PoseBone, None],
                              transform_space_1: typing.Optional[str]='WORLD_SPACE',
                              transform_space_2: typing.Optional[str]='WORLD_SPACE') -> float:
    m1 = transform_matrix(target_1, transform_space_1)
    m2 = transform_matrix(target_2, transform_space_2)
    return (m1.to_translation() - m2.to_translation()).length
    

# https://github.com/blender/blender/blob/594f47ecd2d5367ca936cf6fc6ec8168c2b360d0/source/blender/blenkernel/intern/fcurve_driver.c
def transform_target_rotational_difference(target_1: typing.Union[bpy.types.ID, bpy.types.PoseBone, None],
                                           target_2: typing.Union[bpy.types.ID, bpy.types.PoseBone, None]) -> float:
    q1 = transform_matrix(target_1).to_quaternion()
    q2 = transform_matrix(target_2).to_quaternion()
    angle = math.fabs(2.0 * math.acos((q1.inverted() * q2)[0]))
    return 2.0 * math.pi - angle if angle > math.pi else angle
#!/usr/bin/env python3

'''Helper module for serializing and deserializing stereonet data.'''

from math import degrees, radians

from grouping import DataGroup
from transformation import Line, Plane, Rotation


def stereonet_object_encoder(obj):
    '''A JSON encoder that handles stereonet objects.

    Designed to be passed as default= to the JSONEncoder constructor.
    '''

    tries = [
        # DataGroup
        lambda o: {'name': o.name, 'enabled': o.enabled, 'style': o.style,
                   'data': o.net_objects()},
        # Line
        lambda o: {'plunge': degrees(o.plunge), 'trend': degrees(o.trend)},
        # Plane
        lambda o: {'strike': degrees(o.strike), 'dip': degrees(o.dip)},
        # Rotation
        lambda o: {'rotation_axis': o.rot_axis, 'base_line': o.base_line},
        # tk.*Var
        lambda o: o.get(),
    ]

    for serialize in tries:
        try:
            return serialize(obj)
        except AttributeError:
            continue
    raise TypeError(f'{type(obj).__name__} {obj}')


def stereonet_object_decoder(obj):
    '''A JSON decoder that correctly handles stereonet objects.

    Designed to be passed as object_hook= to the JSONDecoder constructor.
    '''
    if 'name' in obj and 'enabled' in obj and 'style' in obj and 'data' in obj:
        group = DataGroup(obj['name'], enabled=obj['enabled'], **obj['style'])
        for data in obj['data']:
            group.add_net_object(data)
        return group
    if 'plunge' in obj and 'trend' in obj:
        return Line(**{k: radians(v) for k, v in obj.items()})
    if 'strike' in obj and 'dip' in obj:
        return Plane(**{k: radians(v) for k, v in obj.items()})
    if 'rotation_axis' in obj and 'base_line' in obj:
        obj['rot_axis'] = obj.pop('rotation_axis')
        return Rotation(**obj)
    return obj

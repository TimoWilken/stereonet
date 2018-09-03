#!/usr/bin/env python3

'''Helper module for serializing and deserializing stereonet data.'''

from grouping import DataGroup
from transformation import Line, Plane, Rotation


def stereonet_object_encoder(obj):
    '''A JSON encoder that handles stereonet objects.

    Designed to be passed as default= to the JSONEncoder constructor.
    '''

    tries = [
        # DataGroup
        lambda o: {'name': o.name, 'style': o.style, 'data': o.net_objects},
        # Line
        lambda o: {'plunge': o.plunge, 'trend': o.trend},
        # Plane
        lambda o: {'strike': o.strike, 'dip': o.dip},
        # Rotation
        lambda o: {'rotation_axis': o.rot_axis, 'base_line': o.base_line},
    ]

    for serialize in tries:
        try:
            return serialize(obj)
        except AttributeError:
            continue
    raise TypeError


def stereonet_object_decoder(obj):
    '''A JSON decoder that correctly handles stereonet objects.

    Designed to be passed as object_hook= to the JSONDecoder constructor.
    '''
    if 'name' in obj and 'style' in obj and 'data' in obj:
        group = DataGroup(obj['name'], **obj['style'])
        for data in obj['data']:
            group.add_net_object(data)
        return group
    if 'plunge' in obj and 'trend' in obj:
        return Line(**obj)
    if 'strike' in obj and 'dip' in obj:
        return Plane(**obj)
    if 'rotation_axis' in obj and 'base_line' in obj:
        obj['rot_axis'] = obj.pop('rotation_axis')
        return Rotation(**obj)
    return obj

"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING
import typing

from magicgui import magic_factory

import numpy as np

import napari

if TYPE_CHECKING:
    import napari

try:
    import serialem
except ImportError:
    raise RuntimeError(
        "This plugin requires the SerialEM Python modules to be installed. \n\n"
    )


@magic_factory
def example_magic_widget() -> napari.layers.Image:
    serialem. ConnectToSEM(48888, "146.189.163.56")
    print(serialem.ReportNavFile())
    num_items = serialem.ReportNumTableItems()
    print(num_items)
    maps = []
    map_coordinates = []
    for i in range(1,int(num_items)+1):
        print(f"Item {i}:")
        nav_item_info = serialem.ReportOtherItem(i)
        if int(nav_item_info[4]) == 2:
            serialem.LoadOtherMap(i,"A")
            image = np.asarray(serialem.bufferImage("A")).copy()
            if image.shape[1] == 2880:
                maps.append(image)
                map_coordinates.append(nav_item_info[1:3])
    return napari.layers.Image(np.array(maps), metadata={"decolace_maps": True, "decolace_map_coordinates" : map_coordinates}) 

@magic_factory
def place_center_of_shape(areas: napari.types.ShapesData) -> napari.layers.Points:
    """Place a point at the center of each shape in the layer."""
    points = []
    for area in areas:
        # area is a array of shape (N,3) which is a list of polygons
        # Calculate the center of mass of the polygon
        # Use shapely to calculate the center of mass
        # https://shapely.readthedocs.io/en/stable/manual.html#object.centroid
        points.append(area.center)
    return np.array(points)

    



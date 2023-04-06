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

import shapely
import shapely.affinity

import decolace.acquisition_area

from skimage.transform import warp, AffineTransform

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
    serialem.ConnectToSEM(48888, "146.189.163.56")
    print(serialem.ReportNavFile())
    num_items = serialem.ReportNumTableItems()
    print(num_items)
    maps = []
    map_coordinates = []
    map_navids = []
    for i in range(1,int(num_items)+1):
        print(f"Item {i}:")
        nav_item_info = serialem.ReportOtherItem(i)
        if int(nav_item_info[4]) == 2:
            serialem.LoadOtherMap(i,"A")
            image = np.asarray(serialem.bufferImage("A")).copy()
            if image.shape[1] == 2880:
                maps.append(image)
                map_navids.append(i)
                map_coordinates.append(nav_item_info[1:3])
    return napari.layers.Image(np.array(maps), metadata={"decolace_maps": True, "decolace_map_coordinates" : map_coordinates, "decolace_map_navids" : map_navids}) 


@magic_factory
def place_center_of_shape(areas: napari.layers.Shapes, maps: napari.layers.Image) -> napari.layers.Points:
    """Place a point at the center of each shape in the layer."""
    points = []
    areas = areas.data
    for area in areas:
        
        # area is a array of shape (N,3) which is a list of polygons
        # Calculate the center of mass of the polygon
        # Use shapely to calculate the center of mass
        # https://shapely.readthedocs.io/en/stable/manual.html#object.centroid
        map_id = area[0,0]
        if np.sum(area[:,0] - map_id) != 0:
            raise("Error: Map ID is not the same for all points in the polygon")
        polygon = shapely.geometry.Polygon(area[:,1:3])
        points.append(np.array([map_id,polygon.centroid.x, polygon.centroid.y]))
    for point in points:
        nav_id = maps.metadata["decolace_map_navids"][int(point[0])]
        serialem.LoadOtherMap(nav_id,"A")
        index = serialem.AddImagePosAsNavPoint( "A", point[2], point[1]) 
    print(np.array(points))
    l = napari.layers.Points(np.array(points))
    print(l)
    return l





@magic_factory
def place_hexagonal_cover(areas: napari.layers.Shapes, maps: napari.layers.Image) -> napari.layers.Points:
    """This should create the image_shift position for the acquisition. Save
    them into the decolace state and then plot them on the map.
    1. Polygon is in image coordinates
    2. Add to serialEM and then get stage coordinates.
    3. Convert the stage coordinates to beam-image shift coordinates
    4. Calculate acquisition positions
    5. Save the positions into the decolace state
    6. Convert the image_shift position back to image coordinates"""
    points = []
    order = []
    areas = areas.data
    for i, area in enumerate(areas):
        
        # area is a array of shape (N,3) which is a list of polygons
        # Calculate the center of mass of the polygon
        # Use shapely to calculate the center of mass
        # https://shapely.readthedocs.io/en/stable/manual.html#object.centroid
        map_id = area[0,0]
        if np.sum(area[:,0] - map_id) != 0:
            raise("Error: Map ID is not the same for all points in the polygon")
        polygon = shapely.geometry.Polygon(area[:,1:3])

        acquisition_area = decolace.acquisition_area.AcquisitionAreaSingle(f"area_{i}", "/groups/elferich/decolace_test",beam_radius=0.42,tilt=-20)
        acquisition_area.initialize_from_napari(maps.metadata["decolace_map_navids"][int(map_id)], [polygon.centroid.y, polygon.centroid.x], area[:,1:3])
        acquisition_area.calculate_acquisition_positions_from_napari()
        acquisition_area.write_to_disk()

        # Calculate the affine transformation between area[:,1:3] and
        # acquisition_area.state["corner_positions_specimen"]
        
        transform = AffineTransform()
        transform.estimate(area[:,1:3], acquisition_area.state["corner_positions_specimen"])

        center = transform.inverse(acquisition_area.state["acquisition_positions"])



    # Calculate the affine transformation from     
    return None
    #features = {
    #    'order': np.array(order),
    #}

    # define the color cycle for the face_color annotation
    #face_color_cycle = ['blue', 'green']

    write_to_disktext = {
        'string': '{order}',
        'size': 20,
        'color': 'white',
        'translation': np.array([0, 0]),
    }

    l = napari.layers.Points(np.array(points), size=100, face_color="#00000000", features=features, text=text)
    print(l)
    return l    



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

import decolace

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


def hexagonal_cover(polygon, radius):
    """
    Compute hexagonal grid covering the input polygon using spheres of the given radius.

    Args:
        polygon (shapely.geometry.Polygon): Input polygon
        radius (float): Radius of the spheres

    Returns:
        numpy.ndarray: Array of center of the spheres that hexagonally cover the polygon
    """

    # Define a regular hexagon with side length equal to the sphere radius
    hexagon = shapely.Polygon([(radius*np.cos(angle), radius*np.sin(angle)) for angle in np.linspace(0, 2*np.pi, 7)[:-1]])

    # Compute the bounding box of the polygon
    minx, miny, maxx, maxy = polygon.bounds

    # Compute the offset required to center the hexagonal grid within the bounding box
    dx = hexagon.bounds[2] - hexagon.bounds[0]
    dy = hexagon.bounds[3] - hexagon.bounds[1]
    offsetx = (maxx - minx - dx) / 2
    offsety = (maxy - miny - dy) / 2

    # Compute the number of hexagons required in each direction
    nx = int(np.ceil((maxx - minx - dx/2) / (3*radius))) + 1
    ny = int(np.ceil((maxy - miny - dy/2) / (dy*3/2))) + 1

    # Create an empty list to store the center points of the hexagons
    centers = []

    # Loop over each hexagon in the grid and test if it intersects the input polygon
    for j in range(-ny,ny):
        y = miny + offsety + (j*radius*3/2)
        for i in range(-nx,nx):
            x = minx + offsetx + (i*np.sqrt(3)*radius) + (j%2)*0.5*np.sqrt(3)*radius
            hexagon_center = shapely.Point(x, y)
            if polygon.intersects(shapely.affinity.translate(hexagon, xoff=x, yoff=y)):
                centers.append((x, y))

    return np.array(centers)


@magic_factory
def place_hexagonal_cover(areas: napari.layers.Shapes, maps: napari.layers.Image) -> napari.layers.Points:
    """Place a point at the center of each shape in the layer."""
    points = []
    order = []
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
        print(polygon)
        centers = hexagonal_cover(polygon, 50)
        for i, center in enumerate(centers):
            points.append(np.array([map_id,center[0], center[1]]))
            order.append(i+1)
    print(np.array(points))
   
    features = {
        'order': np.array(order),
    }

    # define the color cycle for the face_color annotation
    face_color_cycle = ['blue', 'green']

    text = {
        'string': '{order}',
        'size': 20,
        'color': 'white',
        'translation': np.array([0, 0]),
    }

    l = napari.layers.Points(np.array(points), size=100, face_color="#00000000", features=features, text=text)
    print(l)
    return l    



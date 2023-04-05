import napari

viewer = napari.Viewer()

# note that the second object returned is your widget instance
dw, import_widget = viewer.window.add_plugin_dock_widget('napari-decolace', 'Example Magic Widget')
dw, my_widget = viewer.window.add_plugin_dock_widget('napari-decolace', 'Place hexagonal cover')

import_widget()
napari.run()

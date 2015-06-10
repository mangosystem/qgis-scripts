"""
/***************************************************************************
Name                 : Load Shapefile Layers from Folder
Description          : Load Shapefile Layers from Folder
Date                 : 25/Dec/2014
copyright            : (C) 2014 by Minpa Lee
email                : mapplus@gmail.com
reference:
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
##[GEEPS]=group
##Load Shapefile Layers from Folder=name
##Shapefile_Folder=folder
##Root_Folder_Only=boolean True
##output=output number

import os, fnmatch
from qgis.core import *
from qgis.utils import iface
from processing.tools.vector import VectorWriter

# function
def find_files(directory, pattern, only_root_directory):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename.lower(), pattern):
                filename = os.path.join(root, basename)
                yield filename
        if (only_root_directory):
            break

# main
count = 0
for src_file in find_files(Shapefile_Folder, '*.shp', Root_Folder_Only):
    (head, tail) = os.path.split(src_file)
    (name, ext) = os.path.splitext(tail)
    vlayer = iface.addVectorLayer(src_file, name, "ogr")
    count += 1

output = count
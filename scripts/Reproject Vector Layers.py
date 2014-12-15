"""
/***************************************************************************
Name                 : Reproject Vector Layers
Description          : Reproject Vector Layers
Date                 : 26/Dec/2014
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
##[My Scripts]=group 
##Select_Vector_Layers=multiple vector
##Dest_CRS=crs EPSG:3857 
##Output_Folder=folder
##Ovewrite=boolean
##output=output number

import os
from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

# is_number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# check target crs : epsg code or wkt crs
# http://www.qgis.org/api/classQgsCoordinateReferenceSystem.html
dest_crs = QgsCoordinateReferenceSystem()
try:
    if Dest_CRS.lower().startswith('+proj'):
        dest_crs.createFromProj4(Dest_CRS)
    elif is_number(Dest_CRS):
        dest_crs.createFromSrid(int(Dest_CRS))
    else:
        dest_crs.createFromString(Dest_CRS)
except Exception as detail:
    raise GeoAlgorithmExecutionException('Invalid Target CRS: %s' % detail)

if not dest_crs.isValid():
    raise GeoAlgorithmExecutionException(Dest_CRS)

# http://www.qgis.org/api/classQgsCoordinateTransform.html
trans = QgsCoordinateTransform()
trans.setDestCRS(dest_crs)

# main
projected = 0
selected_layers = Select_Vector_Layers.split(';')
selected_count = len(selected_layers)
for selected in selected_layers:
    layer = processing.getObject(selected)
    output_path = os.path.join(Output_Folder, layer.name() + '.shp')
    projected += 1
    progress.setPercentage(int(100 * projected / selected_count))
    
    # check exist Ovewrite
    if os.path.isfile(output_path) and Ovewrite == False:
        print "Already exists: " + output_path
        continue
    
    trans.setSourceCrs(layer.crs())
    
    # reprojecting layers
    writer = VectorWriter(output_path, None, layer.dataProvider().fields(), 
                          layer.dataProvider().geometryType(), dest_crs)
    features = processing.features(layer)
    for feature in features:
        # transform geometry http://www.qgis.org/api/classQgsGeometry.html
        geometry = feature.geometry()
        geometry.transform(trans)
        
        # create & insert feature
        new_feature = QgsFeature()
        new_feature.setGeometry(geometry)
        new_feature.setAttributes(feature.attributes())
        writer.addFeature(new_feature)
    del writer

output = selected_count

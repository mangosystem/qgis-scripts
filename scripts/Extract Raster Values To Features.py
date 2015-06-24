"""
/***************************************************************************
Name                 : Extract Raster Values To Features
Description          : Extract Raster Values To Features
Date                 : 19/Jun/2015
copyright            : (C) 2015 by Minpa Lee, Mango System inc.
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
##Extract Raster Values To Features=name
##Target_Vector_Layer=vector
##Target_Fields=string dem
##Source_Raster_Layer=raster
##Raster_Band_Index=number 1
##Result=output string

from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools import dataobjects, vector
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


# is_number
def is_number(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


# =============================================================================
# main
# =============================================================================
vec_layer    = processing.getObject(Target_Vector_Layer)
value_field  = Target_Fields.strip()
raster_layer = processing.getObject(Source_Raster_Layer)
band_index   = int(Raster_Band_Index)

# check crs
crsSrc  = vec_layer.crs()      # vector layer's crs
crsDest = raster_layer.crs()   # raster layer's crs
xform = None
if crsSrc.authid() != crsDest.authid():
    xform = QgsCoordinateTransform(crsSrc, crsDest)

# check field
idx_field = vec_layer.fieldNameIndex(value_field)
if idx_field == -1:
    res = vec_layer.dataProvider().addAttributes( [ QgsField(value_field, QVariant.Double) ] )
    vec_layer.updateFields()
    idx_field = vec_layer.fieldNameIndex(value_field)
   
# Loop through each vector feature
features = processing.features(vec_layer)
point_count = len(features)
current = 1
vec_layer.startEditing()
for feature in features:
    progress.setPercentage(int(100 * current / point_count))
    current += 1
    
    if feature[idx_field] != None:
        continue
    
    # use centroid
    geom = feature.geometry().centroid()
    centroid = geom.asPoint()
    if xform:
        try:
            centroid = xform.transform(geom.asPoint())
        except:
            centroid = None
    
    if centroid:
        # get the raster value of the cell under the vector point
        rasterSample = raster_layer.dataProvider().identify(centroid, QgsRaster.IdentifyFormatValue).results()
        # float() argument must be a string or a number See log for more details
        if not is_number(rasterSample[band_index]):
            continue
            
        # the key is the raster band, and the value is the cell's raster value
        elevation = float(rasterSample[band_index])  # band index
        vec_layer.changeAttributeValue(int(feature.id()), idx_field, elevation)
        
vec_layer.commitChanges()
Result = str(current)

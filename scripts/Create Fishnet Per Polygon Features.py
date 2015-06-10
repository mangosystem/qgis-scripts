"""
/***************************************************************************
Name                 : Create Fishnet Per Polygon Features
Description          : Create Fishnet Per Polygon Features
Date                 : 03/April/2015
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
##Create Fishnet Per Polygon Features=name
##Input_Layer=vector polygon
##UniqueId_Field=field Input_Layer
##Name_Field=field Input_Layer
##Tile_Width=number 2100
##Tile_Height=number 1485
##Readjust_Center=boolean True
##Output_Layer=output vector

import math
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


def create__rectangle_polygon(center, width, height):
    xmin = center.x() - (width / 2.0)
    ymin = center.y() - (height / 2.0)
    
    bounds = QgsRectangle(xmin, ymin, xmin + width, ymin + height)
    return QgsGeometry.fromRect(bounds)
    
    
def calculate_columns_rows(bbox, width, height, readjustCenter):
    columns = int(math.floor((bbox.width() / width) + 0.5))
    rows    = int(math.floor((bbox.height() / height) + 0.5))
    
    columns = columns + 1 if columns * width < bbox.width() else columns
    rows    = rows + 1 if rows * height < bbox.height() else rows
    
    if readjustCenter:
        # readjust center & create new boundingbox
        center = bbox.center()    # QgsPoint        
        xmin   = center.x() - ((columns * width) / 2.0)
        ymin   = center.y() - ((rows * height) / 2.0)
        return QgsRectangle(xmin, ymin, xmin + width, ymin + height), columns, rows
    else:
        return bbox, columns, rows
  
  
# =============================================================================
# main
# =============================================================================
width = float(Tile_Width)
height = float(Tile_Height)
if width == 0 or height == 0:
    raise GeoAlgorithmExecutionException('Tile Width & Height values must be greater than 0')
    
input_layer  = processing.getObject(Input_Layer)
input_fields = input_layer.pendingFields()

# output fields : zone name, zone id, tile id
Tid_Field = "tile_id"

tile_fields = QgsFields()
tile_fields.append(input_fields.field(Name_Field))
tile_fields.append(input_fields.field(UniqueId_Field))
tile_fields.append(QgsField(Tid_Field, QVariant.Int))

# write features
writer = VectorWriter(Output_Layer, None, tile_fields, QGis.WKBPolygon, input_layer.crs())
features = processing.features(input_layer)
for feature in features:
    geometry = feature.geometry() # QgsGeometry
    nameVal = feature.attribute(Name_Field)
    uidVal  = feature.attribute(UniqueId_Field)
    
    bbox, columns, rows = calculate_columns_rows(geometry.boundingBox(), width, height, Readjust_Center)
    
    tileID = 1
    # Tile ID direction: upper left --> lower right
    for row in range(rows, 0, -1):
        ymax = bbox.yMinimum() + (height * row)
        for column in range(columns):
            xmin = bbox.xMinimum() + (width * column)
            
            bounds = QgsRectangle(xmin, ymax - height, xmin + width, ymax)
            polygon = QgsGeometry.fromRect(bounds)
            if geometry.disjoint(polygon):
              continue
    
            tile_feature = QgsFeature(tile_fields)
            tile_feature.setGeometry(polygon)
            #tile_feature.setAttributes([nameVal, uidVal, tileID])
            tile_feature.setAttribute(Name_Field, nameVal)
            tile_feature.setAttribute(UniqueId_Field, uidVal)
            tile_feature.setAttribute(Tid_Field, tileID)
            writer.addFeature(tile_feature)
            tileID += 1
del writer
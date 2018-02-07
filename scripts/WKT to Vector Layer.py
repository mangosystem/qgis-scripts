"""
/***************************************************************************
Name                 : WKT to Vector Layer
Description          : WKT to Vector Layer
Date                 : 06/Feb/2018
copyright            : (C) 2015 by Minpa Lee
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
##WKT to Vector Layer=name
##Well_Known_Text=longstring POINT(194051.466 447861.743)
##Output=output vector

from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import iface
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


# import from WKT geometry
try:
    geometry = QgsGeometry.fromWkt(Well_Known_Text)
except Exception as detail:
    raise GeoAlgorithmExecutionException('Invalid WKT Geometry: %s' % detail)
    
# set CRS
crs = iface.mapCanvas().mapRenderer().destinationCrs()
    
# create vector layer
fields = QgsFields()
fields.append(QgsField('id', QVariant.Int))
fields.append(QgsField('type', QVariant.String))

writer = VectorWriter(Output, None, fields, geometry.wkbType(), crs)

# create & write feature
feature = QgsFeature(fields)
feature.setGeometry(geometry)
feature.setAttribute('id', 1)
feature.setAttribute('type', geometry.wkbType())

writer.addFeature(feature)
    
del writer

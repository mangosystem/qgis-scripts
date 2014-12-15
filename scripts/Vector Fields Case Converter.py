"""
/***************************************************************************
Name                 : Vector Field Case Converter
Description          : Vector Field Case Converter
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
##[My Scripts]=group
##Vector_Layer=vector
##Upper_Case=boolean
##Output=output vector

from qgis.core import *
from processing.tools.vector import VectorWriter

vectorLayer = processing.getObject(Vector_Layer)
provider = vectorLayer.dataProvider()

# rebuild fields
new_fields = QgsFields()
for field in provider.fields():
    field_name = field.name().upper() if Upper_Case else field.name().lower()
    field.setName(field_name)
    new_fields.append(field)
    
# write features
writer = VectorWriter(Output, None, new_fields, provider.geometryType(), vectorLayer.crs())

features = processing.features(vectorLayer)
for feature in features:
    writer.addFeature(feature)

del writer

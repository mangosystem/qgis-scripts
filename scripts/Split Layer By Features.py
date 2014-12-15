"""
/***************************************************************************
Name                 : Split Layer By Features
Description          : Split Layer By Features
Date                 : 06/Oct/2014
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
##Input_Layer_To_Be_Splitted=vector
##Split_Layer=vector polygon
##Unique_Value_Field=field Split_Layer
##Use_Prefix_As_Layer_Name=boolean True
##Multipart_To_Singleparts=boolean
##Output_Folder=folder
##number=output number

import os
from PyQt4.QtCore import *
from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


# from MultipartToSingleparts.py
def multiToSingleGeom(wkbType):
    try:
        if wkbType in (QGis.WKBPoint, QGis.WKBMultiPoint,
                       QGis.WKBPoint25D, QGis.WKBMultiPoint25D):
            return QGis.WKBPoint
        elif wkbType in (QGis.WKBLineString, QGis.WKBMultiLineString,
                         QGis.WKBMultiLineString25D,
                         QGis.WKBLineString25D):
            return QGis.WKBLineString
        elif wkbType in (QGis.WKBPolygon, QGis.WKBMultiPolygon,
                         QGis.WKBMultiPolygon25D, QGis.WKBPolygon25D):
            return QGis.WKBPolygon
        else:
            return QGis.WKBUnknown
    except Exception, err:
        raise GeoAlgorithmExecutionException(unicode(err))


# from MultipartToSingleparts.py
def extractAsSingle(geom):
    multiGeom = QgsGeometry()
    geometries = []
    if geom.type() == QGis.Point:
        if geom.isMultipart():
            multiGeom = geom.asMultiPoint()
            for part in multiGeom:
                geometries.append(QgsGeometry().fromPoint(part))
        else:
            geometries.append(geom)
    elif geom.type() == QGis.Line:
        if geom.isMultipart():
            multiGeom = geom.asMultiPolyline()
            for part in multiGeom:
                geometries.append(QgsGeometry().fromPolyline(part))
        else:
            geometries.append(geom)
    elif geom.type() == QGis.Polygon:
        if geom.isMultipart():
            multiGeom = geom.asMultiPolygon()
            for part in multiGeom:
                geometries.append(QgsGeometry().fromPolygon(part))
        else:
            geometries.append(geom)
    return geometries

# check layer and field
input_layer = processing.getObject(Input_Layer_To_Be_Splitted)
provider = input_layer.dataProvider()
output_geometry_type = provider.geometryType()
if Multipart_To_Singleparts:
    output_geometry_type = multiToSingleGeom(provider.geometryType())

split_layer = processing.getObject(Split_Layer)
uv_index = split_layer.fieldNameIndex(Unique_Value_Field)
if uv_index == -1:
    raise GeoAlgorithmExecutionException(Unique_Value_Field + ' does not exist.')

# if split layer's crs is differenf from input layer's crs, create coordinate transform
trans = None
if input_layer.crs().authid() != split_layer.crs().authid():
    trans = QgsCoordinateTransform()
    trans.setDestCRS(input_layer.crs())
    trans.setSourceCrs(split_layer.crs())

current = 0
split_features = processing.features(split_layer)
total = 100.0 / float(len(split_features))
for split_feature in split_features:
    current += 1
    progress.setPercentage(int(current * total))
    
    # if necessary transform geometry
    split_geometry = split_feature.geometry()
    if trans:
        split_geometry.transform(trans)
    
    # boundingbox filter
    filter = QgsFeatureRequest().setFilterRect(split_geometry.boundingBox())
    features = input_layer.getFeatures(filter)
    
    writer = None
    new_feature = QgsFeature()
    for feature in features:
        # check intersects
        orig_geometry = feature.geometry()
        if split_geometry.intersects(orig_geometry):
            new_feature.setAttributes(feature.attributes())
            # perform intersection
            splitted = orig_geometry.intersection(split_geometry)
            if splitted and not splitted.isGeosEmpty() and orig_geometry.type() == splitted.type():
                if not writer:
                    # prefix name = layer name or S
                    prefix_name = input_layer.name() if Use_Prefix_As_Layer_Name == True else u'S'
                    uv_value = split_feature.attributes()[uv_index]
                    out_file = os.path.join(Output_Folder, prefix_name + u'_' + unicode(str(uv_value)) + u'.shp')
                    writer = VectorWriter(out_file, None, provider.fields(), output_geometry_type, input_layer.crs())
                
                # insert feature(s)
                if Multipart_To_Singleparts:
                    geometries = extractAsSingle(splitted)
                    for single_geom in geometries:
                        new_feature.setGeometry(single_geom)
                        writer.addFeature(new_feature)
                else:
                    new_feature.setGeometry(splitted)
                    writer.addFeature(new_feature)
    if writer: 
        del writer
    del filter

number = current

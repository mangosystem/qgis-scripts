"""
/***************************************************************************
Name                 : Raster Extract by Attributes
Description          : Raster Extract by Attributes
Date                 : 15/March/2015
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
##[My Scripts]=group
##Raster Extract by Attributes=name
##Input_Raster=raster
##Expresesion=string Value >= 0
##Output=output raster

import struct
from osgeo import gdal
from osgeo.gdalconst import *
from qgis.core import *
from PyQt4.QtCore import *
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


RASTER_TYPES ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}


# =============================================================================
# main
# =============================================================================
if len(Expresesion.strip()) == 0:
    raise GeoAlgorithmExecutionException('Where Clause required!')

user_expression = Expresesion.lower()
# =============================================================================
# create output raster
# =============================================================================
layer = processing.getObject(Input_Raster)
inputDs = gdal.Open(unicode(layer.source()), GA_ReadOnly)
band = inputDs.GetRasterBand(1)
nodata = band.GetNoDataValue()

driver = gdal.GetDriverByName('GTiff')
outputDs = driver.Create(Output, inputDs.RasterXSize, inputDs.RasterYSize, 1, band.DataType)
outputDs.SetProjection(inputDs.GetProjection())
outputDs.SetGeoTransform(inputDs.GetGeoTransform())
outputBand = outputDs.GetRasterBand(1)
outputBand.SetNoDataValue(nodata)

# =============================================================================
# extrace by attributes
# =============================================================================
fields = QgsFields()
fields.append(QgsField('value', QVariant.Double))

exp = QgsExpression(user_expression)
exp.prepare(fields)
feature = QgsFeature(fields)

data_type  = RASTER_TYPES[gdal.GetDataTypeName(band.DataType)]
for y in xrange(band.YSize):
    progress.setPercentage(y / float(band.YSize) * 100)
    scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1, band.DataType)
    values = struct.unpack(data_type * band.XSize, scanline)
    
    output = ''
    for value in values:
        raster_value = nodata
        if value != nodata:
            #exp = QgsExpression(user_expression.replace('value', str(value)))
            feature.setAttribute(0, value)
            if bool(exp.evaluate(feature)):
              raster_value = value
            else:
              raster_value = nodata
        output = output + struct.pack(data_type, raster_value)
            
    # write line
    outputBand.WriteRaster(0, y, band.XSize, 1, output, buf_xsize=band.XSize, buf_ysize=1, buf_type=band.DataType)
    del output

outputDs.FlushCache()
outputDs = None
inputDs = None

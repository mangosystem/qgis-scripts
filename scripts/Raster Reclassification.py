"""
/***************************************************************************
Name                 : Raster Reclassification
Description          : Raster Reclassification
Date                 : 14/March/2015
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
##Raster Reclassification=name
##Input_Raster=raster
##Reclassify_Ranges=string 0 10 1; 10 20 2; 20 100 3
##Output_Raster_Type=selection Int32;Float32
##Output=output raster

import sys, struct, math
from osgeo import gdal
from osgeo.gdalconst import *
from qgis.core import *
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


OUTPUT_TYPES = ['Int32','Float32']
RASTER_TYPES ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}


# =============================================================================
# main
# =============================================================================
if len(Reclassify_Ranges.strip()) == 0:
    raise GeoAlgorithmExecutionException('Reclassify Ranges values required!')

min_values = []
max_values = []
reclass_values  = []
reclass_ranges = Reclassify_Ranges.strip().split(';')
for reclass in reclass_ranges:
    reclass_intervals = reclass.strip().split()
    min_values.append(float(reclass_intervals[0]))
    max_values.append(float(reclass_intervals[1]))
    reclass_values.append(float(reclass_intervals[2]))
    
# =============================================================================
# create output raster
# =============================================================================
layer = processing.getObject(Input_Raster)
inputDs = gdal.Open(unicode(layer.source()), GA_ReadOnly)
band = inputDs.GetRasterBand(1)
nodata = band.GetNoDataValue()
gdal_output_type = gdal.GetDataTypeByName(OUTPUT_TYPES[Output_Raster_Type])

driver = gdal.GetDriverByName('GTiff')
outputDs = driver.Create(Output, inputDs.RasterXSize, inputDs.RasterYSize, 1, gdal_output_type)
outputDs.SetProjection(inputDs.GetProjection())
outputDs.SetGeoTransform(inputDs.GetGeoTransform())
outputBand = outputDs.GetRasterBand(1)
outputBand.SetNoDataValue(nodata)

# =============================================================================
# reclass raster
# =============================================================================
input_data_type  = RASTER_TYPES[gdal.GetDataTypeName(band.DataType)]
output_data_type = RASTER_TYPES[OUTPUT_TYPES[Output_Raster_Type]]
for y in xrange(band.YSize):
    progress.setPercentage(y / float(band.YSize) * 100)
    scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1, band.DataType)
    values = struct.unpack(input_data_type * band.XSize, scanline)
    
    output = ''
    for value in values:
        reclassValue = value
        if value == nodata:
            reclassValue = nodata
        else:
            for index in range(len(reclass_values)):
                if value >= min_values[index] and value < max_values[index]:
                    reclassValue = reclass_values[index]
                    break
                
        reclassValue = int(reclassValue) if Output_Raster_Type == 0 else float(reclassValue)
        output = output + struct.pack(output_data_type, reclassValue)
            
    # write line
    outputBand.WriteRaster(0, y, band.XSize, 1, output, buf_xsize=band.XSize, buf_ysize=1, buf_type=gdal_output_type)
    del output

outputDs.FlushCache()
outputDs = None
inputDs = None

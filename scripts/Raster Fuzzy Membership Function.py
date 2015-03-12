"""
/***************************************************************************
Name                 : Raster Fuzzy Membership Function
Description          : Raster Fuzzy Membership Function
Date                 : 10/March/2015
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
##Raster Fuzzy Membership Function=name
##Input_Raster=raster
##Degree_Of_Membership=number 1
##Function_Type=selection Linear;Jshaped;Sigmoidal
##IsDecrease=boolean
##Output=output raster

import sys, struct, math
from osgeo import gdal
from osgeo.gdalconst import *
from qgis.core import *


TYPES ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}


# =============================================================================
# min max calculation function
# =============================================================================
def calculate_min_max(band):
  nodata = band.GetNoDataValue()
  minvalue = sys.float_info.max
  maxvalue = sys.float_info.min
  datatype = TYPES[gdal.GetDataTypeName(band.DataType)]
  for y in xrange(band.YSize):
      progress.setPercentage(y / float(band.YSize) * 100)
      scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1, band.DataType)
      values = struct.unpack(datatype * band.XSize, scanline)
      for value in values:
          if value == nodata:
              continue
          minvalue = min(value, minvalue)
          maxvalue = max(value, maxvalue)
  return minvalue, maxvalue


# =============================================================================
# main
# =============================================================================
layer = processing.getObject(Input_Raster)
inputDs = gdal.Open(unicode(layer.source()), GA_ReadOnly)
band = inputDs.GetRasterBand(1)
nodata = band.GetNoDataValue()

# =============================================================================
# calculate min, max value
# =============================================================================
minvalue, maxvalue = calculate_min_max(band)

# calculate min, max value from qgs interface
#rasterInterface = layer.dataProvider().clone()
#bandStat = rasterInterface.bandStatistics(1, QgsRasterBandStats.All, layer.extent(), 0)
#minvalue = bandStat.minimumValue
#maxvalue = bandStat.maximumValue

# =============================================================================
# create output raster : always gdal.GDT_Float32
# =============================================================================
driver = gdal.GetDriverByName('GTiff')
outputDs = driver.Create(Output, inputDs.RasterXSize, inputDs.RasterYSize, 1, gdal.GDT_Float32)
outputDs.SetProjection(inputDs.GetProjection())
outputDs.SetGeoTransform(inputDs.GetGeoTransform())
outputBand = outputDs.GetRasterBand(1)
outputBand.SetNoDataValue(nodata)

# =============================================================================
# calculate fuzzy membership function
# =============================================================================
for y in xrange(band.YSize):
    progress.setPercentage(y / float(band.YSize) * 100)
    scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1, band.DataType)
    values = struct.unpack(TYPES[gdal.GetDataTypeName(band.DataType)] * band.XSize, scanline)
    
    output = ''
    for value in values:
        fuzzy = value
        if value == nodata:
            fuzzy = nodata
        else:
            dx = float(value - minvalue)
            dw = float(maxvalue - minvalue)
            if dw == 0:
                fuzzy = 0.0
            else:
                if Function_Type == 1:   # JSHAPED
                    fuzzy = 1.0 / (1.0 + math.pow((dw - dx) / dw, 2.0))
                elif Function_Type == 2: # SIGMOIDAL
                    fuzzy = math.pow(math.sin((dx / dw) * (math.pi / 2.0)), 2.0)
                else:                   # LINEAR
                    fuzzy = dx / dw;
            if IsDecrease :
              fuzzy = 1.0- fuzzy
              
        fuzzy = Degree_Of_Membership * fuzzy
        output = output + struct.pack(TYPES[gdal.GetDataTypeName(gdal.GDT_Float32)], fuzzy)
            
    # write line
    outputBand.WriteRaster(0, y, band.XSize, 1, output, buf_xsize=band.XSize, buf_ysize=1, buf_type=gdal.GDT_Float32)
    del output

outputDs.FlushCache()
outputDs = None
inputDs = None

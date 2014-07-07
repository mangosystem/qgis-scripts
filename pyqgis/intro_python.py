# -*- coding: utf-8 -*-
"""
# The Python Tutorial
# https://wikidocs.net/book/1
# http://docs.python.org/2/tutorial/index.html
"""

#===================================
# 모듈 참조
#===================================
from 모듈이름 import 모듈함수

# PyQt
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# QGIS
from qgis.core import *
from qgis.gui import *

# 경로 등 내장 함수
from glob import glob
from os import path

#===================================
# 자료형
#===================================
# string 
say = "Python is very easy."
print say[2]
print say[:6]

print '한글'
print u'한글'

# number
a = 3   # int
b = 4   # int
print a / b
print float(a) / b

print say + ' ' + str(a)
print say[4] * 20

# list
list = [1,3,5,7,9]
print len(list)
if 3 in list:
    print 'exist'
else:
    print 'not exist'

#===================================
# 제어문
#===================================
# java for loop
# for (int i = 0; i < 10; i++) {
#     System.out.println(i);
# }

# for
for i in list:
    print i,

for i in range(10):
    print i

for i in range(2, 10):
    print i

for i in range(10, -1, -1):
    print i,

# while
treeHit = 0
while 1:
    treeHit = treeHit + 1
    if treeHit == 10:
        print "last 10"
        break
    elif treeHit == 1:
        print "first 1"
    else:
        print treeHit

#===================================
# Function & Class
#===================================
# function
def sum(a, b): 
    return a + b

print sum(3, 4)

# function
def sum_and_mul(a, b): 
    return (a + b, a * b)

print sum_and_mul(3, 4)
(s, m) = sum_and_mul(3, 4)

# class
class Person:
    def __init__(self, name):
        self.name = name
        
    def greet(self):
        print 'Hello ' + self.name
    
    @staticmethod
    def static_greet(name):
        print 'Hello ' + name

pp = Person('QGIS')
pp.greet()
Person.static_greet('QGIS')

#===================================
# 기타
#===================================
# math
import math

print math.pi
print math.pow(2, 3)

# system
import sys
sys.path.append("C:\OpenGeoSuite\pyqgis") 

# lambda
# lambda = 인수1, 인수2, ...  : 인수를 이용한 표현식
sum = lambda a, b: a+b 
sum(3,4) 

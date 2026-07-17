#coding: utf-8
'''
This module contains a variety of generally useful utility methods.

@author: Cory Banack (original), refactored by Local CV Scraper Team
and further adapted by Strumples & Gemini for Grand Comics DB.
'''

import re
import sys
from time import strftime
import clr
from gcd_resources import Resources

clr.AddReference('System')
from System.IO import File, StreamReader, StreamWriter, StringWriter
from System.Text import Encoding
from System.Net import HttpStatusCode, WebException, WebRequest
from System.Net import ServicePointManager, SecurityProtocolType

clr.AddReference('System.Drawing')
from System.Drawing import Graphics, Bitmap

clr.AddReference('System.Web')
from System.Web import HttpUtility

clr.AddReference('IronPython')
from IronPython.Compiler import CallTarget0 

# unmodifiable cache for speeding up calls to natural_compare 
__keys_cache = None 

#==============================================================================
def is_string(object):
   ''' returns a boolean indicating whether the given object is a string '''
   if object is None:
      return False
   return isinstance(object, basestring)


#==============================================================================
def is_number(s):
   ''' returns a boolean indicating whether the given object is a number, or
       a string that can be converted to a number. '''
   try:
      float(s)
      return True
   except:
      return False


#==============================================================================
def sstr(object):
   ''' safely converts the given object into a string (sstr = safestr) '''
   if object is None:
      return '<None>'
   if is_string(object):
      return object 
   return str(object)


# ==========================================================================
def natural_compare(a, b): 
   ''' Compares two strings using their "natural" ordering. '''
   global __keys_cache
   if __keys_cache is None:
      __keys_cache = { str(x): natural_key(str(x)) for x in range(999) }
      
   a = __keys_cache[a] if a in __keys_cache else natural_key(a)
   b = __keys_cache[b] if b in __keys_cache else natural_key(b)
   return -1 if a < b else 1 if a > b else 0


# ==========================================================================
def natural_key(s):
   ''' Calculates the natural sort order key for the given string. '''
   s = s.strip()
   
   def unicode_fraction_to_float(s):
      number = None
      match = re.match("\s*(-?)\s*(\d*)\s*([⅛⅙⅕¼⅓⅜⅖½⅗⅝⅔¾⅘⅚⅞])\s*", s) 
      if match:
         negative = match.group(1)
         intpart = match.group(2)
         intpart = float(intpart) if is_number(intpart) else 0
         fracs = {"⅛":1.0/8 ,"⅙":1.0/6,"⅕":0.2,"¼":0.25,"⅓":1.0/3,
                  "⅜":3.0/8, "⅖":0.4,"½":0.5,"⅗":0.6,"⅝":5.0/8,
                  "⅔":2.0/3,"¾":0.75,"⅘":0.8,"⅚":5.0/6,"⅞":7.0/8}
         fracpart = match.group(3)
         fracpart = fracs[fracpart] if fracpart in fracs else 0
         number = -1*(intpart+fracpart) if negative else intpart+fracpart
      return number
   
   unicode_float = unicode_fraction_to_float(s)
   if unicode_float:
      return ['', unicode_float, '' ]
   else:
      pattern = r'((?:^\s*-)?(?:(?:\d+\.\d+)|(?:\.\d+)|(?:\d+\.)|(?:\d+)))'
      convert = lambda text: float(text) if is_number(text) \
         else text.lower().strip()
      return [ convert(c) for c in re.split( pattern, s) ]


# ==========================================================================
def invoke(control, delegate, synchronous = True): 
   ''' Invokes the given delegate on the GUI thread safely. '''
   if not control or not delegate:
      raise TypeError("null parameter not allowed!")
   
   if control.IsHandleCreated and \
         not control.IsDisposed and not control.Disposing:
      try:
         if synchronous:
            if control.InvokeRequired:
               control.Invoke(CallTarget0(delegate))
            else:
               delegate()
         else:
            control.BeginInvoke(CallTarget0(delegate))
      except: 
         if sys.exc_info()[0].__name__ == "SystemError" and \
               sstr(sys.exc_info()[1]).find("handle") != -1:
            pass 
         else:
            raise


#==============================================================================
def convert_roman_numerals(num_s):
   ''' Converts Regular or Roman numerals to integers. '''
   roman_mapping = {'i':1, 'ii':2,'iii':3,'iv':4,'v':5,'vi':6,'vii':7,'viii':8,
                    'ix':9,'x':10,'xi':11,'xii':12,'xiii':13,'xiv':14,'xv':15,
                    'xvi':16,'xvii':17,'xviii':18,'xix':19,'xx':20}
   
   num_s = num_s.replace(' ', '').strip().lower()
   negative = num_s.startswith('-')
   if negative:
      num_s = num_s[1:]
   
   retval = None
   try:
      retval = int(num_s)
   except:
      retval = roman_mapping[num_s]
   
   return retval * -1 if negative else retval


#==============================================================================
def convert_number_words(phrase_s, expand_b):
   ''' Maps and converts number words safely. '''
   number_map = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three',\
      '4': 'four', '5': 'five', '6': 'six','7': 'seven', '8': 'eight',\
      '9': 'nine', '10': 'ten', '11': 'eleven', '12': 'twelve',\
      '13': 'thirteen', '14': 'fourteen', '15': 'fifteen',\
      '16': 'sixteen', '17': 'seventeen', '18': 'eighteen', '19': 'nineteen',\
      '20': 'twenty', '0th': 'zeroth', '1rst': 'first', '2nd': 'second',\
      '3rd': 'third', '4th': 'fourth', '5th': 'fifth', '6th': 'sixth',\
      '7th': 'seventh', '8th': 'eighth', '9th': 'ninth', '10th': 'tenth',\
      '11th': 'eleventh', '12th': 'twelveth', '13th': 'thirteenth',\
      '14th': 'fourteenth', '15th': 'fifteenth', '16th': 'sixteenth',\
      '17th': 'seventeenth', '18th': 'eighteenth', '19th': 'nineteenth',\
      '20th': 'twentieth'}

   b = r'\b'
   if expand_b:
      for (x,y) in number_map.iteritems():
         phrase_s = re.sub(b+x+b, y, phrase_s)
      phrase_s = re.sub(r'\b1st\b', 'first', phrase_s)
   else:
      for (x,y) in number_map.iteritems():
         phrase_s = re.sub(b+y+b, x, phrase_s)
      phrase_s = re.sub(r'\btwelfth\b', '12th', phrase_s)
      phrase_s = re.sub(r'\beightteenth\b', '18th', phrase_s)
   return phrase_s


#==============================================================================
def persist_map(map, file):
   ''' Saves configuration mappings to a file. '''
   try:
      import gcd_log as log
      with StreamWriter(file, False, Encoding.UTF8) as sw:
         sw.Write(":: This file was generated on "\
            + strftime(r'%Y.%m.%d %X') + "\n\n")
         keys = map.keys()
         keys.sort()
         for key in keys:
            value = sstr(map[key]).strip()
            key = sstr(key).strip()
            if ':' in key or ':' in value:
               log.debug("WARNING: can't write map entry containing ':'; " + str(key) + " -> " + str(value))
            else:
               sw.Write(key + ' : ' + value + "\n")
      return True
   except Exception as ex:
      import gcd_log as log
      log.debug_exc("problem persisting map to file: " + sstr(file))
      return False 
         
         
#==============================================================================
def load_map(file):
   ''' Loads saved map settings files from disk. '''
   retval = {}
   try:
      if File.Exists(file): 
         with StreamReader(file, Encoding.UTF8, False) as sr:
            line = sr.ReadLine()
            while line is not None:
               pair = line.strip().split(':') 
               if len(pair) == 2:
                  key = pair[0].strip()
                  value = pair[1].strip()
                  if value.lower() == "false":
                     value = False
                  elif value.lower() == "true":
                     value = True 
                  else: 
                     try: 
                        if '.' in value: value = float(value)
                        else: value = int(value)
                     except:
                        pass
                  retval[key] = value
               line = sr.ReadLine()
   except:
      import gcd_log as log
      log.debug_exc("problem loading map from file " + sstr(file))
      retval = {}
   return retval


#==============================================================================
def persist_string(s, file):
   ''' Saves raw string data maps to files. '''
   try:
      import gcd_log as log
      with StreamWriter(file, False, Encoding.UTF8) as sw:
         sw.Write(s)
      return True
   except:
      import gcd_log as log
      log.debug_exc("problem persisting string to file: " + sstr(file))
      return False 
         
         
#==============================================================================
def load_string(file):
   ''' Loads raw string records from text files. '''
   retval = ""
   try:
      if File.Exists(file): 
         with StreamReader(file, Encoding.UTF8, False) as sr:
            retval = sr.ReadToEnd()
   except:
      import gcd_log as log
      log.debug_exc("problem loading string from file " + sstr(file))
      retval = ""
   return retval


#==============================================================================
def strip_back_cover(image):
   ''' Trims out double-page spread canvas elements. '''
   if image:
      pixel_ratio = float(image.Width)/float(image.Height)
      if pixel_ratio < 1.5 and pixel_ratio > 1.2:
         new_image = Bitmap(int(image.Width/2), image.Height)
         graphics = Graphics.FromImage(new_image)
         graphics.DrawImage(image, -int(image.Width/2), 0)
         graphics.Dispose()
         image.Dispose()
         image = new_image
   return image


#==============================================================================
def get_html_string(url):
   ''' Bypassed/Stubbed placeholder method. '''
   return ""
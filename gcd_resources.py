#coding: utf-8
'''
This module contains the Resources class.
'''
import sys
import clr

clr.AddReference('System.Drawing')
from System.Drawing import Image, Bitmap

clr.AddReference('System')
from System import Environment
from System.IO import Directory, File, Path

#==============================================================================
class Resources(object):
   # Per-user data folder name, under %APPDATA%
   PROFILE_DIRECTORY_NAME = 'Local Grand Comics Database Scraper'

   PROFILE_DIRECTORY = None
   LOG_DIRECTORY = None
   LOCAL_CACHE_DIRECTORY = None
   SETTINGS_FILE = None
   ADVANCED_FILE = None
   GEOMETRY_FILE = None
   SERIES_FILE = None
   I18N_DEFAULTS_FILE = None
   
   # Unique XML identifier for your standalone version
   I18N_XML_ENTRY = 'Script.GCDLocalScraper.xml'
   SCRIPT_VERSION = "1.0.0"
   SCRIPT_FULLNAME = 'Local GCD Scraper - v' + SCRIPT_VERSION

   #==============================================================================
   @classmethod
   def initialize(cls):
      ''' Initializes directory structures and paths for configuration. '''
      script_dir = Directory.GetParent(__file__).FullName
      
      profile_dir = cls.get_profile_directory()

      cls.PROFILE_DIRECTORY = profile_dir
      cls.LOG_DIRECTORY = Path.Combine(profile_dir, 'logs')
      cls.SETTINGS_FILE = Path.Combine(profile_dir, 'settings.dat')
      cls.ADVANCED_FILE = Path.Combine(profile_dir, 'advanced.dat')
      cls.GEOMETRY_FILE = Path.Combine(profile_dir, 'geometry.dat')
      cls.SERIES_FILE = Path.Combine(profile_dir, 'series.dat')
      cls.LOCAL_CACHE_DIRECTORY = Path.Combine(profile_dir, 'localCache')
      cls.I18N_DEFAULTS_FILE = Path.Combine(script_dir, 'en.zip')
      
      if not Directory.Exists(profile_dir):
         Directory.CreateDirectory(profile_dir)

   #===========================================================================
   @classmethod
   def get_profile_directory(cls):
      ''' Returns this plugin's per-user data folder (it may not exist yet). '''
      return Path.Combine(
         Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
         cls.PROFILE_DIRECTORY_NAME)

   #===========================================================================
   @classmethod
   def createGCDLogo(cls):
      ''' Loads the primary GCD logo or returns a blank fallback bitmap. '''
      dir = Directory.GetParent(__file__).FullName + "\\"
      if File.Exists(dir + 'localscraper.png'):
         return Image.FromFile(dir + 'localscraper.png')
      return Bitmap(100, 100)

   #===========================================================================
   @classmethod
   def createArrowIcon(cls, left=True, full=True):
      ''' Loads navigation arrows or generates generic fallbacks. '''
      dir = Directory.GetParent(__file__).FullName + "\\"
      if full:
         f = dir + 'fullleftarrow.png' if left else dir + 'fullrightarrow.png'
      else:
         f = dir + 'leftarrow.png' if left else dir + 'rightarrow.png'
      if File.Exists(f):
         return Image.FromFile(f)
      return Bitmap(16, 16)
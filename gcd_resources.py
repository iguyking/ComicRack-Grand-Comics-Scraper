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
      
      # Isolated user data directory path for the standalone local GCD scraper
      profile_dir = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData) + \
         r"\Local Grand Comics Database Scraper"
      
      cls.SETTINGS_FILE = Path.Combine(profile_dir, 'settings.dat')
      cls.ADVANCED_FILE = Path.Combine(profile_dir, 'advanced.dat')
      cls.GEOMETRY_FILE = Path.Combine(profile_dir, 'geometry.dat')
      cls.SERIES_FILE = Path.Combine(profile_dir, 'series.dat')
      cls.LOCAL_CACHE_DIRECTORY = Path.Combine(profile_dir, 'localCache')
      cls.I18N_DEFAULTS_FILE = Path.Combine(script_dir, 'en.zip')
      
      if not Directory.Exists(profile_dir):
         Directory.CreateDirectory(profile_dir)

      # Import any legacy settings from the old directory if they exist
      cls.__import_legacy_settings(script_dir, profile_dir)

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
   def createComicVineLogo(cls):
      ''' Legacy alias wrapper pointing directly to our isolated logo generator. '''
      return cls.createGCDLogo()

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

   #==============================================================================
   @classmethod
   def __import_legacy_settings(cls, legacy_dir, profile_dir):
      ''' Safely copies legacy config maps into the AppData tree profile folder. '''
      settings_file = Path.Combine(legacy_dir, 'settings.dat')
      advanced_file = Path.Combine(legacy_dir, 'advanced.dat')
      geometry_file = Path.Combine(legacy_dir, 'geometry.dat')
      series_file = Path.Combine(legacy_dir, 'series.dat')
      
      try:
         if File.Exists(settings_file) and not File.Exists(cls.SETTINGS_FILE):
            File.Copy(settings_file, cls.SETTINGS_FILE, False)
         if File.Exists(advanced_file) and not File.Exists(cls.ADVANCED_FILE):
            File.Copy(advanced_file, cls.ADVANCED_FILE, False)
         if File.Exists(geometry_file) and not File.Exists(cls.GEOMETRY_FILE):
            File.Copy(geometry_file, cls.GEOMETRY_FILE, False)
         if File.Exists(series_file) and not File.Exists(cls.SERIES_FILE):
            File.Copy(series_file, cls.SERIES_FILE, False)
      except:
         pass
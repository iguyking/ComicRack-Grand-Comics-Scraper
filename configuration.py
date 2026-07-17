#coding: utf-8
'''
This module contains the Configuration object.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs.
'''

import re
import clr
from gcd_resources import Resources
import gcd_utils as utils
from gcd_utils import persist_map, load_map, persist_string, load_string
from constants import ConfigKeys, ConfigDefaults

clr.AddReference('System')
from System.IO import File

#==============================================================================
class Configuration(object):
   '''
   This class contains the configuration details for the scraper, including
   methods for reading and writing those details to the filesystem.
   '''
   
   # Use centralized constants from constants module
   __API_KEY = ConfigKeys.API_KEY
   __DB_PATH = ConfigKeys.DB_PATH
   __UPDATE_SERIES = ConfigKeys.UPDATE_SERIES
   __UPDATE_NUMBER = ConfigKeys.UPDATE_NUMBER
   __UPDATE_RELEASED = ConfigKeys.UPDATE_RELEASED
   __UPDATE_PUBLISHED = ConfigKeys.UPDATE_PUBLISHED
   __UPDATE_TITLE = ConfigKeys.UPDATE_TITLE
   __UPDATE_CROSSOVERS = ConfigKeys.UPDATE_CROSSOVERS
   __UPDATE_WRITER = ConfigKeys.UPDATE_WRITER
   __UPDATE_PENCILLER = ConfigKeys.UPDATE_PENCILLER
   __UPDATE_INKER = ConfigKeys.UPDATE_INKER
   __UPDATE_COVER_ARTIST = ConfigKeys.UPDATE_COVER_ARTIST
   __UPDATE_COLORIST = ConfigKeys.UPDATE_COLORIST
   __UPDATE_LETTERER = ConfigKeys.UPDATE_LETTERER
   __UPDATE_EDITOR = ConfigKeys.UPDATE_EDITOR
   __UPDATE_SUMMARY = ConfigKeys.UPDATE_SUMMARY
   __UPDATE_IMPRINT = ConfigKeys.UPDATE_IMPRINT
   __UPDATE_PUBLISHER = ConfigKeys.UPDATE_PUBLISHER
   __UPDATE_VOLUME = ConfigKeys.UPDATE_VOLUME
   __UPDATE_CHARACTERS = ConfigKeys.UPDATE_CHARACTERS
   __UPDATE_TEAMS = ConfigKeys.UPDATE_TEAMS
   __UPDATE_LOCATIONS = ConfigKeys.UPDATE_LOCATIONS
   __UPDATE_WEBPAGE = ConfigKeys.UPDATE_WEBPAGE
   __OVERWRITE_EXISTING = ConfigKeys.OVERWRITE_EXISTING
   __IGNORE_BLANKS = ConfigKeys.IGNORE_BLANKS
   __CONVERT_IMPRINTS = ConfigKeys.CONVERT_IMPRINTS
   __AUTOCHOOSE_SERIES = ConfigKeys.AUTOCHOOSE_SERIES
   __CONFIRM_ISSUE = ConfigKeys.CONFIRM_ISSUE
   __DOWNLOAD_THUMBS = ConfigKeys.DOWNLOAD_THUMBS
   __PRESERVE_THUMBS = ConfigKeys.PRESERVE_THUMBS
   __FAST_RESCRAPE = ConfigKeys.FAST_RESCRAPE
   __RESCRAPE_NOTES = ConfigKeys.RESCRAPE_NOTES
   __RESCRAPE_TAGS = ConfigKeys.RESCRAPE_TAGS
   __SUMMARY_DIALOG = ConfigKeys.SUMMARY_DIALOG
   
   # Hash matching settings
   __ENABLE_MD5_MATCH = ConfigKeys.ENABLE_MD5_MATCH
   __ENABLE_PHASH_MATCH = ConfigKeys.ENABLE_PHASH_MATCH
   __ENABLE_SERIES_SEARCH = ConfigKeys.ENABLE_SERIES_SEARCH
   __PHASH_THRESHOLD = ConfigKeys.PHASH_THRESHOLD
   
   # Default values from centralized constants
   __DEFAULT_IGNORED_BEFORE_YEAR = ConfigDefaults.IGNORED_BEFORE_YEAR
   __DEFAULT_IGNORED_AFTER_YEAR = ConfigDefaults.IGNORED_AFTER_YEAR
   __DEFAULT_NEVER_IGNORE_THRESHOLD = ConfigDefaults.NEVER_IGNORE_THRESHOLD
   __DEFAULT_UPDATE_RATING = ConfigDefaults.UPDATE_RATING
   __DEFAULT_SHOW_COVERS = ConfigDefaults.SHOW_COVERS
   __DEFAULT_WELCOME_DIALOG = ConfigDefaults.WELCOME_DIALOG
   __DEFAULT_ALT_SEARCH_REGEX = ConfigDefaults.ALT_SEARCH_REGEX
   __DEFAULT_IGNORE_FOLDERS = ConfigDefaults.IGNORE_FOLDERS
   __DEFAULT_FORCE_SERIES_ART = ConfigDefaults.FORCE_SERIES_ART
   __DEFAULT_NOTE_SCRAPE_DATE = ConfigDefaults.NOTE_SCRAPE_DATE
   __DEFAULT_SCRAPE_DELAY = ConfigDefaults.SCRAPE_DELAY
   __DEFAULT_MAX_SEARCH_RESULTS = ConfigDefaults.MAX_SEARCH_RESULTS
   
   # Hash matching defaults
   __DEFAULT_ENABLE_MD5_MATCH = ConfigDefaults.ENABLE_MD5_MATCH
   __DEFAULT_ENABLE_PHASH_MATCH = ConfigDefaults.ENABLE_PHASH_MATCH
   __DEFAULT_ENABLE_SERIES_SEARCH = ConfigDefaults.ENABLE_SERIES_SEARCH
   __DEFAULT_PHASH_THRESHOLD = ConfigDefaults.PHASH_THRESHOLD

   #===========================================================================
   @staticmethod
   def validate_db_path(path):
      if not path or not path.strip():
         return False
      try:
         return File.Exists(path.strip())
      except:
         return False

   #=========================================================================== 
   def __init__(self):
      ''' Initializes a new Configuration object with default settings '''
      self.api_key_s = "" 
      self.db_path_s = "" 
      self.ow_existing_b = True 
      self.ignore_blanks_b = False  
      self.convert_imprints_b = True 
      self.autochoose_series_b = False 
      self.confirm_issue_b = False 
      self.download_thumbs_b = True 
      self.preserve_thumbs_b = True 
      self.scrape_in_groups_b = True 
      self.fast_rescrape_b = True 
      self.rescrape_notes_b = True 
      self.rescrape_tags_b = False 
      self.summary_dialog_b = True 
      
      # Hash matching settings
      self.enable_md5_match_b = True 
      self.enable_phash_match_b = True 
      self.enable_series_search_b = True 
      self.phash_threshold_n = 3 

      self.update_series_b = True 
      self.update_number_b = True 
      self.update_published_b = True 
      self.update_released_b = True 
      self.update_title_b = True 
      self.update_crossovers_b = True 
      self.update_writer_b = True 
      self.update_penciller_b = True 
      self.update_inker_b = True 
      self.update_cover_artist_b = True 
      self.update_colorist_b = True 
      self.update_letterer_b = True 
      self.update_editor_b = True 
      self.update_summary_b = True 
      self.update_publisher_b = True 
      self.update_imprint_b = True 
      self.update_volume_b = True 
      self.update_characters_b = True 
      self.update_teams_b = True 
      self.update_locations_b = True 
      self.update_webpage_b = True 
            
      self.session_data_map = {}
      self.__advanced_settings_s = None
      
      self.__ignored_publishers_sl = None 
      self.__allowed_publishers_sl = None 
      self.__ignored_searchterms_sl = None 
      self.__publisher_aliases_sm = None 
      self.__user_imprints_sm = None 
      self.__ignored_before_year_n = None 
      self.__ignored_after_year_n = None 
      self.__never_ignore_threshold_n = None 
      self.__update_rating_b = None 
      self.__show_covers_b = None 
      self.__welcome_dialog_b = None 
      self.__alt_search_regex_s = None 
      self.__ignore_folders_b = None 
      self.__force_series_art_b = None 
      self.__note_scrape_date_b = None 
      self.__scrape_delay_n = None 
      self.__max_search_results_n = None 
      self.__set_advanced_settings_s("")
   
   #===========================================================================   
   def __set_advanced_settings_s(self, advanced_settings_s = None):
      self.__advanced_settings_s = "" if advanced_settings_s is None \
         else advanced_settings_s.strip()
      
      c = Configuration
      self.__ignored_publishers_sl = set()
      self.__allowed_publishers_sl = set()
      self.__ignored_searchterms_sl = set()
      self.__publisher_aliases_sm = dict()
      self.__user_imprints_sm = dict()
      self.__ignored_before_year_n = c.__DEFAULT_IGNORED_BEFORE_YEAR
      self.__ignored_after_year_n = c.__DEFAULT_IGNORED_AFTER_YEAR
      self.__never_ignore_threshold_n = c.__DEFAULT_NEVER_IGNORE_THRESHOLD
      self.__update_rating_b = c.__DEFAULT_UPDATE_RATING
      self.__show_covers_b = c.__DEFAULT_SHOW_COVERS
      self.__welcome_dialog_b = c.__DEFAULT_WELCOME_DIALOG
      self.__alt_search_regex_s = c.__DEFAULT_ALT_SEARCH_REGEX
      self.__ignore_folders_b = c.__DEFAULT_IGNORE_FOLDERS
      self.__force_series_art_b = c.__DEFAULT_FORCE_SERIES_ART
      self.__note_scrape_date_b = c.__DEFAULT_NOTE_SCRAPE_DATE
      self.__scrape_delay_n = c.__DEFAULT_SCRAPE_DELAY
      self.__max_search_results_n = c.__DEFAULT_MAX_SEARCH_RESULTS

      lines_s = [ x.strip() for x in self.__advanced_settings_s.split("\n") if x.strip() ]
      pattern_s = r"^(?i){0}\s*=\s*['\"]?(.+?)['\"]?$"
      for line_s in lines_s:
         match = re.match(pattern_s.format("IGNORE_PUBLISHER"), line_s) 
         if match: self.__ignored_publishers_sl.add(match.group(1).lower().strip())
         
         match = re.match(pattern_s.format("ALLOW_PUBLISHER"), line_s)
         if match: self.__allowed_publishers_sl.add(match.group(1).lower().strip())
            
         match = re.match(pattern_s.format("IGNORE_SEARCHTERM"), line_s) 
         if match:
            term = match.group(1).lower().strip()
            if term and term.isalnum():
               self.__ignored_searchterms_sl.add(term)
            
         match = re.match(pattern_s.format("IGNORE_BEFORE_YEAR"), line_s)
         if match and utils.is_number(match.group(1)):
            self.__ignored_before_year_n = int(float(match.group(1)))
            
         match = re.match(pattern_s.format("IGNORE_AFTER_YEAR"), line_s)
         if match and utils.is_number(match.group(1)):
            self.__ignored_after_year_n = int(float(match.group(1)))
            
         match = re.match(pattern_s.format("NEVER_IGNORE_THRESHOLD"), line_s)
         if match and utils.is_number(match.group(1)):
            self.__never_ignore_threshold_n = int(float(match.group(1)))
            
         match = re.match(pattern_s.format("SCRAPE_RATING"), line_s)
         if match: self.__update_rating_b = match.group(1).strip().lower()=="true"
            
         match = re.match(pattern_s.format("SHOW_COVERS"), line_s)
         if match: self.__show_covers_b = match.group(1).strip().lower()=="true"
            
         match = re.match(pattern_s.format("WELCOME_DIALOG"), line_s)
         if match: self.__welcome_dialog_b = match.group(1).strip().lower()=="true"
            
         match = re.match(pattern_s.format("ALT_SEARCH_REGEX"), line_s)
         if match:
            try:
               re.compile(match.group(1))
               self.__alt_search_regex_s = match.group(1)
            except: pass
         
         match = re.match(pattern_s.format("IGNORE_FOLDERS"), line_s)
         if match: self.__ignore_folders_b = match.group(1).strip().lower()=="true"
            
         match = re.match(pattern_s.format("FORCE_SERIES_ART"), line_s)
         if match: self.__force_series_art_b = match.group(1).strip().lower()=="true"
            
         match = re.match(pattern_s.format("NOTE_SCRAPE_DATE"), line_s)
         if match: self.__note_scrape_date_b = match.group(1).strip().lower()=="true"
            
         match = re.match(pattern_s.format("PUBLISHER_ALIAS"), line_s)
         if match:
            match = re.match(r"^\s*(\S.*?)\s*[-=]+>\s*(\S.*?)$", match.group(1))
            if match:
               pub, alias = match.group(1).strip(" '\"").lower(), match.group(2).strip(" '\"")
               if pub and alias and len(alias) <= 50: 
                  self.__publisher_aliases_sm[pub] = alias
                  
         match = re.match(pattern_s.format("IMPRINT"), line_s)
         if match:
            match = re.match(r"^\s*(\S.*?)\s*[-=]+>\s*(\S.*?)$", match.group(1))
            if match:
               imprint_s = match.group(1).lower().strip(" '\"")
               publisher_s = match.group(2).strip(" '\"")
               if publisher_s and imprint_s and len(publisher_s) <= 50 and len(imprint_s) <= 50:  
                  self.__user_imprints_sm[imprint_s] = publisher_s
         
         match = re.match(pattern_s.format("SCRAPE_DELAY"), line_s)
         if match and utils.is_number(match.group(1)):
            self.__scrape_delay_n = min(3600, max(2, int(float(match.group(1)))))

         match = re.match(pattern_s.format("MAX_SEARCH_RESULTS"), line_s)
         if match and utils.is_number(match.group(1)):
            self.__max_search_results_n = min(5000, max( 10, int(float(match.group(1))) ) )

   advanced_settings_s = property( lambda self : self.__advanced_settings_s, __set_advanced_settings_s, __set_advanced_settings_s)
   ignored_publishers_sl = property( lambda self : list(self.__ignored_publishers_sl), None, None)
   allowed_publishers_sl = property( lambda self : list(self.__allowed_publishers_sl), None, None)
   ignored_searchterms_sl = property( lambda self : list(self.__ignored_searchterms_sl), None, None)
   publisher_aliases_sm = property( lambda self : dict(self.__publisher_aliases_sm), None, None)
   user_imprints_sm = property( lambda self : dict(self.__user_imprints_sm), None, None)
   ignored_before_year_n = property( lambda self : self.__ignored_before_year_n, None, None)
   ignored_after_year_n = property( lambda self : self.__ignored_after_year_n, None, None)
   never_ignore_threshold_n = property( lambda self : self.__never_ignore_threshold_n, None, None)
   update_rating_b = property( lambda self : self.__update_rating_b, None, None)
   show_covers_b = property( lambda self : self.__show_covers_b, None, None)
   welcome_dialog_b = property( lambda self : self.__welcome_dialog_b, None, None)
   alt_search_regex_s = property( lambda self : self.__alt_search_regex_s, None, None)
   ignore_folders_b = property( lambda self : self.__ignore_folders_b, None, None)
   force_series_art_b = property( lambda self : self.__force_series_art_b, None, None)
   note_scrape_date_b = property( lambda self : self.__note_scrape_date_b, None, None)
   scrape_delay_n = property( lambda self : self.__scrape_delay_n, None, None)
   max_search_results_n = property( lambda self : self.__max_search_results_n, None, None)
   
   #===========================================================================
   def load_defaults(self):
      loaded = {}
      if File.Exists(Resources.SETTINGS_FILE):
         loaded = load_map(Resources.SETTINGS_FILE)
         
      if Configuration.__API_KEY in loaded:
         self.api_key_s = loaded[Configuration.__API_KEY]
      
      if Configuration.__DB_PATH in loaded:
         path = loaded[Configuration.__DB_PATH].replace('|COLON|', ':')
         if Configuration.validate_db_path(path):
            self.db_path_s = path
            
      if Configuration.__UPDATE_SERIES in loaded: self.update_series_b = loaded[Configuration.__UPDATE_SERIES]
      if Configuration.__UPDATE_NUMBER in loaded: self.update_number_b = loaded[Configuration.__UPDATE_NUMBER]
      if Configuration.__UPDATE_PUBLISHED in loaded: self.update_published_b = loaded[Configuration.__UPDATE_PUBLISHED]
      if Configuration.__UPDATE_RELEASED in loaded: self.update_released_b = loaded[Configuration.__UPDATE_RELEASED]
      if Configuration.__UPDATE_TITLE in loaded: self.update_title_b = loaded[Configuration.__UPDATE_TITLE]
      if Configuration.__UPDATE_CROSSOVERS in loaded: self.update_crossovers_b = loaded[Configuration.__UPDATE_CROSSOVERS]
      if Configuration.__UPDATE_WRITER in loaded: self.update_writer_b = loaded[Configuration.__UPDATE_WRITER]
      if Configuration.__UPDATE_PENCILLER in loaded: self.update_penciller_b = loaded[Configuration.__UPDATE_PENCILLER]
      if Configuration.__UPDATE_INKER in loaded: self.update_inker_b = loaded[Configuration.__UPDATE_INKER]
      if Configuration.__UPDATE_COVER_ARTIST in loaded: self.update_cover_artist_b = loaded[Configuration.__UPDATE_COVER_ARTIST]
      if Configuration.__UPDATE_COLORIST in loaded: self.update_colorist_b = loaded[Configuration.__UPDATE_COLORIST]
      if Configuration.__UPDATE_LETTERER in loaded: self.update_letterer_b = loaded[Configuration.__UPDATE_LETTERER]
      if Configuration.__UPDATE_EDITOR in loaded: self.update_editor_b = loaded[Configuration.__UPDATE_EDITOR]
      if Configuration.__UPDATE_SUMMARY in loaded: self.update_summary_b = loaded[Configuration.__UPDATE_SUMMARY]
      if Configuration.__UPDATE_IMPRINT in loaded: self.update_imprint_b = loaded[Configuration.__UPDATE_IMPRINT]
      if Configuration.__UPDATE_PUBLISHER in loaded: self.update_publisher_b = loaded[Configuration.__UPDATE_PUBLISHER]
      if Configuration.__UPDATE_VOLUME in loaded: self.update_volume_b = loaded[Configuration.__UPDATE_VOLUME]
      if Configuration.__UPDATE_CHARACTERS in loaded: self.update_characters_b = loaded[Configuration.__UPDATE_CHARACTERS]
      if Configuration.__UPDATE_TEAMS in loaded: self.update_teams_b = loaded[Configuration.__UPDATE_TEAMS]
      if Configuration.__UPDATE_LOCATIONS in loaded: self.update_locations_b = loaded[Configuration.__UPDATE_LOCATIONS]
      if Configuration.__UPDATE_WEBPAGE in loaded: self.update_webpage_b = loaded[Configuration.__UPDATE_WEBPAGE]
      if Configuration.__OVERWRITE_EXISTING in loaded: self.ow_existing_b = loaded[Configuration.__OVERWRITE_EXISTING]
      if Configuration.__IGNORE_BLANKS in loaded: self.ignore_blanks_b = loaded[Configuration.__IGNORE_BLANKS]
      if Configuration.__CONVERT_IMPRINTS in loaded: self.convert_imprints_b = loaded[Configuration.__CONVERT_IMPRINTS]
      if Configuration.__AUTOCHOOSE_SERIES in loaded: self.autochoose_series_b = loaded[Configuration.__AUTOCHOOSE_SERIES]
      if Configuration.__CONFIRM_ISSUE in loaded: self.confirm_issue_b = loaded[Configuration.__CONFIRM_ISSUE]
      if Configuration.__DOWNLOAD_THUMBS in loaded: self.download_thumbs_b = loaded[Configuration.__DOWNLOAD_THUMBS]
      if Configuration.__PRESERVE_THUMBS in loaded: self.preserve_thumbs_b = loaded[Configuration.__PRESERVE_THUMBS]
      if Configuration.__FAST_RESCRAPE in loaded: self.fast_rescrape_b = loaded[Configuration.__FAST_RESCRAPE]
      if Configuration.__RESCRAPE_NOTES in loaded: self.rescrape_notes_b = loaded[Configuration.__RESCRAPE_NOTES]
      if Configuration.__RESCRAPE_TAGS in loaded: self.rescrape_tags_b = loaded[Configuration.__RESCRAPE_TAGS]
      if Configuration.__SUMMARY_DIALOG in loaded: self.summary_dialog_b = loaded[Configuration.__SUMMARY_DIALOG]
      if Configuration.__ENABLE_MD5_MATCH in loaded: self.enable_md5_match_b = loaded[Configuration.__ENABLE_MD5_MATCH]
      if Configuration.__ENABLE_PHASH_MATCH in loaded: self.enable_phash_match_b = loaded[Configuration.__ENABLE_PHASH_MATCH]
      if Configuration.__ENABLE_SERIES_SEARCH in loaded: self.enable_series_search_b = loaded[Configuration.__ENABLE_SERIES_SEARCH]
      if Configuration.__PHASH_THRESHOLD in loaded: self.phash_threshold_n = loaded[Configuration.__PHASH_THRESHOLD]
      
      if File.Exists(Resources.ADVANCED_FILE): 
         self.advanced_settings_s = load_string(Resources.ADVANCED_FILE)
         
   #===========================================================================
   def save_defaults(self):
      defaults = {}
      defaults[Configuration.__API_KEY] = self.api_key_s
      defaults[Configuration.__DB_PATH] = self.db_path_s.replace(':', '|COLON|')
      defaults[Configuration.__UPDATE_SERIES] = self.update_series_b
      defaults[Configuration.__UPDATE_NUMBER] = self.update_number_b
      defaults[Configuration.__UPDATE_RELEASED] = self.update_released_b
      defaults[Configuration.__UPDATE_PUBLISHED] = self.update_published_b
      defaults[Configuration.__UPDATE_TITLE] = self.update_title_b
      defaults[Configuration.__UPDATE_CROSSOVERS] = self.update_crossovers_b
      defaults[Configuration.__UPDATE_WRITER] = self.update_writer_b
      defaults[Configuration.__UPDATE_PENCILLER] = self.update_penciller_b
      defaults[Configuration.__UPDATE_INKER] = self.update_inker_b
      defaults[Configuration.__UPDATE_COVER_ARTIST] = self.update_cover_artist_b
      defaults[Configuration.__UPDATE_COLORIST] = self.update_colorist_b
      defaults[Configuration.__UPDATE_LETTERER] = self.update_letterer_b
      defaults[Configuration.__UPDATE_EDITOR] = self.update_editor_b
      defaults[Configuration.__UPDATE_SUMMARY] = self.update_summary_b
      defaults[Configuration.__UPDATE_IMPRINT] = self.update_imprint_b
      defaults[Configuration.__UPDATE_PUBLISHER] = self.update_publisher_b
      defaults[Configuration.__UPDATE_VOLUME] = self.update_volume_b
      defaults[Configuration.__UPDATE_CHARACTERS] = self.update_characters_b
      defaults[Configuration.__UPDATE_TEAMS] = self.update_teams_b
      defaults[Configuration.__UPDATE_LOCATIONS] = self.update_locations_b
      defaults[Configuration.__UPDATE_WEBPAGE] = self.update_webpage_b
      defaults[Configuration.__OVERWRITE_EXISTING] = self.ow_existing_b
      defaults[Configuration.__CONVERT_IMPRINTS] = self.convert_imprints_b
      defaults[Configuration.__AUTOCHOOSE_SERIES] = self.autochoose_series_b
      defaults[Configuration.__CONFIRM_ISSUE] = self.confirm_issue_b
      defaults[Configuration.__IGNORE_BLANKS] = self.ignore_blanks_b
      defaults[Configuration.__DOWNLOAD_THUMBS] = self.download_thumbs_b
      defaults[Configuration.__PRESERVE_THUMBS] = self.preserve_thumbs_b
      defaults[Configuration.__FAST_RESCRAPE] = self.fast_rescrape_b
      defaults[Configuration.__RESCRAPE_NOTES] = self.rescrape_notes_b
      defaults[Configuration.__RESCRAPE_TAGS] = self.rescrape_tags_b
      defaults[Configuration.__SUMMARY_DIALOG] = self.summary_dialog_b
      defaults[Configuration.__ENABLE_MD5_MATCH] = self.enable_md5_match_b
      defaults[Configuration.__ENABLE_PHASH_MATCH] = self.enable_phash_match_b
      defaults[Configuration.__ENABLE_SERIES_SEARCH] = self.enable_series_search_b
      defaults[Configuration.__PHASH_THRESHOLD] = self.phash_threshold_n
   
      persist_map(defaults, Resources.SETTINGS_FILE)
      persist_string(self.advanced_settings_s, Resources.ADVANCED_FILE)
   
   #===========================================================================
   def __ne__(self, other):
      return not self.__eq__(other)

   #===========================================================================
   def __eq__(self, other):
      return \
      self.ow_existing_b == other.ow_existing_b and \
      self.ignore_blanks_b == other.ignore_blanks_b and \
      self.convert_imprints_b == other.convert_imprints_b and \
      self.autochoose_series_b == other.autochoose_series_b and \
      self.confirm_issue_b == other.confirm_issue_b and \
      self.download_thumbs_b == other.download_thumbs_b and \
      self.preserve_thumbs_b == other.preserve_thumbs_b and \
      self.fast_rescrape_b == other.fast_rescrape_b and \
      self.rescrape_notes_b == other.rescrape_notes_b and \
      self.rescrape_tags_b == other.rescrape_tags_b and \
      self.summary_dialog_b == other.summary_dialog_b and \
      self.api_key_s == other.api_key_s and \
      self.db_path_s == other.db_path_s and \
      self.update_series_b == other.update_series_b and \
      self.update_number_b == other.update_number_b and \
      self.update_published_b == other.update_published_b and \
      self.update_released_b == other.update_released_b and \
      self.update_title_b == other.update_title_b and \
      self.update_crossovers_b == other.update_crossovers_b and \
      self.update_writer_b == other.update_writer_b and \
      self.update_penciller_b == other.update_penciller_b and \
      self.update_inker_b == other.update_inker_b and \
      self.update_cover_artist_b == other.update_cover_artist_b and \
      self.update_colorist_b == other.update_colorist_b and \
      self.update_letterer_b == other.update_letterer_b and \
      self.update_editor_b == other.update_editor_b and \
      self.update_summary_b == other.update_summary_b and \
      self.update_imprint_b == other.update_imprint_b and \
      self.update_publisher_b == other.update_publisher_b and \
      self.update_volume_b == other.update_volume_b and \
      self.update_characters_b == other.update_characters_b and \
      self.update_teams_b == other.update_teams_b and \
      self.update_locations_b == other.update_locations_b and \
      self.update_webpage_b == other.update_webpage_b and \
      self.advanced_settings_s == other.advanced_settings_s and \
      self.enable_md5_match_b == other.enable_md5_match_b and \
      self.enable_phash_match_b == other.enable_phash_match_b and \
      self.enable_series_search_b == other.enable_series_search_b and \
      self.phash_threshold_n == other.phash_threshold_n
   
   #===========================================================================
   def __str__(self):
      def x(x): return 'X' if x else ' '
      retval = \
      "--------------------------------------------------------------------\n"+\
      "[{0}] Series".format(x(self.update_series_b)).ljust(20) +\
      "[{0}] Volume".format(x(self.update_volume_b)).ljust(20) +\
      "[{0}] Number".format(x(self.update_number_b)).ljust(20) +\
      "\n" + \
      "[{0}] Title".format(x(self.update_title_b)).ljust(20) +\
      "[{0}] Published".format(x(self.update_published_b)).ljust(20) +\
      "[{0}] Released".format(x(self.update_released_b)).ljust(20) +\
      "\n" + \
      "[{0}] Crossovers".format(x(self.update_crossovers_b)).ljust(20) +\
      "[{0}] Publisher".format(x(self.update_publisher_b)).ljust(20) +\
      "[{0}] Imprint".format(x(self.update_imprint_b)).ljust(20) +\
      "\n" + \
      "[{0}] Writer".format(x(self.update_writer_b)).ljust(20) +\
      "[{0}] Penciller".format(x(self.update_penciller_b)).ljust(20) +\
      "[{0}] Inker".format(x(self.update_inker_b)).ljust(20) +\
      "\n" + \
      "[{0}] Colorist".format(x(self.update_colorist_b)).ljust(20) +\
      "[{0}] Letterer".format(x(self.update_letterer_b)).ljust(20) +\
      "[{0}] Cover Art".format(x(self.update_cover_artist_b)).ljust(20) +\
      "\n" + \
      "[{0}] Editor".format(x(self.update_editor_b)).ljust(20) +\
      "[{0}] Summary".format(x(self.update_summary_b)).ljust(20) +\
      "[{0}] Characters".format(x(self.update_characters_b)).ljust(20) +\
      "\n" + \
      "[{0}] Teams".format(x(self.update_teams_b)).ljust(20) +\
      "[{0}] Locations".format(x(self.update_locations_b)).ljust(20) +\
      "[{0}] Webpage".format(x(self.update_webpage_b)).ljust(20) +\
      "\n" +\
      "-------------------------------------------------------------------\n"+\
      "[{0}] Overwrite Existing".format(x(self.ow_existing_b)).ljust(30)+\
      "[{0}] Ignore Blanks".format(x(self.ignore_blanks_b)).ljust(30) +\
      "\n" + \
      "[{0}] Convert Imprints".format(x(self.convert_imprints_b)).ljust(30) +\
      "[{0}] Autochoose Series".format(x(self.autochoose_series_b)).ljust(30)+\
      "\n" + \
      "[{0}] Download Thumbs".format(x(self.download_thumbs_b)).ljust(30) +\
      "[{0}] Preserve Thumbs".format(x(self.preserve_thumbs_b)).ljust(30)+\
      "\n" + \
      "[{0}] Confirm Issues".format(x(self.confirm_issue_b)).ljust(30)+\
      "[{0}] Rescraping: Notes".format(x(self.rescrape_notes_b)).ljust(30)+\
      "\n" + \
      "[{0}] Fast Rescrape".format(x(self.fast_rescrape_b)).ljust(30)+\
      "[{0}] Rescraping: Tags".format(x(self.rescrape_tags_b)).ljust(30) +\
      "\n" + \
      "[{0}] Summary Dialog".format(x(self.summary_dialog_b)).ljust(30)+\
      "\n" + \
      "-------------------------------------------------------------------\n"+\
      "Hash Matching:\n" +\
      "[{0}] MD5 Match".format(x(self.enable_md5_match_b)).ljust(20) +\
      "[{0}] PHash Match".format(x(self.enable_phash_match_b)).ljust(20) +\
      "[{0}] Series Search".format(x(self.enable_series_search_b)).ljust(20) +\
      "\n" + \
      "PHash Threshold: {0}".format(self.phash_threshold_n).ljust(30) +\
      "\n" + \
      "-------------------------------------------------------------------"

      lines_sl = []
      c = Configuration
      
      if self.ignored_before_year_n != c.__DEFAULT_IGNORED_BEFORE_YEAR:
         lines_sl.append("Ignore all series that start before {0}.\n".format(self.ignored_before_year_n))
      if self.ignored_after_year_n != c.__DEFAULT_IGNORED_AFTER_YEAR:
         lines_sl.append("Ignore all series that start after {0}.\n".format(self.ignored_after_year_n))
      if self.never_ignore_threshold_n != c.__DEFAULT_NEVER_IGNORE_THRESHOLD:
         lines_sl.append("Don't ignore series that have {0} or more issues.\n".format(self.never_ignore_threshold_n))
      if self.update_rating_b != c.__DEFAULT_UPDATE_RATING: lines_sl.append("Scrape Community Rating into each issue (slow).\n")
      if self.show_covers_b != c.__DEFAULT_SHOW_COVERS: lines_sl.append("Hide series and issue covers while scraping.\n")
      if self.welcome_dialog_b != c.__DEFAULT_WELCOME_DIALOG: lines_sl.append("Do not show the initial 'Welcome Dialog'.\n")
      if self.alt_search_regex_s != c.__DEFAULT_ALT_SEARCH_REGEX: lines_sl.append("Alternate Filename Search Regex:\n   {0}\n".format(self.alt_search_regex_s))
      if self.ignore_folders_b != c.__DEFAULT_IGNORE_FOLDERS: lines_sl.append("Ignore folders when grouping issues into series.\n")
      if self.force_series_art_b != c.__DEFAULT_FORCE_SERIES_ART: lines_sl.append("Always display Series Art in the Series dialog.\n")
      if self.note_scrape_date_b != c.__DEFAULT_NOTE_SCRAPE_DATE: lines_sl.append("Include scrape date when scraping to Notes.\n")
      if self.scrape_delay_n != c.__DEFAULT_SCRAPE_DELAY: lines_sl.append("Using scrape delay of {0} seconds.\n".format(self.scrape_delay_n))
      if self.max_search_results_n != c.__DEFAULT_MAX_SEARCH_RESULTS: lines_sl.append("Series search will return first {0} results.\n".format(self.max_search_results_n))
       
      for publisher_s in self.ignored_publishers_sl: lines_sl.append("Ignore all series published by '{0}'\n".format(publisher_s))
      if self.allowed_publishers_sl: lines_sl.append("ONLY allowing series from {0} publisher(s): {1}\n".format(len(self.allowed_publishers_sl), ", ".join(sorted(self.allowed_publishers_sl))))
      for searchterm_s in self.ignored_searchterms_sl: lines_sl.append("Ignore search term '{0}'\n".format(searchterm_s))
      for imprint_s in self.user_imprints_sm.keys(): lines_sl.append("Treat '{0}' as an imprint of '{1}'\n".format(imprint_s, self.user_imprints_sm[imprint_s]))
      for publisher_s in self.publisher_aliases_sm.keys(): lines_sl.append("Replace publisher '{0}' with '{1}'\n".format(publisher_s, self.publisher_aliases_sm[publisher_s])) 

      advanced_lines_s = "".join(lines_sl) 
      if advanced_lines_s: retval += "\n" + advanced_lines_s + "\n-------------------------------------------------------------------"
      return retval
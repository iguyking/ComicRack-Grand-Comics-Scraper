#coding: utf-8
'''
This module contains the ComicBook class, which represents a comic book
from ComicRack that we are scraping data into.

@author: Cory Banack
'''

import re
from time import strftime
from dbmodels import IssueRef, SeriesRef
from pluginbookdata import PluginBookData
import gcd_utils as utils
from gcd_utils import sstr, is_number
from constants import Tags
import clr
import db
import fnameparser 
import gcd_log as log 
from bookdata import BookData

clr.AddReference('System')
from System.IO import Path
from System.Security.Cryptography import MD5
from System.Text import Encoding

#==============================================================================
class ComicBook(object):
   '''
   This class is a wrapper for the ComicRack ComicBook object, which adds 
   additional, scraper-oriented functionality to the object, and provides 
   read-only access to some of its data.
   '''
   
   # Magic tag string for permanently skipping books - use centralized constant
   CVDBSKIP = Tags.SKIP_BOOK

   #===========================================================================   
   def __init__(self, crbook, scraper):
      '''
      Initializes this ComicBook object based on an underlying ComicRack 
      ComicBook object (the crbook) parameter and the given ScrapeEngine.
      '''
      self.__scraper = scraper;
      self.__bookdata = PluginBookData(crbook, scraper)
      self.__parse_extra_details_from_path()


   #===========================================================================

   # Series name of this book.  Not None, may be empty.
   series_s = property( lambda self : self.__bookdata.series_s )
   
   # Issue number (string) of this book. Not None, may be empty.
   issue_num_s = property( lambda self : self.__bookdata.issue_num_s )
   
   # Volume (start year) of this book as an int >= -1, where -1 is unknown.
   volume_year_n = property( lambda self :  self.__bookdata.volume_year_n )
   
   # Publication year of this book, as an int >= -1, where -1 is unknown
   pub_year_n = property( lambda self : self.__bookdata.pub_year_n )
   
   # Release year of this book, as an int >= -1, where -1 is unknown
   rel_year_n = property( lambda self : self.__bookdata.rel_year_n )
   
   # The format of this book (giant, annual, etc.)  Not None, may be empty.
   format_s = property( lambda self : self.__bookdata.format_s )
   
   # The underlying path for this book (full path, including extension), 
   # or "" if it is a fileless book.  Will never be None.
   path_s = property(lambda self : self.__bookdata.path_s )
   
   # The number of pages in this book, an integer >= 0.
   page_count_n = property( lambda self : self.__bookdata.page_count_n )
   
   # the unique id string associated with this comic book's series.
   unique_series_s = property( lambda self : self.__unique_series_s() )  

   # an IssueRef object identifying this book in the database, if available.
   issue_ref = property( lambda self : None if \
      self.__extract_issue_ref() == 'skip' else self.__extract_issue_ref() )
   
   # a SeriesRef object identifying this book's series in the database, if available.
   series_ref = property( lambda self : self.__extract_series_ref() )
    
   # true if this book as has been marked to "skip forever"
   skip_b = property( lambda self : self.__extract_issue_ref() == 'skip' ) 

   #==========================================================================
   def create_image_of_page(self, page_index):
      return self.__bookdata.create_image_of_page(page_index)

   #===========================================================================
   def skip_forever(self):
      bd = self.__bookdata
      notes = self.__scraper.config.rescrape_notes_b
      tags = self.__scraper.config.rescrape_tags_b
      
      if notes == tags or tags:
         bd.tags_sl = self.__add_key_to_tags(bd.tags_sl, None);
         log.debug("Added " + str(ComicBook.CVDBSKIP) + " flag to comic book 'Tags'")
      
      if notes == tags or notes:
         bd.notes_s = self.__add_key_to_notes(bd.notes_s, None)
         log.debug("Added " + str(ComicBook.CVDBSKIP) + " flag to comic book 'Notes'")
         
      bd.update()
         

   # =============================================================================
   def __extract_issue_ref(self): 
      bd = self.__bookdata
      tagstring = ', '.join(bd.tags_sl)
      
      skip_found = re.search(r'(?i)'+ComicBook.CVDBSKIP, tagstring)
      if not skip_found:
         skip_found = re.search(r'(?i)'+ComicBook.CVDBSKIP, bd.notes_s)
      retval = "skip" if skip_found else None
   
      if retval is None:   
         issue_key = db.parse_key_tag(tagstring)
         if issue_key == None:
            issue_key = db.parse_key_tag(bd.notes_s)
         if issue_key == None:
            issue_key = int(bd.issue_key_s) if utils.is_number(bd.issue_key_s) else None
         if issue_key != None:
            retval = IssueRef(self.issue_num_s, issue_key, self.__bookdata.title_s, self.__bookdata.cover_url_s);
   
      return retval
   
   # =============================================================================
   def __extract_series_ref(self): 
      bd = self.__bookdata
      retval = None
      series_key = int(bd.series_key_s) if utils.is_number(bd.series_key_s) else None
      if series_key != None:
         retval = SeriesRef(series_key, None, -1, '', -1, None);
      return retval
   

   #==========================================================================
   def __unique_series_s(self):
      bd = self.__bookdata
      sname = '' if not bd.series_s else bd.series_s
      if sname and bd.format_s:
         sname += bd.format_s
      sname = re.sub('\W+', '', sname).lower()

      svolume = ''
      if sname:
         if bd.volume_year_n and bd.volume_year_n > 0:
            svolume = sstr(bd.volume_year_n)
      else:
         sname = "uniqueid-" + utils.sstr(id(self))
      
      location = Path.GetDirectoryName(bd.path_s) if bd.path_s else None
      location = location if location else ''
      hash = svolume if self.__scraper.config.ignore_folders_b else location + svolume
      if hash:  
         with MD5.Create() as md5:
            bytes = md5.ComputeHash(Encoding.UTF8.GetBytes(hash))
            hash = ''.join( [ "%02X" % x for x in bytes[:5] ] ).strip()
      return sname + hash 

   #===========================================================================
   def update(self, issue):
      ''' Copies all data in the given issue into this ComicBook object and its backing data source. '''
      log.debug("setting values for this comic book ('*' = changed):")
      config = self.__scraper.config
      bd = self.__bookdata
      
      # series ---------------------
      value = self.__massage_new_string("Series", issue.series_name_s, \
         bd.series_s, config.update_series_b, config.ow_existing_b, True)
      if value is None: bd.dont_update("series_s") 
      else: bd.series_s = value
      
      # issue number ---------------
      value = self.__massage_new_string("Issue Number", issue.issue_num_s, \
         bd.issue_num_s, config.update_number_b, config.ow_existing_b, True)
      if value is None: bd.dont_update("issue_num_s") 
      else: bd.issue_num_s = value
      
      # title ----------------------
      value = self.__massage_new_string("Title", issue.title_s, bd.title_s, \
         config.update_title_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("title_s") 
      else: bd.title_s = value
      
      # format ---------------------
      if hasattr(issue, 'format_s'):
         value = self.__massage_new_string("Format", issue.format_s, bd.format_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("format_s")
         else: bd.format_s = value

      # price ----------------------
      if hasattr(issue, 'price_s'):
         value = self.__massage_new_string("Price", issue.price_s, bd.price_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("price_s")
         else: bd.price_s = value

      # page count -----------------
      if hasattr(issue, 'page_count_n'):
         value = self.__massage_new_number("Page Count", issue.page_count_n, bd.page_count_n, \
            True, config.ow_existing_b, config.ignore_blanks_b, -1, lambda x: x >= 0)
         if value is None: bd.dont_update("page_count_n")
         else: bd.page_count_n = value

      # isbn -----------------------
      if hasattr(issue, 'isbn_s'):
         value = self.__massage_new_string("ISBN", issue.isbn_s, bd.isbn_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("isbn_s")
         else: bd.isbn_s = value

      # age rating -----------------
      if hasattr(issue, 'age_rating_s'):
         value = self.__massage_new_string("Age Rating", issue.age_rating_s, bd.age_rating_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("age_rating_s")
         else: bd.age_rating_s = value

      # variant --------------------
      if hasattr(issue, 'variant_s'):
         value = self.__massage_new_string("Variant", issue.variant_s, bd.variant_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("variant_s")
         else: bd.variant_s = value

      # genre ----------------------
      if hasattr(issue, 'genre_s'):
         value = self.__massage_new_string("Genre", issue.genre_s, bd.genre_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("genre_s")
         else: bd.genre_s = value

      # story arc ------------------
      if hasattr(issue, 'story_arcs_sl') and issue.story_arcs_sl:
         arc_str = ", ".join(issue.story_arcs_sl)
         value = self.__massage_new_string("Story Arc", arc_str, bd.story_arc_s, \
            True, config.ow_existing_b, config.ignore_blanks_b)
         if value is None: bd.dont_update("story_arc_s")
         else: bd.story_arc_s = value
      
      # crossovers -----------------
      value = self.__massage_new_string_list("Crossovers", issue.crossovers_sl, bd.crossovers_sl, \
         config.update_crossovers_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("crossovers_sl")
      else: bd.crossovers_sl = value
      
      # summary --------------------
      value = self.__massage_new_string("Summary", issue.summary_s, bd.summary_s, \
         config.update_summary_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("summary_s")
      else: bd.summary_s = value
      
      # release date ---------------
      value = self.__massage_new_date("Release Date", \
         (issue.rel_year_n, issue.rel_month_n, issue.rel_day_n), (bd.rel_year_n, bd.rel_month_n, bd.rel_day_n), \
         config.update_released_b, config.ow_existing_b, config.ignore_blanks_b, -1)
      if value is None: 
         bd.dont_update("rel_year_n")
         bd.dont_update("rel_month_n")
         bd.dont_update("rel_day_n")
      else:
         bd.rel_year_n, bd.rel_month_n, bd.rel_day_n = value
         
      # published date -------------
      value = self.__massage_new_date("Publish Date", \
         (issue.pub_year_n, issue.pub_month_n, issue.pub_day_n), (bd.pub_year_n, bd.pub_month_n, bd.pub_day_n), \
         config.update_published_b, config.ow_existing_b, config.ignore_blanks_b, -1)
      if value is None: 
         bd.dont_update("pub_year_n")
         bd.dont_update("pub_month_n")
         bd.dont_update("pub_day_n")
      else:
         bd.pub_year_n, bd.pub_month_n, bd.pub_day_n = value
      
      # volume ---------------------
      value = self.__massage_new_number("Volume", issue.volume_year_n, bd.volume_year_n, \
         config.update_volume_b, config.ow_existing_b, config.ignore_blanks_b, -1, lambda x : x > 0)
      if value is None: bd.dont_update("volume_year_n")
      else: bd.volume_year_n = value
       
      # publisher and imprint -----
      self.__update_publishers(issue, config)
      
      # characters -----------------
      value = self.__massage_new_string_list("Characters", issue.characters_sl, bd.characters_sl, \
         config.update_characters_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("characters_sl")
      else: bd.characters_sl = value
      
      # teams ----------------------
      value = self.__massage_new_string_list("Teams", issue.teams_sl, bd.teams_sl, \
         config.update_teams_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("teams_sl")
      else: bd.teams_sl = value
      
      # locations ------------------
      value = self.__massage_new_string_list("Locations", issue.locations_sl, bd.locations_sl, \
         config.update_locations_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("locations_sl")
      else: bd.locations_sl = value
      
      # creators -------------------
      value = self.__massage_new_string_list("Writers", issue.writers_sl, bd.writers_sl, \
         config.update_writer_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("writers_sl")
      else: bd.writers_sl = value
         
      value = self.__massage_new_string_list("Pencillers", issue.pencillers_sl, bd.pencillers_sl, \
         config.update_penciller_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("pencillers_sl")
      else: bd.pencillers_sl = value
      
      value = self.__massage_new_string_list("Inkers", issue.inkers_sl, bd.inkers_sl, \
         config.update_inker_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("inkers_sl")
      else: bd.inkers_sl = value
         
      value = self.__massage_new_string_list("Colorists", issue.colorists_sl, bd.colorists_sl, \
         config.update_colorist_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("colorists_sl")
      else: bd.colorists_sl = value
         
      value = self.__massage_new_string_list("Letterers", issue.letterers_sl, bd.letterers_sl, \
         config.update_letterer_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("letterers_sl")
      else: bd.letterers_sl = value
         
      value = self.__massage_new_string_list("CoverArtists", issue.cover_artists_sl, bd.cover_artists_sl, \
         config.update_cover_artist_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("cover_artists_sl")
      else: bd.cover_artists_sl = value
         
      value = self.__massage_new_string_list("Editors", issue.editors_sl, bd.editors_sl, \
         config.update_editor_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("editors_sl")
      else: bd.editors_sl = value
   
      # webpage --------------------
      value = self.__massage_new_string("Webpage", issue.webpage_s, bd.webpage_s, \
         config.update_webpage_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("webpage_s")
      else: bd.webpage_s = value
           
      # rating ---------------------
      value = self.__massage_new_number("Rating", issue.rating_n, bd.rating_n, \
         config.update_rating_b, config.ow_existing_b, config.ignore_blanks_b, 0.0, lambda x: x >= 0 and x <= 5)
      if value is None: bd.dont_update("rating_n")
      else: bd.rating_n = value
         
      # tags & notes ---------------
      new_tags = self.__add_key_to_tags(bd.tags_sl, issue.issue_key)
      value = self.__massage_new_string_list("Tags", new_tags, bd.tags_sl, config.rescrape_tags_b, True, False)
      if value is None: bd.dont_update("tags_sl")
      else: bd.tags_sl = value
      
      new_notes = self.__add_key_to_notes(bd.notes_s, issue.issue_key)
      value = self.__massage_new_string("Notes", new_notes, bd.notes_s, config.rescrape_notes_b, True, False)
      if value is None: bd.dont_update("notes_s")
      else: bd.notes_s = value
      
      # keys -----------------------
      value = self.__massage_new_string("Issue Key", issue.issue_key, bd.issue_key_s, True, True, False)
      if value is None: bd.dont_update("issue_key_s") 
      else: bd.issue_key_s = value
      
      value = self.__massage_new_string("Series Key", issue.series_key, bd.series_key_s, True, True, False)
      if value is None: bd.dont_update("series_key_s") 
      else: bd.series_key_s = value
      
      self.__update_cover_url(issue)
      bd.update()

   #===========================================================================
   def __update_publishers(self, issue, config):
      bd = self.__bookdata
      publisher_s = issue.publisher_s
      imprint_s = issue.imprint_s
      
      key = imprint_s if imprint_s else publisher_s
      if key and key.lower() in config.user_imprints_sm:
         publisher_s = config.user_imprints_sm[key.lower()]
         imprint_s = key
               
      if not config.convert_imprints_b and imprint_s:
         publisher_s = imprint_s
         imprint_s = ''
         
      aliases = config.publisher_aliases_sm;
      if publisher_s.lower() in aliases: publisher_s = aliases[publisher_s.lower()]
      if imprint_s.lower() in aliases: imprint_s = aliases[imprint_s.lower()]
         
      if publisher_s == imprint_s: imprint_s = ''
      
      value = self.__massage_new_string("Imprint", imprint_s, bd.imprint_s, \
         config.update_imprint_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("imprint_s")
      else: bd.imprint_s = value
            
      value = self.__massage_new_string("Publisher", publisher_s, bd.publisher_s, \
         config.update_publisher_b, config.ow_existing_b, config.ignore_blanks_b)
      if value is None: bd.dont_update("publisher_s")
      else: bd.publisher_s = value
   
   #===========================================================================
   def __update_cover_url(self, issue):
      config = self.__scraper.config
      bd = self.__bookdata
      
      url_s = None
      alt_cover_key = sstr(issue.issue_key)+"-altcover"
      if alt_cover_key in config.session_data_map:
         url_s = config.session_data_map[alt_cover_key]
      if not url_s and len(issue.image_urls_sl):  
         url_s = issue.image_urls_sl[0]
         
      label = "Cover Art URL"
      if not url_s:
         log.debug("-->  " + str(label.ljust(15)) + ": --- not available! ---")
         bd.dont_update("cover_url_s")
      else:
         log.debug("-->  " + str(label.ljust(15)) + ": " + str(url_s))
         bd.cover_url_s = url_s
            
      
   #===========================================================================
   def __add_key_to_tags(self, tags_sl, issue_key):
      tagstring_s = ', '.join(tags_sl).strip() if tags_sl else ''
      key_tag_s = db.create_key_tag_s(issue_key) if issue_key != None else ComicBook.CVDBSKIP 
      if key_tag_s and tagstring_s:
         matches = False
         prev_issue_key = db.parse_key_tag(tagstring_s)
         if prev_issue_key:
            prev_key_tag_s = db.create_key_tag_s(prev_issue_key)
            if prev_key_tag_s:
               regexp = re.compile(r"(?i)" + prev_key_tag_s)
               matches = regexp.search(tagstring_s)
         if matches:
            updated_tagstring_s = re.sub(regexp, key_tag_s, tagstring_s)
         else:
            if tagstring_s[-1] == ",": tagstring_s = tagstring_s[:-1]
            updated_tagstring_s = tagstring_s + ", " + key_tag_s
      elif key_tag_s:
         updated_tagstring_s = key_tag_s
      else:
         updated_tagstring_s = tagstring_s
      return updated_tagstring_s.split(", ")
   
   #===========================================================================
   def __add_key_to_notes(self, notestring_s, issue_key):
      notestring_s = notestring_s.strip() if notestring_s else ''
      key_tag_s = db.create_key_tag_s(issue_key) if issue_key != None else ComicBook.CVDBSKIP
      date_s = " on "+strftime(r'%Y.%m.%d %X') if self.__scraper.config.note_scrape_date_b else "" 
      key_note_s = 'Scraped metadata from {0} [{1}]{2}.'.format("LocalGCD", key_tag_s, date_s) if key_tag_s else ''
         
      if key_note_s and notestring_s:
         matches = False
         prev_issue_key = db.parse_key_tag(notestring_s)
         if prev_issue_key:
            prev_key_tag = db.create_key_tag_s(prev_issue_key)
            if prev_key_tag:
               regexp = re.compile( r"(?i)Scraped.*?" + prev_key_tag + "(]\.|.*?[\d\.]{8,} [\d:]{6,}\.)")                                   
               matches = regexp.search(notestring_s) 
         if matches:
            updated_notestring_s = re.sub(regexp, key_note_s, notestring_s)
         else:
            if prev_issue_key:
               prev_key_tag = db.create_key_tag_s(prev_issue_key)
               if prev_key_tag:
                  regexp = re.compile(r"(?i)" + prev_key_tag)
                  matches = regexp.search(notestring_s)
            if matches:
               updated_notestring_s = re.sub(regexp, key_tag_s, notestring_s)
            else:
               updated_notestring_s = notestring_s + "\n\n" + key_note_s 
      elif key_note_s:  
         updated_notestring_s = key_note_s
      else:
         updated_notestring_s = notestring_s
      return updated_notestring_s
   
   #===========================================================================
   @staticmethod 
   def __massage_new_string(label, new_value, old_value, update, overwrite, ignoreblanks):
      # Safe Unicode conversion pass to normalize strings before console output
      try:
         if new_value is not None:
            if isinstance(new_value, str):
               new_value = unicode(new_value, 'utf-8', 'ignore')
            else:
               new_value = unicode(sstr(new_value))
      except:
         new_value = sstr(new_value) if new_value is not None else ''

      try:
         if old_value is not None:
            if isinstance(old_value, str):
               old_value = unicode(old_value, 'utf-8', 'ignore')
            else:
               old_value = unicode(sstr(old_value))
      except:
         old_value = sstr(old_value) if old_value is not None else ''

      if new_value is None: new_value = u''
      if old_value is None: old_value = u''
      
      old_value = old_value.strip()
      new_value = new_value.strip()
      
      retval = None;      
      if update and (overwrite or not old_value) and not (ignoreblanks and not new_value):
         retval = new_value
         marker = '*' if old_value != new_value else ' '
         
         # Convert cleanly to ASCII for the console output stream to avoid crashing
         try:
            chars = retval.replace('\n', ' ').encode('ascii', 'ignore')
         except:
            chars = sstr(retval).replace('\n', ' ')
            
         if len(chars) > 70: chars = chars[:70] + " ..."
         log.debug("--> " + str(marker) + " " + str(label.ljust(15)) + ": " + str(chars))
      else:
         log.debug("-->  " + str(label.ljust(15)) + ": --- skipped ---")
      return retval
   
   #===========================================================================
   @staticmethod 
   def __massage_new_string_list(label, new_list, old_list, update, overwrite, ignoreblanks):
      new_list = [] if new_list is None else list(new_list)
      new_list = [x for x in new_list if x != None and len(x.strip())>0]
      old_list = [] if old_list is None else list(old_list)
      old_list = [x for x in old_list if x != None and len(x.strip())>0]
      
      retval = None;      
      if update and (overwrite or len(old_list)==0) and (not ignoreblanks or len(new_list) > 0):
         retval = new_list
         marker = '*' if old_list != new_list else ' '
         chars = ', '.join(retval).replace('\n', ' ')
         if len(chars) > 70: chars = chars[:70] + " ..."
         log.debug("--> " + str(marker) + " " + str(label.ljust(15)) + ": " + str(chars))
      else:
         log.debug("-->  " + str(label.ljust(15)) + ": --- skipped ---")
      return retval
   
   #===========================================================================
   @staticmethod 
   def __massage_new_number(label, new_value, old_value, update, overwrite, ignoreblanks, blank_value, is_valid=None, remap_invalid=None):
      if new_value is None: new_value = blank_value;
      if old_value is None: old_value = blank_value;
      if type(blank_value) != int and type(blank_value) != float: raise TypeError("wrong type for blank value");
      if type(old_value) != int and type(old_value) != float: raise TypeError("wrong type for old value");
      if type(old_value) != type(blank_value): raise TypeError("blank type is invalid type");
      if type(old_value) != type(new_value):
         try:
            if isinstance(old_value, int): new_value = int(new_value)
            else: new_value = float(new_value)
         except:
            log.debug("--> WARNING: can't convert '" + str(new_value) + "' into a " + str(type(old_value)))
            new_value = blank_value
            
      if is_valid:
         if not is_valid(new_value):
            if remap_invalid: new_value = remap_invalid(new_value)
         if not is_valid(new_value): new_value = blank_value
           
      retval = None;  
      if update and (overwrite or old_value == blank_value) and not (ignoreblanks and new_value == blank_value):
         retval = new_value
         marker = '*' if old_value != new_value else ' '
         if retval == blank_value: log.debug("--> " + str(marker) + " " + str(label.ljust(15)) + ": ")
         else: log.debug("--> " + str(marker) + " " + str(label.ljust(15)) + ": " + str(retval))
      else:
         log.debug("-->  " + str(label.ljust(15)) + ": --- skipped ---")
         
      if retval != None:
         retval = float(retval) if type(old_value) == float else int(retval)
      return retval
   
   #===========================================================================
   @staticmethod 
   def __massage_new_date(label, new_value, old_value, update, overwrite, ignoreblanks, blank_value):
      blank_date = (blank_value,blank_value,blank_value)
      new_value = blank_date if not new_value else new_value
      old_value = blank_date if not old_value else old_value
      if type(blank_value) != int: raise TypeError("wrong type for blank value");
      if len(old_value) != 3 or type(old_value[2]) != int: raise TypeError("wrong type for old value");
      if len(new_value) != 3 or type(new_value[2]) != int: raise TypeError("wrong type for new value");
            
      retval = None;
      if update and (overwrite or old_value == blank_date) and not (ignoreblanks and new_value == blank_date):
         retval = new_value
         marker = '*' if old_value != new_value else ' '
         if retval == blank_date: log.debug("--> " + str(marker) + " " + str(label.ljust(15)) + ": ")
         else: log.debug("--> " + str(marker) + " " + str(label.ljust(15)) + ": " + '-'.join(['??' if x == blank_value else sstr(x) for x in retval]))
      else:
         log.debug("-->  " + str(label.ljust(15)) + ": --- skipped ---")
      return retval
   
   # ==========================================================================
   def __parse_extra_details_from_path(self):
      bd  = self.__bookdata
      no_series = BookData.blank("series_s") == bd.series_s
      no_issuenum = BookData.blank("issue_num_s") == bd.issue_num_s
      no_year = BookData.blank("pub_year_n") == bd.pub_year_n
      if no_series or no_issuenum or no_year:
         if bd.path_s:
            filename = Path.GetFileName(bd.path_s)
            config = self.__scraper.config
            regex = config.alt_search_regex_s
            extracted = None
            if regex: extracted = fnameparser.regex(filename, regex) 
            if not extracted: extracted = fnameparser.extract(filename)
            if no_series: bd.series_s = extracted[0]
            if no_issuenum: bd.issue_num_s = extracted[1]
            if no_year: bd.pub_year_n = int(extracted[2]) if is_number(extracted[2]) else BookData.blank("pub_year_n")
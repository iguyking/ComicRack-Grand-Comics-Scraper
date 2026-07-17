#coding: utf-8
'''
This module contains the PluginBookData class, which is an implementation of BookData 
that reads and writes directly to the ComicRack database via ComicRack's plugin api.

@author: Cory Banack
'''
import re
from System import DateTime
from bookdata import BookData
import gcd_utils as utils
from gcd_utils import sstr
from constants import FieldNames
import clr
import db
import gcd_log as log

clr.AddReference('System')

#==============================================================================
class PluginBookData(BookData):
   ''' A BookData object customized for working with ComicRack directly. '''

   #===========================================================================
   def __init__(self, crbook, scraper):
      super(PluginBookData, self).__init__();
      if not "ComicBook" in utils.sstr(type(crbook)):
         raise Exception("invalid backing ComicBook")
         
      def split(s):
         return s.split(",") if s else []
         
      # Load primary details from ComicRack mapping trees
      self.series_s = crbook.Series
      self.issue_num_s = crbook.Number
      self.pub_year_n = crbook.Year
      self.pub_month_n = crbook.Month
      self.pub_day_n = crbook.Day
      self.rel_year_n = crbook.ReleasedTime.Year
      self.rel_month_n = crbook.ReleasedTime.Month
      self.rel_day_n = crbook.ReleasedTime.Day
      self.volume_year_n = crbook.Volume
      self.format_s = crbook.Format
      self.title_s = crbook.Title
      self.crossovers_sl = split(crbook.AlternateSeries)
      self.summary_s = crbook.Summary
      self.publisher_s = crbook.Publisher
      self.imprint_s = crbook.Imprint
      self.characters_sl = split(crbook.Characters)
      self.teams_sl = split(crbook.Teams)
      self.locations_sl = split(crbook.Locations)
      self.writers_sl = split(crbook.Writer)
      self.pencillers_sl = split(crbook.Penciller)
      self.inkers_sl = split(crbook.Inker)
      self.colorists_sl = split(crbook.Colorist)
      self.letterers_sl = split(crbook.Letterer)
      self.cover_artists_sl = split(crbook.CoverArtist)
      self.editors_sl = split(crbook.Editor)
      self.tags_sl = split(crbook.Tags)
      self.notes_s = crbook.Notes
      self.path_s = crbook.FilePath
      self.webpage_s = crbook.Web
      self.rating_n = crbook.CommunityRating
      self.page_count_n = crbook.PageCount
      
      # Expanded data tracking parameters initialization layer
      self.price_s = crbook.Price if hasattr(crbook, 'Price') else ""
      self.age_rating_s = crbook.AgeRating if hasattr(crbook, 'AgeRating') else ""
      self.variant_s = crbook.Variant if hasattr(crbook, 'Variant') else ""
      self.genre_s = crbook.Genre if hasattr(crbook, 'Genre') else ""
      self.story_arc_s = crbook.StoryArc if hasattr(crbook, 'StoryArc') else ""
      self.isbn_s = crbook.ISBN if hasattr(crbook, 'ISBN') else ""

      self.issue_key_s = crbook.GetCustomValue(FieldNames.ISSUE_KEY)
      self.series_key_s = crbook.GetCustomValue(FieldNames.SERIES_KEY)
      self.__crbook = crbook;
      self.__scraper = scraper;

   #==========================================================================
   def create_image_of_page(self, page_index):
      fileless = not self.path_s
      page_image = None
      if fileless:
         page_image = None
      else:
         try: page_image = self.__scraper.comicrack.App.GetComicPage(self.__crbook, page_index)
         except: page_image = None
      if page_image: page_image = utils.strip_back_cover(page_image)
      return page_image

   #===========================================================================
   def update(self):
      ''' Writes all eligible properties out to their counterparts in ComicRack. '''
      ok_to_update = self.updated_properties()
      
      def cleanup(s):
         s = re.sub(r",(\s+)", r"\1", s) if s else ""
         return re.sub(r",", r" ", s)

      if "series_s" in ok_to_update:
         self.__crbook.Series = self.series_s
         ok_to_update.remove("series_s")
         
      if "issue_num_s" in ok_to_update:
         self.__crbook.Number = self.issue_num_s
         ok_to_update.remove("issue_num_s")
         
      if "volume_year_n" in ok_to_update:
         try: self.__crbook.Volume = int(self.volume_year_n) if self.volume_year_n and int(self.volume_year_n) > 0 else 0
         except: self.__crbook.Volume = 0
         ok_to_update.remove("volume_year_n")
         
      if "format_s" in ok_to_update:
         self.__crbook.Format = self.format_s
         ok_to_update.remove("format_s")
         
      if "title_s" in ok_to_update:
         self.__crbook.Title = self.title_s
         ok_to_update.remove("title_s")
         
      if "crossovers_sl" in ok_to_update:
         self.__crbook.AlternateSeries = ', '.join([cleanup(x) for x in self.crossovers_sl])
         ok_to_update.remove("crossovers_sl")
         
      if "summary_s" in ok_to_update:
         self.__crbook.Summary = self.summary_s
         ok_to_update.remove("summary_s")
         
      if "publisher_s" in ok_to_update:
         self.__crbook.Publisher = self.publisher_s
         ok_to_update.remove("publisher_s")
         
      if "imprint_s" in ok_to_update:
         self.__crbook.Imprint = self.imprint_s
         ok_to_update.remove("imprint_s")
         
      if "characters_sl" in ok_to_update:
         self.__crbook.Characters = ', '.join([cleanup(x) for x in self.characters_sl])
         ok_to_update.remove("characters_sl")
         
      if "teams_sl" in ok_to_update:
         self.__crbook.Teams = ', '.join([cleanup(x) for x in self.teams_sl])
         ok_to_update.remove("teams_sl")
         
      if "locations_sl" in ok_to_update:
         self.__crbook.Locations = ', '.join([cleanup(x) for x in self.locations_sl])
         ok_to_update.remove("locations_sl")
         
      if "writers_sl" in ok_to_update:
         self.__crbook.Writer = ', '.join([cleanup(x) for x in self.writers_sl])
         ok_to_update.remove("writers_sl")
         
      if "pencillers_sl" in ok_to_update:
         self.__crbook.Penciller = ', '.join([cleanup(x) for x in self.pencillers_sl])
         ok_to_update.remove("pencillers_sl")
         
      if "inkers_sl" in ok_to_update:
         self.__crbook.Inker = ', '.join([cleanup(x) for x in self.inkers_sl])
         ok_to_update.remove("inkers_sl")
         
      if "colorists_sl" in ok_to_update:
         self.__crbook.Colorist = ', '.join([cleanup(x) for x in self.colorists_sl])
         ok_to_update.remove("colorists_sl")
         
      if "letterers_sl" in ok_to_update:
         self.__crbook.Letterer = ', '.join([cleanup(x) for x in self.letterers_sl])
         ok_to_update.remove("letterers_sl")
         
      if "cover_artists_sl" in ok_to_update:
         self.__crbook.CoverArtist = ', '.join([cleanup(x) for x in self.cover_artists_sl])
         ok_to_update.remove("cover_artists_sl")
         
      if "editors_sl" in ok_to_update:
         self.__crbook.Editor = ', '.join([cleanup(x) for x in self.editors_sl])
         ok_to_update.remove("editors_sl")
         
      if "webpage_s" in ok_to_update:
         self.__crbook.Web = self.webpage_s
         ok_to_update.remove("webpage_s")
         
      if "rating_n" in ok_to_update:
         self.__crbook.CommunityRating = self.rating_n
         ok_to_update.remove("rating_n")
         
      if "tags_sl" in ok_to_update:
         self.__crbook.Tags = ', '.join([cleanup(x) for x in self.tags_sl])
         ok_to_update.remove("tags_sl")
         
      if "notes_s" in ok_to_update:
         self.__crbook.Notes = self.notes_s
         ok_to_update.remove("notes_s")

      # Expanded tracking assignments pushed into native ComicRack structures
      if "price_s" in ok_to_update:
         self.__crbook.Price = self.price_s
         ok_to_update.remove("price_s")

      if "age_rating_s" in ok_to_update:
         self.__crbook.AgeRating = self.age_rating_s
         ok_to_update.remove("age_rating_s")

      if "variant_s" in ok_to_update:
         self.__crbook.Variant = self.variant_s
         ok_to_update.remove("variant_s")

      if "genre_s" in ok_to_update:
         self.__crbook.Genre = self.genre_s
         ok_to_update.remove("genre_s")

      if "story_arc_s" in ok_to_update:
         self.__crbook.StoryArc = self.story_arc_s
         ok_to_update.remove("story_arc_s")

      if "isbn_s" in ok_to_update:
         self.__crbook.ISBN = self.isbn_s
         ok_to_update.remove("isbn_s")

      if "page_count_n" in ok_to_update:
         try: self.__crbook.PageCount = int(self.page_count_n)
         except: pass
         ok_to_update.remove("page_count_n")
         
      if "issue_key_s" in ok_to_update:
         self.__crbook.SetCustomValue(FieldNames.ISSUE_KEY, self.issue_key_s)
         ok_to_update.remove("issue_key_s")
         
      if "series_key_s" in ok_to_update:
         self.__crbook.SetCustomValue(FieldNames.SERIES_KEY, self.series_key_s)
         ok_to_update.remove("series_key_s")
         
      if "pub_year_n" in ok_to_update or "pub_month_n" in ok_to_update or "pub_day_n" in ok_to_update:
         try:
            self.__crbook.Year = self.pub_year_n
            self.__crbook.Month = self.pub_month_n
            self.__crbook.Day = self.pub_day_n
         except: pass
            
      if "rel_year_n" in ok_to_update or "rel_month_n" in ok_to_update or "rel_day_n" in ok_to_update:
         try:
            year = self.rel_year_n if self.rel_year_n > 0 else 1
            month = self.rel_month_n if 1 <= self.rel_month_n <= 12 else 1
            day = self.rel_day_n if 1 <= self.rel_day_n <= 31 else 1
            self.__crbook.ReleasedTime = DateTime(year, month, day)
         except: pass
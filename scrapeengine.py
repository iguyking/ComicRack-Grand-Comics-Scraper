'''
This module is home to the ScrapeEngine class.
@author: Cory Banack
'''
import clr

import gcd_log as log
import gcd_utils as utils
from gcd_utils import sstr, natural_key
from gcd_resources import Resources 
from configuration import Configuration
from comicform import ComicForm
from seriesform import SeriesForm, SeriesFormResult
from issueform import IssueForm, IssueFormResult
from progressbarform import ProgressBarForm
from searchform import SearchForm
import db
from welcomeform import WelcomeForm
from finishform import FinishForm
import gcd_i18n as i18n
from matchscore import MatchScore
from comicbook import ComicBook
import automatcher
import dbutils
from gcd_configform import ConfigForm
import hashmatcher

# Import extracted classes from their new modules
from bookstatus import BookStatus
from scrapedseries import ScrapedSeries

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Application, MessageBox, \
    MessageBoxButtons, MessageBoxIcon

clr.AddReference('System')
from System.IO import Path
from System import GC, DateTime
from System.Threading import Thread, ThreadStart

clr.AddReference('System.Runtime')
from System.Runtime.InteropServices import RuntimeInformation;

# =============================================================================
class ScrapeEngine(object):
   '''
   This class contains the main processing loop for the Comic Vine Scraper
   script.   Once initialized, you pass a collection of books to the 
   ScrapeEngine via the 'scrape' method.
   
   Those books will be processed one at a time, with windows and dialogs
   popping up to interact with the user as needed (including a single 
   ComicForm window, which is present the during the entire scrape, always
   showing the user the current status of the ScrapeEngine.)
   '''

   # ==========================================================================
   def __init__(self, comicrack):
      '''
      Initializes this ScrapeEngine.  It takes the ComicRack Application 
      object as it's only parameter.
      '''
      
      # the Configuration details for this ScrapeEngine.  used everywhere.  
      self.config = Configuration()
      
      # the ComicRack application object, i.e. the instance of ComicRack that
      # is running this script.  used everywhere.
      self.comicrack = comicrack
      
      # a list of methods that will each be fired whenever the 'scrape' 
      # operation begins processing/scraping a new book. these methods should
      # look like:   
      #             start_scrape(book, num_remaining)
      #
      # where 'book' is the new book being scraped and 'num_remaining' is the 
      # number of books left to scrape, including the one currently starting
      self.start_scrape_listeners = []

      # a list of no-argument methods that will each be fired once 
      # when (and if) the scrape operation gets cancelled.
      self.cancel_listeners = []
      
      # this variable can be set by calling the 'cancel' method.  when it is 
      # set to True, it indicates that the entire script should be cancelled as 
      # soon as possible.
      self.__cancelled_b = False
      
      # a list of two values, the first value tells how many books this 
      # scrape engine has scraped, the second tells how many it has skipped.
      # it becomes valid as soon as the main processing loop starts running.
      self.__status = [0,0]
      
      # an object that we use to keep (and add to) a persistent list of which 
      # series' the user has chosen while scraping.  it can then be used to
      # help present better sorted choices to the user in the future.
      self.__matchscore = MatchScore()



   # ==========================================================================
   def cancel(self):
      '''
      This method cancels the ScrapeEngine's current scrape operation, 
      and causes the main processing loop to exit on the next iteration;
      all ComicBooks that haven't yet been scraped will be skipped.
      '''
      
      if not self.__cancelled_b:
         # do this on calling thread, even if its not the mainwindow UI
         # thread, cause that thread could be blocked by SCRAPE_DELAY
         self.__cancelled_b = True 
         def delegate(): 
            for cancel_listener in self.cancel_listeners:
               try:
                  cancel_listener()
               except:
                  pass  # Ignore errors closing forms
         utils.invoke(self.comicrack.MainWindow, delegate, False)



   # ==========================================================================
   def scrape(self, books):
      '''
      This is the entry-point to the ScraperEngine's main processing loop.
      '''
      
      try:
         # FIX: Converted all multi-argument log commas to additions (+)
         log.debug()
         log.debug("-"*80)
         log.debug("Local GCD Scraper Version:  " + sstr(Resources.SCRIPT_VERSION) +
                   "  (using " + sstr(RuntimeInformation.FrameworkDescription) + ")" )
         log.debug("Running As:          " + "ComicRack Plugin (CR version " +
            self.comicrack.App.ProductVersion + ")")
         log.debug("Cache Directory:     " + sstr(Resources.LOCAL_CACHE_DIRECTORY))
         log.debug("Settings File:       " + sstr(Resources.SETTINGS_FILE))
         auto_log = log.get_auto_log_path()
         if auto_log:
            log.debug("Session Log File:    " + sstr(auto_log))
         log.debug("-"*80)
         log.debug()

         if books:
            self.__scrape(books) 
            
         log.debug("Scraper terminated normally (scraped {0}, skipped {1})."\
            .format(self.__status[0], self.__status[1]))
            
      except Exception as ex:
         log.handle_error(ex)
         
      finally:
         if self.config.summary_dialog_b:
            try:
               with FinishForm(self, self.__status) as finish_form:
                  finish_form.show_form()
            except Exception as ex:
               log.handle_error(ex)
         
         try:
            hashmatcher.clear_hash_cache()
         except:
            pass



   # ==========================================================================
   def __scrape(self, books):
      '''
      The private implementation of the 'scrape' method.
      '''
      self.__status = [0, len(books)]
      
      self.config = Configuration()
      self.config.load_defaults()
      
      if not self.config.db_path_s:
         log.debug("Database path not available.  Showing config dialog.")
         with ConfigForm(self.comicrack.MainWindow) as config_form:
            config_form.show_form()
         self.config.load_defaults()
         if not self.config.db_path_s:
            log.debug("Database path still not available.  Aborting.")
            return
         
      if self.config.welcome_dialog_b:
         with WelcomeForm(self, books) as welcome_form:
            self.__cancelled_b = not welcome_form.show_form()
         self.config = Configuration()
         self.config.load_defaults()
         if self.__cancelled_b:
            log.debug("Cancelled!")
            return

      log.debug(self.config)
      log.debug()
      
      db.initialize(**{'db_path':self.config.db_path_s}) 
      
      if self.config.enable_phash_match_b:
         if not hashmatcher.is_hash_cache_initialized():
            log.debug("Initializing hash cache...")
            hash_count = hashmatcher.initialize_hash_cache()
            log.debug("Hash cache initialized with " + sstr(hash_count) + " entries")
      
      books = [ ComicBook(book, self) for book in books ]
      books = self.__sort_books(books) 

      comic_form = ComicForm.show_threadsafe(self)
      
      try:
         scrape_cache = {}
         i = 0
         orig_length = len(books)
         while i < len(books):
            if self.__cancelled_b: break
            book = books[i]
            
            delayed_b = i >= orig_length
            if i != 0 and not delayed_b:
               self.__wait_until_ready()
               if self.__cancelled_b: break
               
            # FIX: Clean log concatenation string here
            bname = 'FILELESS ("' + book.series_s + " #" + book.issue_num_s + '")' if book.path_s == "" else Path.GetFileName(book.path_s)
            log.debug("======> scraping next comic book: '" + sstr(bname) + "'")
            
            num_remaining = len(books) - i
            for start_scrape in self.start_scrape_listeners:
               start_scrape(book, num_remaining)

            manual_search_b = False
            fast_rescrape_b = self.config.fast_rescrape_b and not delayed_b
            autoscrape_b = self.config.autochoose_series_b and \
                not self.config.confirm_issue_b and not delayed_b
            bookstatus = BookStatus("DELAYED") if delayed_b else BookStatus("UNSCRAPED")
               
            while not self.__cancelled_b:
               try:
                  bookstatus = self.__scrape_book(book, scrape_cache,
                    manual_search_b, fast_rescrape_b, autoscrape_b, bookstatus)
               except Exception as ex:
                  log.debug_exc("Exception during __scrape_book")
                  bookstatus = BookStatus("SKIPPED")
                  break
               
               if bookstatus.equals("UNSCRAPED"):
                  manual_search_b = True
                  continue
               elif bookstatus.equals("SCRAPED"):
                  self.__status[0] += 1
                  self.__status[1] -= 1
                  break
               elif bookstatus.equals("SKIPPED"):
                  break
               elif bookstatus.equals("DELAYED"):
                  if not delayed_b: 
                     books.append(book)
                  break
            
            GC.Collect()
            GC.WaitForPendingFinalizers()
            log.debug()
            log.debug()
            i = i + 1
            
      finally:
         self.comicrack.MainWindow.Activate()
         if comic_form: 
            comic_form.close_threadsafe()
            import time
            time.sleep(0.2)


   # ==========================================================================
   def __scrape_book(self, book, scrape_cache, 
         manual_search_b, fast_rescrape_b, autoscrape_b, prev_status=None):
      '''
      The private heart of the Main Processing Loop.
      '''
      Application.DoEvents()
      if self.__cancelled_b: return BookStatus("SKIPPED")
      if prev_status == None: prev_status = BookStatus("UNSCRAPED")
         
      if book.skip_b: 
         log.debug("found SKIP tag, so skipping the scrape for this book.")
         return BookStatus("SKIPPED")

      issue_ref = book.issue_ref
      if issue_ref and fast_rescrape_b:
         log.debug("rescraping details in book identified its issue as: '" + sstr(issue_ref) + "'")
         try:
            issue = db.query_issue(issue_ref, self.config.update_rating_b)
            book.update(issue)
            return BookStatus("SCRAPED")
         except:
            log.debug_exc("Error rescraping details:")
            log.debug("we'll retry scraping this book again at the end.")
            return BookStatus("DELAYED")

      key = book.unique_series_s
      
      if key not in scrape_cache and not manual_search_b:
         if book.series_ref and fast_rescrape_b:
            log.debug("rescraping details in book identified its series as: '" + sstr(book.series_ref) + "'")
            scraped_series = ScrapedSeries( book.series_ref )
            scrape_cache[key] = scraped_series
   
      if key not in scrape_cache and not manual_search_b:
         magic_series_ref = db.check_magic_file(book.path_s)
         if magic_series_ref:        
            log.debug("a 'magic' file identified this book's series as: '" + sstr(magic_series_ref) + "'")
            scraped_series = ScrapedSeries( magic_series_ref )
            scrape_cache[key] = scraped_series
      
      is_delayed_book = prev_status and prev_status.equals("DELAYED")
      if not manual_search_b and is_delayed_book and hashmatcher.is_hash_matching_available(self.config):
         log.debug("trying hash-based matching...")
         hash_issue_ref, hash_series_ref, match_type = \
            hashmatcher.find_issue_by_hash(book, self.config)
         if hash_issue_ref and hash_series_ref:
            log.debug("hash matching found issue! type: " + sstr(match_type) +
               ", issue: " + sstr(hash_issue_ref) + ", series: " + sstr(hash_series_ref))
            try:
               issue = db.query_issue(hash_issue_ref, self.config.update_rating_b)
               book.update(issue)
               return BookStatus("SCRAPED")
            except:
               log.debug_exc("Error applying hash match:")
               log.debug("falling through to normal search flow.")
         else:
            log.debug("hash matching didn't find a unique match.")
         
      if key not in scrape_cache and autoscrape_b and self.config.enable_series_search_b:
         if self.config.confirm_issue_b:
            raise Exception("can't confirm issues while autoscraping")
         log.debug("trying to match this book automatically (Level 3: series text search)...")
         auto_series_ref = automatcher.find_series_ref(book, self.config) 
         if auto_series_ref:
            log.debug("...found a suitable match:  " + sstr(auto_series_ref))
            scraped_series = ScrapedSeries( auto_series_ref )
            scrape_cache[key] = scraped_series
         else:
            log.debug("...couldn't find a match. leave it until the end.")
            return BookStatus("DELAYED")
      elif key not in scrape_cache and autoscrape_b and not self.config.enable_series_search_b:
         log.debug("series text search disabled, skipping Level 3 matching.")
         return BookStatus("DELAYED")

      search_terms_s = None
      series_refs = None
      if key not in scrape_cache: 
         search_terms_s = book.series_s
         
         # --- AUTO-SELECTION BATCH RESCUE ---
         # If we are in auto-choose mode and have search terms, try a quick database query
         # to see if a high-confidence match can save us from a manual popup.
         if autoscrape_b and search_terms_s and manual_search_b:
            temp_refs = self.__query_series_refs(search_terms_s)
            if temp_refs:
               # Score the matches using the engine's matchscore matrix
               best_ref = None
               best_score = -1
               for ref in temp_refs:
                  score = self.__matchscore.compute_n(book, ref)
                  if score > best_score:
                     best_score = score
                     best_ref = ref
               
               # High Confidence Threshold: If the match score is excellent (e.g., >= 85),
               # auto-assign it right here and skip the manual search forms entirely!
               if best_ref and best_score >= 85:
                  log.debug("Automatcher Rescue: Found high-confidence match ({0}) for '{1}'".format(best_score, search_terms_s))
                  scraped_series = ScrapedSeries(best_ref)
                  scrape_cache[key] = scraped_series
                  series_refs = temp_refs

         # Fall back to manual popups only if we still don't have a cached series match
         if key not in scrape_cache and (manual_search_b or not search_terms_s):
            log.debug('asking user for series search terms...')
            with SearchForm(self, search_terms_s, 
                  prev_status.get_failed_search_terms_s() ) as search_form:
               search_form_result = search_form.show_form()
            log.debug( "...and the user chose to " + search_form_result.get_debug_string() )
            
            if search_form_result.equals("SEARCH"):
               search_terms_s = search_form_result.get_search_terms()
            elif search_form_result.equals("CANCEL"):
               self.__cancelled_b = True
               return BookStatus("SKIPPED")
            elif search_form_result.equals("SKIP"):
               return BookStatus("SKIPPED")
            elif search_form_result.equals("PERMSKIP"):
               book.skip_forever()
               return BookStatus("SKIPPED")
               
         if key not in scrape_cache:
            series_refs = self.__query_series_refs(search_terms_s)
         if self.__cancelled_b: 
            return BookStatus("SKIPPED")
         if not series_refs and key not in scrape_cache:
            return BookStatus("UNSCRAPED", search_terms_s)

      while True:
         force_issue_dialog_b = self.config.confirm_issue_b 
         if key not in scrape_cache: 
            if not series_refs or not search_terms_s:
               return BookStatus("UNSCRAPED")
            series_form_result =\
               self.__choose_series_ref(book, search_terms_s, series_refs)
            
            if series_form_result.equals("CANCEL") or self.__cancelled_b:
               self.__cancelled_b = True
               return BookStatus("SKIPPED")
            elif series_form_result.equals("SKIP"):
               return BookStatus("SKIPPED")
            elif series_form_result.equals("PERMSKIP"):
               book.skip_forever()
               return BookStatus("SKIPPED")
            elif series_form_result.equals("SEARCH"): 
               return BookStatus("UNSCRAPED")
            elif series_form_result.equals("SHOW") or \
                 series_form_result.equals("OK"):
               scraped_series = ScrapedSeries( series_form_result.get_ref() )
               force_issue_dialog_b = series_form_result.equals("SHOW")
               scrape_cache[key] = scraped_series
               
         scraped_series = scrape_cache[key]
         log.debug("searching for the right issue in '" + sstr(scraped_series.series_ref) + "'")

         issue_ref = None         
         if autoscrape_b:
            series_ref = scraped_series.series_ref
            if book.issue_num_s == "":
               if series_ref.issue_count_n <=1:
                  refs = self.__query_issue_refs(series_ref)
                  if len(refs) == 1: issue_ref = list(refs)[0]
            else:
               issue_ref = db.query_issue_ref( series_ref, book.issue_num_s )
               
            if issue_ref == None:
               log.debug("couldn't find issue number.  leaving until the end.")
               del scrape_cache[key]
               return BookStatus("DELAYED")
            else: 
               log.debug("   ...identified issue number " + sstr(book.issue_num_s))
               
         else:            
            issue_form_result = self.__choose_issue_ref( book, 
               scraped_series.series_ref, scraped_series.issue_refs, 
               force_issue_dialog_b)
            
            if issue_form_result.equals("CANCEL") or self.__cancelled_b:
               self.__cancelled_b = True
               return BookStatus("SKIPPED")
            elif issue_form_result.equals("SKIP") or \
                  issue_form_result.equals("PERMSKIP"):
               if force_issue_dialog_b and not self.config.confirm_issue_b:
                  del scrape_cache[key]
               if issue_form_result.equals("PERMSKIP"):
                  book.skip_forever()
               return BookStatus("SKIPPED")
            elif issue_form_result.equals("BACK"):
               del scrape_cache[key]
            else:
               issue_ref = issue_form_result.get_ref()
         
         if issue_ref != None:      
            issue = db.query_issue( issue_ref, self.config.update_rating_b )
            book.update(issue)
            self.__matchscore.record_choice(scraped_series.series_ref)
            return BookStatus("SCRAPED")

      raise Exception("should never get here")


   # ==========================================================================
   def __sort_books(self, books):
      '''Sorts books cleanly before processing loop execution.'''
      def __compare_books(book1, book2):
         result = book1.unique_series_s.CompareTo(book2.unique_series_s)
         if result == 0:
            num1 = '' if not book1.issue_num_s else book1.issue_num_s
            num2 = '' if not book2.issue_num_s else book2.issue_num_s
            def pad(num):
               try:
                  f = float(num.lower().strip('abcdefgh'))
                  if f < 10: return "000" + num
                  elif f < 100: return "00" + num
                  elif f < 1000: return "0" + num
                  else: return num
               except:
                  return num
            result = pad(num1).CompareTo(pad(num2))
         return result

      slow_scrape_books = []
      fast_scrape_books = []
      if self.config.fast_rescrape_b:
         for book in books:
            if book.skip_b or book.issue_ref:
               fast_scrape_books.append(book)
            else:
               slow_scrape_books.append(book)
      else:
         slow_scrape_books = list(books)
      
      slow_scrape_books.sort(cmp=__compare_books)     
      fast_scrape_books.sort(cmp=__compare_books)     
      
      return fast_scrape_books+slow_scrape_books


   # ==========================================================================   
   def __choose_series_ref(self, book, search_terms_s, series_refs):
      result = SeriesFormResult("SEARCH")
      if series_refs:
         log.debug('displaying the series selection dialog...')
         with SeriesForm(self, book, series_refs, search_terms_s) as sform:
            result = sform.show_form() 
         log.debug('   ...user chose to ' + sstr(result.get_debug_string()))
      return result


   # ==========================================================================   
   def __choose_issue_ref(self, book, series_ref, issue_refs, force_b):
      result = None
      series_name_s = series_ref.series_name_s
      issue_num_s = '' if not book.issue_num_s else book.issue_num_s
      if issue_refs == None: raise "issue_refs must be a set"

      if len(issue_refs) == 0 and issue_num_s and not force_b:
         issue_ref = db.query_issue_ref(series_ref, book.issue_num_s)
         if issue_ref:
            result = IssueFormResult("OK", issue_ref)
            log.debug("   ...identified issue number " + sstr(issue_num_s))
            
      if len(issue_refs) == 0 and (not result or force_b):
         for ref in self.__query_issue_refs(series_ref):
            issue_refs.add(ref)
         if self.__cancelled_b: 
            result = IssueFormResult("CANCEL")
         elif len(issue_refs) == 0:
            MessageBox.Show(self.comicrack.MainWindow,
            i18n.get("NoIssuesAvailableText").format(series_name_s),
            i18n.get("NoIssuesAvailableTitle"), MessageBoxButtons.OK, 
               MessageBoxIcon.Warning)
            result = IssueFormResult("BACK")
            log.debug("   ...no issues in this series; user must go back")

      if not result and len(issue_refs) > 0 and issue_num_s:
         counts = {}
         for ref in issue_refs:
            counts[ref.issue_num_s] = counts.get(ref.issue_num_s, 0) + 1
         if issue_num_s in counts and counts[issue_num_s] > 1:
            log.debug("   ...found more than one issue number " + sstr(issue_num_s))
         else:
            for ref in issue_refs:
               if natural_key(ref.issue_num_s) == natural_key(issue_num_s):
                  result = IssueFormResult("OK", ref)
                  log.debug("   ...identified issue number " + sstr(issue_num_s))
                  break

      if not result and not issue_num_s and len(issue_refs)==1:
         result = IssueFormResult("OK", list(issue_refs)[0])

      if not result or force_b:
         if len(issue_refs) == 0:
            result = IssueFormResult("BACK")
         else:
            if not force_b:
               log.debug("   ...could not identify issue number automatically")
            hint = result.get_ref() if result else None
            log.debug("displaying the issue selection dialog...")
            with IssueForm(self, hint, issue_refs, series_ref) as issue_form:
               result = issue_form.show_form()
               result = result if result else IssueFormResult("BACK")
            log.debug('   ...user chose to ' + sstr(result.get_debug_string()))

      return result



   # ==========================================================================   
   def __query_series_refs(self, search_terms_s):
      if not search_terms_s:
         raise Exception("cannot query for empty search terms")
      
      with ProgressBarForm(self.comicrack.MainWindow, self) as progbar:
         def callback(num_matches_n, expected_callbacks_n):
            if not self.__cancelled_b:
               if not progbar.Visible:
                  progbar.pb.Maximum = expected_callbacks_n
                  progbar.show_form()
               if progbar.Visible and not self.__cancelled_b:
                  progbar.pb.PerformStep()
                  progbar.Text = \
                     i18n.get("SearchProgbarText").format(sstr(num_matches_n))
            Application.DoEvents()
            return self.__cancelled_b
         log.debug("searching for series that match '" + sstr(search_terms_s) + "'...")
         
         series_refs = db.query_series_refs( search_terms_s,
            self.config.ignored_searchterms_sl, callback )
         
      filtered_refs = dbutils.filter_series_refs(series_refs,
         self.config.ignored_publishers_sl, 
         self.config.ignored_before_year_n,
         self.config.ignored_after_year_n,
         self.config.never_ignore_threshold_n,
         self.config.allowed_publishers_sl)
      
      filtered_n = len(series_refs) - len(filtered_refs) 
      if filtered_n > 0:
         log.debug("...filtered out " + sstr(filtered_n) + " (of " + sstr(len(series_refs)) + ") results.")
      if len(filtered_refs) == 0:
         log.debug("...no results found for this search")
      else:
         log.debug("...found {0} results".format(len(filtered_refs)))
      return filtered_refs



   # ==========================================================================   
   def __query_issue_refs(self, series_ref):
      log.debug("finding all issues for '" + sstr(series_ref) + "'...")
      with ProgressBarForm(self.comicrack.MainWindow, self) as progform:
         def callback(complete_ratio_n):
            complete_ratio_n = max(0.0, min(1.0, complete_ratio_n))
            if complete_ratio_n < 1.0 and not progform.Visible\
                  and not self.__cancelled_b:
               progform.pb.Maximum = 100
               progform.pb.Value = complete_ratio_n * 100
               progform.show_form()
            if progform.Visible and not self.__cancelled_b:
               progform.pb.Value = complete_ratio_n * 100
               progform.Text = i18n.get("IssuesProgbarText")\
                  .format(sstr((int)(complete_ratio_n * 100)))
            Application.DoEvents()
            return self.__cancelled_b
         issue_refs = db.query_issue_refs(series_ref, callback)
         log.debug("   ...found " + sstr(len(issue_refs)) + " issues in local GCD database")
         return issue_refs


   # =============================================================================
   def __wait_until_ready(self):
       ''' Bypassed for local database operation to ensure maximum performance. '''
#coding: utf-8
'''
This module contains code that search the database in an attempt to 
automatically find a good match for a given ComicBook object. 

@author: Cory Banack (original), refactored by Local CV Scraper Team
and further adapted by Strumples & Gemini for Grand Comics DB.
'''
from dbmodels import IssueRef
import db
import dbutils
import gcd_log as log
from matchscore import MatchScore
import imagehash
import gcd_utils as utils
from gcd_utils import sstr

# when comparing two comic covers, they must be this similar or greater
# (when using imagehash.similarity()) to be considered "the same"
__MATCH_THRESHOLD = 0.87

#==============================================================================
def find_series_ref(book, config):
   ''' 
   Performs a number of queries on the database, in an attempt to find a 
   SeriesRef object that strongly matches the given book.  A variety of 
   techniques are employed, including checking for matching issue numbers in
   the prospective series, and image matching the cover of the prospective 
   issue in the prospective series.  The user's search and filtering 
   preferences (in 'config') are also taken into account.
      
   Returns None if no clear series identification could be made. 
   '''
   
   try:
      # tests to see if two hashes are close enough to be considered "the same"
      def are_the_same(hash1, hash2):
         x = imagehash.similarity(hash1, hash2)
         return x > __MATCH_THRESHOLD
      
      
      retval = None
      series_ref = __find_best_series(book, config)
      if series_ref:
         matches = False
         hash_local = __get_local_hash(book)
         if hash_local:
            # 1. convert SeriesRef + issue num to an IssueRef iff its possible.
            ref = db.query_issue_ref(series_ref, book.issue_num_s) \
               if book.issue_num_s else series_ref
            ref = series_ref if not ref else ref

            # 2. see if the local and remote hashes match up
            hash_remote = __get_remote_hash(ref)
            matches = are_the_same(hash_local, hash_remote)
            
            # 3. if the given ref is an IssueRef, we can try to load the issue's
            #    additional cover images and see if any of them match, too.
            if not matches and type(ref) == IssueRef:
               issue = db.query_issue(ref, True)
               if issue:
                  for ref in issue.image_urls_sl:
                     hash_remote = __get_remote_hash(ref)
                     matches = are_the_same(hash_local, hash_remote)
                     if matches: break
         retval = series_ref if matches else None
         
      return retval
   except Exception as ex:
      log.debug_exc("automatcher.find_series_ref error: " + sstr(ex))
      return None

#==============================================================================
def __find_best_series(book, config):      
   ''' 
   Queries the database to find a best guess for a series matching the given
   ComicBook, based on its name, year, issue number, and other text attributes.
   
   Returns SeriesRef if a reasonable guess was found, or None if one wasn't.
   '''
   
   try:
      # 1. obtain SeriesRefs for this book, removing some as dictated by prefs
      series_refs = db.query_series_refs( book.series_s, 
         config.ignored_searchterms_sl )
      
      series_refs = dbutils.filter_series_refs( 
            series_refs,
            config.ignored_publishers_sl, 
            config.ignored_before_year_n,
            config.ignored_after_year_n,
            config.never_ignore_threshold_n,
            config.allowed_publishers_sl)

      # 2. obtain the first, second, and third best matching SeriesRefs for the
      #    given book, if there are any.
      primary = None
      secondary = None 
      tertiary = None   
      if len(series_refs) > 0:
         mscore = MatchScore()

         # DIAGNOSTIC: log every candidate series and its computed score, so
         # a bad pick can be diagnosed directly from the log instead of
         # guesswork. Sorted best-first, capped to avoid huge logs for very
         # common series names.
         try:
            scored = [(mscore.compute_n(book, r), r) for r in series_refs]
            scored.sort(key=lambda t: t[0], reverse=True)
            log.debug("Series match candidates for '" + sstr(book.series_s) +
               "' #" + sstr(book.issue_num_s) + " (" + sstr(book.pub_year_n) +
               "):")
            for score_n, r in scored[:10]:
               # FIX: Used clean string concatenation (+) instead of comma separators
               log.debug("   score=" + sstr(score_n) + 
                  "  id=" + sstr(r.series_key) +
                  "  name=" + sstr(r.series_name_s) +
                  "  year=" + sstr(r.volume_year_n) +
                  "  issues=" + sstr(r.issue_count_n) +
                  "  pub=" + sstr(r.publisher_s))
         except Exception as ex:
            log.debug_exc("Error logging match candidates: " + sstr(ex))

         def find_best_score( refs ):
            return reduce( lambda x,y: x if mscore.compute_n(book, x) \
               >= mscore.compute_n(book,y) else y, refs) if refs else None
         primary = find_best_score(series_refs)
         if primary:
            series_refs.remove(primary)
            secondary = find_best_score(series_refs)
            if secondary:
               series_refs.remove(secondary)
               tertiary = find_best_score(series_refs)
         
         # 3. if our book is the first (or unknown) issue, figure out if the best  
         #    matching series has a similar cover to the second or third best.
         #    if it does, we're probably dealing with a trade paperback and a 
         #    regular issue, and we can't find the best series reliably, so we bail
         is_first_issue = (lambda i : not i or \
            (utils.is_number(i) and float(i)==1.0))(book.issue_num_s)
         if is_first_issue and primary and secondary:
            too_similar = False
            SIMILARITY_THRESHOLD = __MATCH_THRESHOLD - 0.10
            hash1 = __get_remote_hash(primary)
            hash2 = __get_remote_hash(secondary)
            if imagehash.similarity(hash1, hash2) > SIMILARITY_THRESHOLD:
               too_similar = True
            elif tertiary:
               hash3 = __get_remote_hash(tertiary)
               if imagehash.similarity(hash1, hash3) > SIMILARITY_THRESHOLD:
                  too_similar = True
            primary = None if too_similar else primary
         
      return primary
   except Exception as ex:
      log.debug_exc("automatcher.__find_best_series error: " + sstr(ex))
      return None
            

#==============================================================================
def __get_local_hash(book):
   ''' 
   Gets the image hash for the cover of the give ComicBook object.  Returns
   None if the cover image was empty or couldn't be hashed for any reason.
   '''   
   hash = None # matches nothing
   image = None
   try:
      image = book.create_image_of_page(0) if book else None
      if image:
         image = utils.strip_back_cover(image)
         hash = imagehash.hash(image)
   except Exception as ex:
      log.debug_exc("__get_local_hash exception")
      hash = None
   finally:
      if image: 
         try:
            image.Dispose()
         except:
            pass
   return hash 


#==============================================================================
def __get_remote_hash(ref):
   ''' 
   Gets the image hash for a remote comic book resource.  This resource
   can be a SeriesRef (hashes series art), an IssueRef (hashes the 
   first issue cover) or a URL to an image on the web.
   
   Returns None if the ref led to an image that was empty or \
   couldn't be hashed for any reason.
   '''  
   hash = None # matches nothing
   image = None
   try:
      image = db.query_image(ref) if ref else None
      if image:
         image = utils.strip_back_cover(image)
         hash = imagehash.hash(image)
   except Exception as ex:
      log.debug_exc("__get_remote_hash exception")
      hash = None
   finally:
      if image:
         try:
            image.Dispose()
         except:
            pass
   return hash
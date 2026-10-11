#coding: utf-8
'''
Underlying SQLite database implementation for the Grand Comics Database (GCD).
Aggressive dual-layer relational data compilation for ComicRack / ComicInfo.xml.
'''
import re
import clr
import gcd_log as log
import gcd_utils as utils
from gcd_utils import is_string, sstr
from constants import Tags
from dbmodels import SeriesRef, IssueRef, Issue

clr.AddReference('System')
from System.IO import Directory, File, Path, StreamReader
from System.Text import Encoding

clr.AddReference('System.Drawing')
from System.Drawing import Image

# Get script directory using .NET
_script_dir = Directory.GetParent(__file__).FullName

# Add reference to our custom SQLite wrapper (with FTS5 support)
_sqlitefts_dll = Path.Combine(_script_dir, 'SQLiteFTS.dll')
if File.Exists(_sqlitefts_dll):
   clr.AddReferenceToFileAndPath(_sqlitefts_dll)
else:
   raise Exception("SQLiteFTS.dll not found at: " + _sqlitefts_dll)

from SQLiteFTS import SQLiteConnection as FTSConnection

# ComicRack's package installer flattens subdirectories, so the .crplugin ships
# native\x64\e_sqlite3.dll as e_sqlite3.dll and native\x86\e_sqlite3.dll as
# e_sqlite3_x86.dll next to this script
from System import Environment
_arch = 'x64' if Environment.Is64BitProcess else 'x86'
_native_sqlite = Path.Combine(_script_dir, 'native', _arch, 'e_sqlite3.dll')
_flat_sqlite = Path.Combine(_script_dir, 'e_sqlite3.dll' if _arch == 'x64' else 'e_sqlite3_x86.dll')
if File.Exists(_native_sqlite):
   FTSConnection.InitializeFromDirectory(_script_dir)
elif File.Exists(_flat_sqlite):
   FTSConnection.Initialize(_flat_sqlite)
else:
   raise Exception("No " + _arch + " SQLite library found at: " + _native_sqlite + " or " + _flat_sqlite)

def fix_mojibake(text):
   """Fixes UTF-8 text encoding anomalies."""
   if not text:
      return text
   try:
      text.encode('ascii')
      return text 
   except:
      pass
   try:
      return text.encode('cp1252').decode('utf-8')
   except:
      return text

__connection = None
__db_path = ""
__series_details_cache = None

def _initialize(**kwargs):
   global __connection, __db_path, __series_details_cache
   __series_details_cache = {}
   
   if "db_path" in kwargs:
      __db_path = kwargs["db_path"]
   if not __db_path:
      raise Exception("You must set a database path!")
   if not File.Exists(__db_path):
      raise Exception("Database file not found: " + __db_path)
      
   __connection = FTSConnection(__db_path)
   log.debug("SQLite database opened successfully via SQLiteFTS assembly: " + sstr(__db_path))

def _shutdown():
   global __connection, __series_details_cache
   __series_details_cache = None
   if __connection:
      __connection.Dispose()
      __connection = None
   log.debug("SQLite database closed cleanly.")

def _get_db_name_s():
   return "GCDLocal"

def _create_key_tag_s(issue_key):
   try:
      return Tags.KEY_TAG_PREFIX + utils.sstr(int(issue_key))
   except:
      return None

def _parse_key_tag(text_s):
   if not text_s:
      return None
      
   # Safe Unicode/ASCII normalization pass
   try:
      if isinstance(text_s, str):
         # Safeguard IronPython's string decoding
         text_s = unicode(text_s, 'utf-8', 'ignore')
   except:
      try:
         text_s = unicode(sstr(text_s), 'utf-8', 'ignore')
      except:
         pass
         
   try:
      # Strip out any non-ASCII characters (like \xe9) to prevent regex engine decode failures
      clean_text = text_s.encode('ascii', 'ignore')
   except:
      clean_text = sstr(text_s)

   try:
      tag_found = re.search(r'(?i)' + Tags.KEY_TAG_PREFIX + r'(\d{1,})', clean_text)
      if not tag_found:
         # Safely search for escaped GCD or ComicVine ID tag sets
         tag_found = re.search(r'(?i)GCD\.?\[(\d{1,})', clean_text)
      if not tag_found:
         tag_found = re.search(r'(?i)ComicVine\.?\[(\d{1,})', clean_text)
         
      return int(tag_found.group(1).lower()) if tag_found else None
   except Exception as re_ex:
      log.debug("Key tag regex parsing failed (safely bypassed): " + sstr(re_ex))
      return None

def _check_magic_file(path_s):
   series_ref = None
   file_s = None
   try:
      dir_s = path_s if path_s and Directory.Exists(path_s) else Path.GetDirectoryName(path_s) if path_s else None
      dir_s = dir_s if dir_s and Directory.Exists(dir_s) else None
      if dir_s:
         for f in [dir_s + "\\" + x for x in ["cvinfo.txt", "cvinfo"]]:
            if File.Exists(f):
               file_s = f
         if file_s:
            with StreamReader(file_s, Encoding.UTF8, False) as sr:
               line = sr.ReadToEnd().strip()
               series_ref = __url_to_seriesref(line)
   except:
      pass
   return series_ref

def _query_series_refs(search_terms_s, callback_function):
   series_refs = set()
   search_s = __cleanup_search_terms(search_terms_s, False)
   if search_s:
      if not series_refs:
         series_ref = __url_to_seriesref(search_terms_s)
         if series_ref:
            series_refs.add(series_ref)
      if not series_refs:
         series_refs = __query_series_refs_db(search_s, callback_function)
      if not series_refs:
         altsearch_s = __cleanup_search_terms(search_s, True)
         if search_terms_s and altsearch_s != search_s:
            series_refs = __query_series_refs_db(altsearch_s, callback_function)
   return series_refs

def __query_series_refs_db(search_terms_s, callback_function):
   cleaned = search_terms_s
   for char in ['"', "'", '-', '*', '^', ':', '(', ')', '{', '}', '.']:
      cleaned = cleaned.replace(char, ' ')
   words = [w for w in cleaned.split() if len(w) > 1]
   if not words:
      return set()
      
   series_refs = set()
   
   try:
      fts_query = ' '.join(words)
      sql = """
         SELECT s.id, s.name, s.year_began, s.issue_count, s.id, p.name as publisher_name
         FROM volume_fts f
         JOIN gcd_series s ON f.rowid = s.id
         LEFT JOIN gcd_publisher p ON s.publisher_id = p.id
         WHERE volume_fts MATCH ?
         ORDER BY rank LIMIT 100
      """
      results = __connection.Query(sql, fts_query)
      for row in results:
         series_refs.add(__dict_to_series_ref(row))
      if len(series_refs) > 0:
         return series_refs
   except Exception as ex:
      pass

   try:
      conditions = []
      params = []
      for idx, word in enumerate(words):
         conditions.append("s.name LIKE @w" + str(idx))
         params.append("%" + word + "%")
         
      sql = """
         SELECT s.id, s.name, s.year_began, s.issue_count, s.id, p.name as publisher_name
         FROM gcd_series s
         LEFT JOIN gcd_publisher p ON s.publisher_id = p.id
         WHERE """ + " AND ".join(conditions) + """
         ORDER BY s.issue_count DESC LIMIT 100
      """
      
      results = __connection.Query(sql, *params)
      for row in results:
         series_refs.add(__dict_to_series_ref(row))
   except Exception as ex:
      log.debug_exc("Standard search fallback failed: " + sstr(ex))
      
   return series_refs

def __dict_to_series_ref(row):
   series_id = row['c0'] if row['c0'] else 0
   name = fix_mojibake(sstr(row['c1'])) if row['c1'] else ''
   start_year = sstr(row['c2']) if row['c2'] else ''
   issue_count = row['c3'] if row['c3'] else 0
   image_url = sstr(row['c4']) if row['c4'] else ''
   publisher = fix_mojibake(sstr(row['c5'])) if row['c5'] else ''
   return SeriesRef(series_id, name, start_year if start_year else -1, publisher, issue_count if issue_count else 0, image_url)

def __url_to_seriesref(url_s):
   url_s = url_s.strip()
   pattern = r"^.*?\\b(4000)-(?P<num>\\d{2,})\\b.*$"
   match = re.match(pattern, url_s, re.I)
   if match:
      issue_id = int(match.group("num"))
      try:
         sql = "SELECT series_id FROM gcd_issue WHERE id = @p0"
         results = __connection.Query(sql, issue_id)
         if results and len(results) > 0:
            series_id = results[0]["series_id" if "series_id" in results[0] else "c0"]
            url_s = "4050-" + sstr(series_id)
      except:
         pass
   pattern = r"^.*?\\b(49|4050)-(?P<num>\\d{2,})\\b.*$"
   match = re.match(pattern, url_s, re.I)
   if match:
      return __get_series_ref_by_id(int(match.group("num")))
   return None

def __get_series_ref_by_id(series_id):
   try:
      sql = """
         SELECT s.id, s.name, s.year_began, s.issue_count, s.id, p.name as publisher_name
         FROM gcd_series s
         LEFT JOIN gcd_publisher p ON s.publisher_id = p.id
         WHERE s.id = @p0
      """
      results = __connection.Query(sql, series_id)
      if results and len(results) > 0:
         row = results[0]
         return SeriesRef(int(row["c0"]), sstr(row["c1"]), sstr(row["c2"]) if row["c2"] else -1, sstr(row["c5"]) if row["c5"] else '', int(row["c3"]), sstr(row["c4"]))
   except:
      pass
   return None

def __cleanup_search_terms(search_terms_s, alt_b):
   search_terms_s = search_terms_s.lower()
   search_terms_s = re.sub(r'[\\(\\[]\\d{4}(-\\d{0,4})?[\\)\\]]', '', search_terms_s)
   search_terms_s = re.sub(r" & ", ' and ', search_terms_s)
   search_terms_s = re.sub(r'\\b(c2c|ctc|noads+|tbp)\\b', '', search_terms_s)
   if alt_b:
      search_terms_s = utils.convert_number_words(search_terms_s, True)
   word = re.compile(r"[\w':.-]{1,}")
   return ' '.join(word.findall(search_terms_s))

def _query_issue_refs(series_ref, callback_function=lambda x : False):
   series_id = int(series_ref.series_key)
   issue_refs = set()
   try:
      # Pull the actual cover path/url alias tracked by the database schema
      sql = """
         SELECT MIN(i.id) as id, i.number, 
                COALESCE(NULLIF(i.title, ''), (SELECT title FROM gcd_story WHERE issue_id = i.id AND title != '' LIMIT 1), ''),
                MIN(i.barcode) as cover_path
         FROM gcd_issue i
         WHERE i.series_id = @p0 
         GROUP BY i.number
      """
      results = __connection.Query(sql, series_id)
      for row in results:
         # Safely pass row['c3'] (the cover asset path/id) into the IssueRef model
         issue_refs.add(IssueRef(sstr(row["c1"]), int(row["c0"]), fix_mojibake(sstr(row["c2"])), sstr(row["c3"])))
   except Exception as ex:
      log.debug_exc("Error querying issue refs: " + sstr(ex))
   return issue_refs

def query_issue_ref(series_ref, issue_num_s):
   try:
      series_id = int(series_ref.series_key)
      sql = """
         SELECT MIN(i.id) as id, i.number, 
                COALESCE(
                   NULLIF(i.title, ''),
                   (SELECT NULLIF(title, '') FROM gcd_story WHERE issue_id = i.id AND title != '' LIMIT 1),
                   (SELECT NULLIF(feature, '') FROM gcd_story WHERE issue_id = i.id AND feature != '' LIMIT 1),
                   ''
                ) as display_title, '' as image_url 
         FROM gcd_issue i
         WHERE i.series_id = @p0 AND i.number = @p1 
         GROUP BY i.number LIMIT 1
      """
      results = __connection.Query(sql, series_id, sstr(issue_num_s))
      if results and len(results) > 0:
         row = results[0]
         return IssueRef(sstr(row["c1"]), int(row["c0"]), fix_mojibake(sstr(row["c2"])), sstr(row["c3"]))
   except:
      pass
   return None

def _query_issue(issue_ref, slow_data):
   issue = Issue(issue_ref)
   issue_id = int(issue_ref.issue_key)
   try:
      sql = """
         SELECT i.id, i.number, i.title, i.key_date, i.publication_date, i.price, i.page_count, i.isbn, i.rating, i.variant_name, 
                s.id as series_id, s.name as series_name, s.year_began, s.format, s.notes as series_notes,
                p.name as publisher_name, b.name as brand_name
         FROM gcd_issue i 
         JOIN gcd_series s ON i.series_id = s.id 
         LEFT JOIN gcd_publisher p ON s.publisher_id = p.id 
         LEFT JOIN gcd_brand b ON i.brand_id = b.id
         WHERE i.id = @p0
      """
      results = __connection.Query(sql, issue_id)
      if results and len(results) > 0:
         __parse_issue_from_dict(issue, results[0])
         
         # TAG COVER ART: Push the issue ref's cover path/URL string straight into ComicRack's image target engine
         if hasattr(issue_ref, 'thumb_url_s') and issue_ref.thumb_url_s:
            issue.image_urls_sl.append(issue_ref.thumb_url_s)
            
         __append_relational_story_metadata(issue, issue_id)
         
   except Exception as ex:
      log.debug_exc("Error querying issue: " + sstr(ex))
   return issue

def __parse_issue_from_dict(issue, row):
   def get_str(col_idx):
      key = "c" + str(col_idx)
      val = row[key] if row.ContainsKey(key) else None
      return fix_mojibake(sstr(val)) if val is not None else ''

   issue.issue_key = get_str(0)
   issue.issue_num_s = get_str(1)
   issue.title_s = get_str(2)
   
   key_date = get_str(3)
   if key_date: __parse_date(issue, key_date, 'pub')
   
   issue.published_s = get_str(4)
   issue.price_s = get_str(5)
   issue.page_count_n = int(row['c6']) if row['c6'] else -1
   
   isbn = get_str(7)
   if isbn: issue.isbn_s = isbn.replace('-', '')
   
   issue.age_rating_s = get_str(8)
   issue.variant_s = get_str(9)
   
   issue.series_key = get_str(10)
   issue.series_name_s = get_str(11)
   
   start_year = get_str(12)
   if start_year:
      try: issue.volume_year_n = int(start_year)
      except: pass
         
   format_val = get_str(13)
   if format_val: issue.format_s = format_val
   
   issue.publisher_s = get_str(15)
   issue.imprint_s = get_str(16)

def __append_relational_story_metadata(issue, base_issue_id):
   ''' Gathers and merges metadata from flat string fields and deeply nested relational mapping sets. '''
   try:
      var_sql = """
         SELECT id FROM gcd_issue 
         WHERE series_id = (SELECT series_id FROM gcd_issue WHERE id = @p0) 
           AND number = (SELECT number FROM gcd_issue WHERE id = @p0)
      """
      variant_ids = [int(r['c0']) for r in __connection.Query(var_sql, base_issue_id)]
      if not variant_ids:
         variant_ids = [base_issue_id]

      placeholders = ", ".join(["@p" + str(i) for i in range(len(variant_ids))])
      
      # Layer 1: Query the primary denormalized text columns
      credit_sql = """
         SELECT title, feature, sequence_number, script, pencils, inks, colors, letters, editing, characters, synopsis, genre, reprint_notes, notes 
         FROM gcd_story 
         WHERE issue_id IN ({0})
         ORDER BY sequence_number ASC
      """.format(placeholders)
      stories = __connection.Query(credit_sql, *variant_ids)
      
      summaries = []
      genres = []
      notes_blocks = []
      fallback_titles = []
      
      for s in stories:
         st_title = fix_mojibake(sstr(s['c0'])) if s.ContainsKey('c0') and s['c0'] else ""
         st_feat = fix_mojibake(sstr(s['c1'])) if s.ContainsKey('c1') and s['c1'] else ""
         seq_num = int(s['c2']) if s.ContainsKey('c2') and s['c2'] else 99
         
         # Fallback issue title generation rules
         resolved_t = st_title if st_title else st_feat
         if seq_num > 0 or not issue.title_s:
            if resolved_t and not issue.title_s:
               issue.title_s = resolved_t
            elif resolved_t and resolved_t not in fallback_titles:
               fallback_titles.append(resolved_t)

         def add_creators_flat(key_str, target_list):
            if s.ContainsKey(key_str) and s[key_str]:
               val = fix_mojibake(sstr(s[key_str]))
               for name in [n.strip() for n in re.split(r'[;,]', val) if n.strip()]:
                  if name.lower() not in ['various', '?', 'none', 'unknown'] and name not in target_list: 
                     target_list.append(name)
                     
         add_creators_flat('c3', issue.writers_sl)
         add_creators_flat('c4', issue.pencillers_sl)
         add_creators_flat('c5', issue.inkers_sl)
         add_creators_flat('c6', issue.colorists_sl)
         add_creators_flat('c7', issue.letterers_sl)
         add_creators_flat('c8', issue.editors_sl)
         
         if s.ContainsKey('c9') and s['c9']:
            chars = fix_mojibake(sstr(s['c9']))
            for c in [n.strip() for n in re.split(r'[;,]', chars) if n.strip()]:
               if c and c not in issue.characters_sl: issue.characters_sl.append(c)
         
         if s.ContainsKey('c10') and s['c10']:
            syn = fix_mojibake(sstr(s['c10']))
            if syn and __strip_html(syn) not in summaries: 
               summaries.append(__strip_html(syn))
         
         if s.ContainsKey('c11') and s['c11']:
            gen = fix_mojibake(sstr(s['c11']))
            for g in [g.strip() for g in re.split(r'[;,]', gen) if g.strip()]:
               if g and g not in genres: genres.append(g)
         
         if s.ContainsKey('c12') and s['c12']:
            rep = fix_mojibake(sstr(s['c12']))
            if rep and rep not in notes_blocks: notes_blocks.append("Reprint: " + rep)
         
         if s.ContainsKey('c13') and s['c13']:
            st_notes = fix_mojibake(sstr(s['c13']))
            if st_notes and st_notes not in notes_blocks: notes_blocks.append("Story Notes: " + st_notes)

      # Layer 2: Relational Creator Join Extraction (Overcomes migrated normalized blank fields)
      try:
         rel_credit_sql = """
            SELECT sc.story_id, ct.name, cd.name
            FROM gcd_story_credit sc
            JOIN gcd_credit_type ct ON sc.credit_type_id = ct.id
            JOIN gcd_creator_name_detail cd ON sc.creator_id = cd.id
            WHERE sc.story_id IN (SELECT id FROM gcd_story WHERE issue_id IN ({0}))
         """.format(placeholders)
         rel_credits = __connection.Query(rel_credit_sql, *variant_ids)
         
         for rc in rel_credits:
            role = sstr(rc['c1']).lower() if rc.ContainsKey('c1') else ""
            creator = fix_mojibake(sstr(rc['c2'])) if rc.ContainsKey('c2') else ""
            if not creator or creator.lower() in ['various', '?', 'none', 'unknown']:
               continue
               
            if 'script' in role or 'writer' in role:
               if creator not in issue.writers_sl: issue.writers_sl.append(creator)
            elif 'pencil' in role:
               if creator not in issue.pencillers_sl: issue.pencillers_sl.append(creator)
            elif 'ink' in role:
               if creator not in issue.inkers_sl: issue.inkers_sl.append(creator)
            elif 'color' in role:
               if creator not in issue.colorists_sl: issue.colorists_sl.append(creator)
            elif 'letter' in role:
               if creator not in issue.letterers_sl: issue.letterers_sl.append(creator)
            elif 'editor' in role or 'edit' in role:
               if creator not in issue.editors_sl: issue.editors_sl.append(creator)
            elif 'cover' in role:
               if creator not in issue.cover_artists_sl: issue.cover_artists_sl.append(creator)
      except Exception as e:
         log.debug("Relational creators scan skipped: " + sstr(e))

      # Layer 3: Relational Characters Join Extraction
      try:
         rel_char_sql = """
            SELECT cd.name 
            FROM gcd_story_character sc
            JOIN gcd_character_name_detail cd ON sc.character_id = cd.id
            WHERE sc.story_id IN (SELECT id FROM gcd_story WHERE issue_id IN ({0}))
         """.format(placeholders)
         rel_chars = __connection.Query(rel_char_sql, *variant_ids)
         for rc in rel_chars:
            c_name = fix_mojibake(sstr(rc['c0'])) if rc.ContainsKey('c0') else ""
            if c_name and c_name not in issue.characters_sl: issue.characters_sl.append(c_name)
      except Exception as e:
         pass

      if not issue.title_s and fallback_titles:
         issue.title_s = " / ".join(fallback_titles)
         
      if summaries: issue.summary_s = "\n\n".join(summaries)
      if genres: issue.genre_s = ", ".join(sorted(list(set(genres))))
      if notes_blocks: issue.notes_s = " ; ".join(notes_blocks)

      # Layer 4: Relational Story Arcs and Teams
      try:
         team_sql = """
            SELECT DISTINCT name FROM gcd_group 
            WHERE id IN (SELECT group_id FROM gcd_group_character WHERE story_id IN (SELECT id FROM gcd_story WHERE issue_id IN ({0})))
         """.format(placeholders)
         teams = __connection.Query(team_sql, *variant_ids)
         for t in teams:
            t_name = fix_mojibake(sstr(t['c0']))
            if t_name and t_name not in issue.teams_sl: issue.teams_sl.append(t_name)

         arc_sql = """
            SELECT DISTINCT name FROM gcd_story_arc 
            WHERE id IN (SELECT storyarc_id FROM gcd_story_story_arc WHERE story_id IN (SELECT id FROM gcd_story WHERE issue_id IN ({0})))
         """.format(placeholders)
         arcs = __connection.Query(arc_sql, *variant_ids)
         for a in arcs:
            a_name = fix_mojibake(sstr(a['c0']))
            if a_name and a_name not in issue.story_arcs_sl: issue.story_arcs_sl.append(a_name)
      except:
         pass

   except Exception as ex:
      log.debug("Relational metrics expansion skipped: " + sstr(ex))

def __parse_date(issue, date_str, prefix):
   try:
      parts = date_str.split('-')
      if len(parts) >= 1 and parts[0]: setattr(issue, prefix + '_year_n', int(parts[0]))
      if len(parts) >= 2 and parts[1]: setattr(issue, prefix + '_month_n', int(parts[1]))
      if len(parts) >= 3 and parts[2]: setattr(issue, prefix + '_day_n', int(parts[2]))
   except: pass

def __strip_html(text):
   if not text: return text
   clean = re.sub(r'<[^>]+>', '', text)
   clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
   return re.sub(r'\s+', ' ', clean).strip()

def _query_image(ref, lasttry=False):
   ''' Hybrid Asset Fetcher: Scans local folders first; falls back to the official ComicVine developer REST API 
       using the custom API Key entered directly in your plugin's preferences. '''
   retval = None
   if ref is None: return retval

   # 1. Identify unique primary database identifiers and string contexts
   db_key = ""
   series_name = ""
   issue_num = ""
   
   if hasattr(ref, 'issue_key') and ref.issue_key: db_key = sstr(ref.issue_key)
   elif hasattr(ref, 'series_key') and ref.series_key: db_key = sstr(ref.series_key)
   elif isinstance(ref, (int, float)): db_key = sstr(int(ref))
   elif is_string(ref): db_key = sstr(ref)

   # Isolate raw numeric key strings
   db_key = re.sub(r'\D+', '', db_key)

   if db_key:
      # --- PHASE 1: LOCAL HARD DRIVE SCAN ---
      local_cover_dirs = ["I:\\Comics\\Covers", "D:\\Comics\\Covers", "C:\\Comics\\Covers"]
      for base_dir in local_cover_dirs:
         if Directory.Exists(base_dir):
            for ext in [".jpg", ".jpeg", ".png"]:
               path = Path.Combine(base_dir, db_key + ext)
               if File.Exists(path):
                  try: return Image.FromFile(path)
                  except: pass

      # --- PHASE 2: LOCAL METADATA ENRICHMENT LOOKUP ---
      try:
         if hasattr(ref, 'series_name_s') and ref.series_name_s: 
            series_name = sstr(ref.series_name_s)
         elif hasattr(ref, 'name_s') and ref.name_s: 
            series_name = sstr(ref.name_s)
            
         if hasattr(ref, 'issue_num_s') and ref.issue_num_s: 
            issue_num = sstr(ref.issue_num_s)

         if not series_name and __connection:
            is_issue_query = "SELECT series_id, number FROM gcd_issue WHERE id = @p0 LIMIT 1"
            issue_rows = __connection.Query(is_issue_query, int(db_key))
            
            if issue_rows and len(issue_rows) > 0:
               parent_series_id = int(issue_rows[0]["c0"])
               if not issue_num: 
                  issue_num = sstr(issue_rows[0]["c1"])
                  
               name_query = "SELECT name FROM gcd_series WHERE id = @p0 LIMIT 1"
               name_rows = __connection.Query(name_query, parent_series_id)
               if name_rows and len(name_rows) > 0:
                  series_name = sstr(name_rows[0]["c0"])
            else:
               series_query = "SELECT name FROM gcd_series WHERE id = @p0 LIMIT 1"
               series_rows = __connection.Query(series_query, int(db_key))
               if series_rows and len(series_rows) > 0:
                  series_name = sstr(series_rows[0]["c0"])
      except Exception as db_ex:
         log.debug("Local text context enrichment failed: " + sstr(db_ex))

   # --- PHASE 3: AUTHENTICATED OFFICIAL COMICVINE DEVELOPER API FETCH ---
   if series_name:
      from System.Net import WebRequest
      from System.IO import MemoryStream
      from System import Byte, Array
      from configuration import Configuration
      
      try:
         config = Configuration()
         config.load_defaults()
         cv_api_key = config.api_key_s

         if cv_api_key and len(cv_api_key) >= 32 and not cv_api_key.lower().startswith("gcd"):
            # Clean punctuation out of the series name to protect URL formatting
            clean_series = re.sub(r'[\(\[\].:=]', '', series_name).strip()
            
            # ACCURACY FIX: If we have an issue number, target the /issues/ list endpoint 
            # with strict metadata field filtering instead of a broad keyword search.
            if issue_num:
               api_endpoint_url = "https://comicvine.gamespot.com/api/issues/?api_key={0}&format=json&filter=volume:{1},issue_number:{2}&limit=1".format(
                  cv_api_key, clean_series.replace(' ', '%20'), issue_num.strip()
               )
            else:
               # Fallback to pure volume filtering if no issue number context exists
               api_endpoint_url = "https://comicvine.gamespot.com/api/volumes/?api_key={0}&format=json&filter=name:{1}&limit=1".format(
                  cv_api_key, clean_series.replace(' ', '%20')
               )
            
            req = WebRequest.Create(api_endpoint_url)
            req.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LocalGCDScraper/1.0"
            req.Timeout = 6000
            
            with req.GetResponse() as res:
               with StreamReader(res.GetResponseStream()) as reader:
                  raw_json = reader.ReadToEnd()
                  
                  img_match = re.search(r'"super_url"\s*:\s*"(.*?)"', raw_json)
                  if not img_match:
                     img_match = re.search(r'"medium_url"\s*:\s*"(.*?)"', raw_json)
                     
                  if img_match and img_match.group(1):
                     cv_cdn_url = img_match.group(1).replace(r'\/', '/')
                     
                     img_req = WebRequest.Create(cv_cdn_url)
                     img_req.UserAgent = "Mozilla/5.0"
                     img_req.Timeout = 6000
                     with img_req.GetResponse() as img_res:
                        ms = MemoryStream()
                        buf = Array.CreateInstance(Byte, 2048)
                        st = img_res.GetResponseStream()
                        while True:
                           read = st.Read(buf, 0, 2048)
                           if read <= 0: break
                           ms.Write(buf, 0, read)
                        ms.Position = 0
                        return Image.FromStream(ms)
         else:
            log.debug("ComicVine API lookup skipped: No valid preference key found in settings.dat.")
      except Exception as cv_ex:
         log.debug("Authenticated ComicVine image retrieval failed: " + sstr(cv_ex))

   return None

def query_issue_by_md5(md5_hash):
   return None

def query_issue_by_first_page_md5(first_page_md5):
   return None

def load_all_perceptual_hashes():
   return []
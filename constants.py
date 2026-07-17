"""
Centralized constants for the Local Grand Comics Database Scraper plugin.

This module contains all magic strings, configuration keys, and other constants
used throughout the plugin. Centralizing these values makes maintenance easier
and reduces the risk of typos or inconsistencies.

@author: Local CV Scraper Team for original ComicVine build/ strumples & Gemini
"""

#==============================================================================
# Grand Comics Database Custom Field Names
#==============================================================================
class FieldNames(object):
    # Isolated keys so it creates its own custom fields in ComicRack
    ISSUE_KEY = "gcd_issue"
    SERIES_KEY = "gcd_volume"

#==============================================================================
# Tag Values
#==============================================================================
class Tags(object):
    # Unique tag prefixes so you can distinguish books processed by this plugin
    SKIP_BOOK = "GCDBSKIP"
    KEY_TAG_PREFIX = "GCD"
    LEGACY_KEY_PATTERN = r'(?i)GCD.?\[(\d{1,})'


#==============================================================================
# Configuration Setting Keys
#==============================================================================
class ConfigKeys(object):
    """
    Keys used in the settings.dat configuration file.
    """
    # Database settings
    API_KEY = 'apiKey'  # Legacy, for ComicVine API
    DB_PATH = 'dbPath'  # Path to local SQLite database
    
    # Metadata update toggles
    UPDATE_SERIES = 'updateSeries'
    UPDATE_NUMBER = 'updateNumber'
    UPDATE_RELEASED = 'updateReleased'
    UPDATE_PUBLISHED = 'updatePublished'
    UPDATE_TITLE = 'updateTitle'
    UPDATE_CROSSOVERS = 'updateCrossovers'
    UPDATE_WRITER = 'updateWriter'
    UPDATE_PENCILLER = 'updatePenciller'
    UPDATE_INKER = 'updateInker'
    UPDATE_COVER_ARTIST = 'updateCoverArtist'
    UPDATE_COLORIST = 'updateColorist'
    UPDATE_LETTERER = 'updateLetterer'
    UPDATE_EDITOR = 'updateEditor'
    UPDATE_SUMMARY = 'updateSummary'
    UPDATE_IMPRINT = 'updateImprint'
    UPDATE_PUBLISHER = 'updatePublisher'
    UPDATE_VOLUME = 'updateVolume'
    UPDATE_CHARACTERS = 'updateCharacters'
    UPDATE_TEAMS = 'updateTeams'
    UPDATE_LOCATIONS = 'updateLocations'
    UPDATE_WEBPAGE = 'updateWebpage'
    
    # Behavior settings
    OVERWRITE_EXISTING = 'overwriteExisting'
    IGNORE_BLANKS = 'ignoreBlanks'
    CONVERT_IMPRINTS = 'convertImprints'
    AUTOCHOOSE_SERIES = 'autochooseSeries'
    CONFIRM_ISSUE = 'confirmIssue'
    DOWNLOAD_THUMBS = 'downloadThumbs'
    PRESERVE_THUMBS = 'preserveThumbs'
    FAST_RESCRAPE = 'fastRescrape'
    RESCRAPE_NOTES = 'updateNotes'
    RESCRAPE_TAGS = 'updateTags'
    SUMMARY_DIALOG = 'summaryDialog'
    
    # Hash matching settings
    ENABLE_MD5_MATCH = 'enableMd5Match'
    ENABLE_PHASH_MATCH = 'enablePhashMatch'
    ENABLE_SERIES_SEARCH = 'enableSeriesSearch'
    PHASH_THRESHOLD = 'phashThreshold'


#==============================================================================
# Configuration Default Values
#==============================================================================
class ConfigDefaults(object):
    """
    Default values for configuration settings.
    """
    # Advanced settings defaults
    IGNORED_BEFORE_YEAR = 0
    IGNORED_AFTER_YEAR = 9999999
    NEVER_IGNORE_THRESHOLD = 9999999
    UPDATE_RATING = False
    SHOW_COVERS = True
    WELCOME_DIALOG = True
    ALT_SEARCH_REGEX = ""
    IGNORE_FOLDERS = False
    FORCE_SERIES_ART = False
    NOTE_SCRAPE_DATE = False
    SCRAPE_DELAY = 1
    MAX_SEARCH_RESULTS = 100
    
    # Hash matching defaults
    ENABLE_MD5_MATCH = True
    ENABLE_PHASH_MATCH = True
    ENABLE_SERIES_SEARCH = True
    PHASH_THRESHOLD = 3


#==============================================================================
# Book Status Values
#==============================================================================
class BookStatusValues(object):
    """
    Status values for books during the scrape process.
    """
    # Book was successfully scraped
    SCRAPED = "SCRAPED"
    
    # Book was skipped (user chose to skip or cancel)
    SKIPPED = "SKIPPED"
    
    # Book hasn't been scraped yet
    UNSCRAPED = "UNSCRAPED"
    
    # Book scraping was delayed (will retry at end)
    DELAYED = "DELAYED"


#==============================================================================
# Hash Matching Types
#==============================================================================
class HashMatchTypes(object):
    """
    Types of hash matches that can be returned.
    """
    # MD5 hash of entire file matched
    MD5_FILE = 'md5_file'
    
    # MD5 hash of first page (cover) matched
    MD5_PAGE = 'md5_page'
    
    # Perceptual hash (pHash) matched
    PHASH = 'phash'
    
    # Average hash (aHash) matched
    AHASH = 'ahash'


#==============================================================================
# Database Constants
#==============================================================================
class DatabaseConstants(object):
    DB_NAME = "LocalGCD"
    MAX_HAMMING_DISTANCE = 64
    DEFAULT_SEARCH_LIMIT = 100


#==============================================================================
# File System Constants
#==============================================================================
class FileConstants(object):
    """
    Constants related to file system operations.
    """
    # Magic file names that can specify series info
    CVINFO_FILES = ["cvinfo.txt", "cvinfo"]
    
    # Settings file names (relative to profile directory)
    SETTINGS_FILE = 'settings.dat'
    ADVANCED_FILE = 'advanced.dat'
    GEOMETRY_FILE = 'geometry.dat'
    SERIES_FILE = 'series.dat'
    LOCAL_CACHE_DIR = 'localCache'
    
    # Encoding for colon character in settings (workaround for file format)
    COLON_ENCODING = '|COLON|'
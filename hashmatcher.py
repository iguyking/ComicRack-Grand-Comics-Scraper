'''
This module implements a waterfall hash matching strategy for identifying
comic books from the local database.

The strategy tries multiple methods in order of confidence:
1. Level 1: MD5 Hash Matching (exact file or first page match)
2. Level 2: Perceptual Hash Matching (fuzzy visual comparison)
3. Level 3: Series Name Search (text-based, handled by existing code)

This module handles Levels 1 and 2. Level 3 is the existing search flow.

@author: Local CV Scraper Team
'''

import gcd_log as log
import db
from gcd_utils import sstr
from constants import HashMatchTypes
from hashutils import (calculate_file_md5, calculate_bytes_md5,
                       CTImageHasher, hamming_distance, is_pil_available)

import clr
clr.AddReference('System')
from System.IO import MemoryStream

clr.AddReference('System.Drawing')
from System.Drawing import Image


# =============================================================================
# Module-level cache for perceptual hashes
# =============================================================================

# Cache of all perceptual hashes loaded from database
# Format: List of (gcd_id, ct_phash, ct_ahash, source)
__perceptual_hash_cache = None

# Hash indexes for O(1) exact match lookup
# Format: {hash_value: [(cvid, source), ...]}
__phash_index = None
__ahash_index = None

# Flag to track if cache loading has been attempted
__cache_load_attempted = False


# =============================================================================
def initialize_hash_cache():
    '''
    Pre-load all perceptual hashes from the database into memory.
    Also builds hash indexes for fast exact-match lookups.
    
    Returns:
        Number of hashes loaded
    '''
    global __perceptual_hash_cache, __cache_load_attempted, __phash_index, __ahash_index
    
    if __perceptual_hash_cache is not None:
        return len(__perceptual_hash_cache)
    
    __cache_load_attempted = True
    
    try:
        log.debug("Loading hash cache...")
        __perceptual_hash_cache = db.load_all_perceptual_hashes()
        
        # Build hash indexes for O(1) exact match lookup
        log.debug("Building hash indexes...")
        __phash_index = {}
        __ahash_index = {}
        
        phash_count = 0
        ahash_count = 0
        for cvid, ct_phash, ct_ahash, source in __perceptual_hash_cache:
            # Ensure unsigned 64-bit (defensive, should already be masked from DB load)
            if ct_phash:
                ct_phash_masked = ct_phash & 0xFFFFFFFFFFFFFFFF
                if ct_phash_masked not in __phash_index:
                    __phash_index[ct_phash_masked] = []
                __phash_index[ct_phash_masked].append((cvid, source))
                phash_count += 1
            if ct_ahash:
                ct_ahash_masked = ct_ahash & 0xFFFFFFFFFFFFFFFF
                if ct_ahash_masked not in __ahash_index:
                    __ahash_index[ct_ahash_masked] = []
                __ahash_index[ct_ahash_masked].append((cvid, source))
                ahash_count += 1
        
        log.debug("Loaded " + sstr(len(__perceptual_hash_cache)), 
                  " hashes into cache")
        log.debug("Hash counts - phash entries: " + sstr(phash_count),
                  ", ahash entries: ", sstr(ahash_count))
        log.debug("Built indexes: " + sstr(len(__phash_index)) + " unique phashes, " +
                  sstr(len(__ahash_index)) + " unique ahashes")
        return len(__perceptual_hash_cache)
    except Exception as ex:
        log.debug_exc("Error loading perceptual hash cache: " + sstr(ex))
        __perceptual_hash_cache = []
        __phash_index = {}
        __ahash_index = {}
        return 0


def clear_hash_cache():
    '''
    Clear the perceptual hash cache to free memory.
    Call this when the scrape session ends.
    '''
    global __perceptual_hash_cache, __cache_load_attempted, __phash_index, __ahash_index
    __perceptual_hash_cache = None
    __phash_index = None
    __ahash_index = None
    __cache_load_attempted = False
    log.debug("Perceptual hash cache cleared")


def is_hash_cache_initialized():
    '''
    Check if the perceptual hash cache is already initialized.
    
    Returns:
        True if the cache is loaded, False otherwise
    '''
    global __perceptual_hash_cache
    return __perceptual_hash_cache is not None


# =============================================================================
# Main Waterfall Matching Function
# =============================================================================

def find_issue_by_hash(book, config):
    '''
    Attempt to identify a comic book using the waterfall hash matching strategy.
    
    Args:
        book: ComicBook object to match
        config: Configuration object with matching settings
        
    Returns:
        Tuple of (issue_ref, series_ref, match_type) if found, or (None, None, None)
        match_type is one of HashMatchTypes constants (MD5_FILE, MD5_PAGE, PHASH, AHASH) or None
    '''
    
    # Check if any hash matching is enabled
    if not config.enable_md5_match_b and not config.enable_phash_match_b:
        return (None, None, None)
    
    # Level 1: MD5 Hash Matching
    if config.enable_md5_match_b:
        result = _try_md5_matching(book)
        if result[0] is not None:
            return result
    
    # Level 2: Perceptual Hash Matching  
    if config.enable_phash_match_b:
        result = _try_perceptual_hash_matching(book, config.phash_threshold_n)
        if result[0] is not None:
            return result
    
    # No match found - fall through to Level 3 (series name search)
    return (None, None, None)


# =============================================================================
# Level 1: MD5 Hash Matching
# =============================================================================

def _try_md5_matching(book):
    '''
    Try to match a book using MD5 hash of the file or first page.
    
    Args:
        book: ComicBook object
        
    Returns:
        Tuple of (issue_ref, series_ref, match_type) or (None, None, None)
    '''
    
    # Try file MD5 first (only for books with file paths)
    if book.path_s:
        try:
            file_md5 = calculate_file_md5(book.path_s)
            if file_md5:
                log.debug("Calculated file MD5: " + file_md5)
                issue_ref = db.query_issue_by_md5(file_md5)
                if issue_ref:
                    log.debug("Found exact MD5 file match! CVID: " + 
                              sstr(issue_ref.issue_key))
                    series_ref = db.get_series_ref_for_issue(issue_ref.issue_key)
                    return (issue_ref, series_ref, HashMatchTypes.MD5_FILE)
                else:
                    log.debug("File MD5 match not found in database.")
        except Exception as ex:
            log.debug_exc("Error calculating file MD5: " + sstr(ex))
    
    # Try first page MD5
    try:
        first_page_md5 = _calculate_first_page_md5(book)
        if first_page_md5:
            log.debug("Calculated first page MD5: " + first_page_md5)
            issue_ref = db.query_issue_by_first_page_md5(first_page_md5)
            if issue_ref:
                log.debug("Found exact MD5 first page match! CVID: " + 
                          sstr(issue_ref.issue_key))
                series_ref = db.get_series_ref_for_issue(issue_ref.issue_key)
                return (issue_ref, series_ref, HashMatchTypes.MD5_PAGE)
            else:
                log.debug("First page MD5 match not found in database.")
    except Exception as ex:
        log.debug_exc("Error with first page MD5 matching: " + sstr(ex))
    
    return (None, None, None)


def _calculate_first_page_md5(book):
    '''
    Calculate MD5 hash of the first page (cover) of a comic book.
    
    Args:
        book: ComicBook object
        
    Returns:
        MD5 hash string or None
    '''
    if book.page_count_n < 1:
        return None
    
    image = None
    try:
        image = book.create_image_of_page(0)
        if image is None:
            return None
        
        # Save image to memory stream using PNG format
        # (RawFormat may not have a valid encoder)
        from System.Drawing.Imaging import ImageFormat
        ms = MemoryStream()
        image.Save(ms, ImageFormat.Png)
        data = ms.ToArray()
        ms.Close()
        
        return calculate_bytes_md5(data)
        
    except Exception as ex:
        log.debug_exc("Error calculating first page MD5: " + sstr(ex))
        return None
    finally:
        if image:
            try:
                image.Dispose()
            except:
                pass


# =============================================================================
# Level 2: Perceptual Hash Matching
# =============================================================================

def _try_perceptual_hash_matching(book, threshold):
    '''
    Try to match a book using perceptual hash comparison.
    
    Args:
        book: ComicBook object
        threshold: Maximum Hamming distance for a match (default 3)
        
    Returns:
        Tuple of (issue_ref, series_ref, match_type) or (None, None, None)
    '''
    global __perceptual_hash_cache
    
    # Ensure cache is loaded
    if __perceptual_hash_cache is None:
        initialize_hash_cache()
    
    if not __perceptual_hash_cache:
        log.debug("Perceptual hash cache is empty, skipping phash matching")
        return (None, None, None)
    
    # Calculate perceptual hashes for the book's cover
    book_phash, book_ahash = _calculate_book_perceptual_hashes(book)
    
    if book_phash == 0 and book_ahash == 0:
        log.debug("Could not calculate perceptual hashes for book cover")
        return (None, None, None)
    
    log.debug("Book cover hashes - phash: " + sstr(book_phash), 
              ", ahash: ", sstr(book_ahash))
    
    # FAST PATH: Check for exact matches using hash indexes (O(1) lookup)
    exact_matches = _find_exact_hash_matches(book_phash, book_ahash)
    if exact_matches:
        log.debug("Found " + sstr(len(exact_matches)) + " exact hash match(es) via index lookup")
        # Group by CVID
        cvid_map = {}
        for cvid, hash_type, source in exact_matches:
            if cvid not in cvid_map:
                cvid_map[cvid] = (0, hash_type, source)
        
        unique_cvids = list(cvid_map.keys())
        if len(unique_cvids) == 1:
            cvid = unique_cvids[0]
            distance, hash_type, source = cvid_map[cvid]
            log.debug("Single exact match found! CVID: " + sstr(cvid), 
                      ", type: ", hash_type, ", source: ", source)
            issue_ref = db.get_issue_ref_by_cvid(cvid)
            series_ref = db.get_series_ref_for_issue(cvid)
            return (issue_ref, series_ref, hash_type)
        else:
            log.debug("Multiple exact matches - will need user selection. CVIDs: " + 
                      sstr(unique_cvids[:5]))
            return (None, None, None)
    
    # SLOW PATH: No exact match, search for fuzzy matches within threshold
    log.debug("No exact match, searching for fuzzy matches (threshold=", sstr(threshold), ")...")
    matches, closest_match = _find_perceptual_matches(book_phash, book_ahash, threshold)
    
    if not matches:
        if closest_match:
            log.debug("No perceptual hash matches found within threshold ", 
                      sstr(threshold), ". Closest match: CVID ", 
                      sstr(closest_match[0]), " at distance ", 
                      sstr(closest_match[1]), " (", closest_match[2], ")")
        else:
            log.debug("No perceptual hash matches found within threshold ", 
                      sstr(threshold), " (no close matches in database)")
        return (None, None, None)
    
    # Apply strict best score logic:
    # If any match has distance 0, discard all non-perfect matches
    perfect_matches = [m for m in matches if m[1] == 0]
    if perfect_matches:
        matches = perfect_matches
        log.debug("Found ", sstr(len(perfect_matches)), " perfect phash match(es)")
    
    # Group matches by CVID (same issue might appear in both tables)
    cvid_map = {}  # cvid -> best (distance, hash_type, source)
    for cvid, distance, hash_type, source in matches:
        if cvid not in cvid_map or distance < cvid_map[cvid][0]:
            cvid_map[cvid] = (distance, hash_type, source)
    
    unique_cvids = list(cvid_map.keys())
    log.debug("Found ", sstr(len(unique_cvids)), " unique CVID(s) matching")
    
    # If exactly one unique CVID, return it
    if len(unique_cvids) == 1:
        cvid = unique_cvids[0]
        distance, hash_type, source = cvid_map[cvid]
        log.debug("Single match found! CVID: ", sstr(cvid), 
                  ", distance: ", sstr(distance),
                  ", type: ", hash_type, ", source: ", source)
        
        issue_ref = db.get_issue_ref_by_cvid(cvid)
        series_ref = db.get_series_ref_for_issue(cvid)
        return (issue_ref, series_ref, hash_type)
    
    # Multiple CVIDs matched - this needs user selection
    # For now, return None to fall through to manual search
    # TODO: Implement a selection dialog for multiple phash matches?
    log.debug("Multiple CVIDs matched with same confidence - ",
              "falling through to manual search. CVIDs: ",
              sstr(unique_cvids[:5]), "..." if len(unique_cvids) > 5 else "")
    
    return (None, None, None)


def _calculate_book_perceptual_hashes(book):
    '''
    Calculate ComicTagger-compatible perceptual hashes for a book's cover.
    
    Args:
        book: ComicBook object
        
    Returns:
        Tuple of (ct_phash, ct_ahash) as integers, or (0, 0) on error
    '''
    if not is_pil_available():
        return (0, 0)
    
    # Note: We don't check page_count_n here because it can be stale/zero
    # after "clear data" in ComicRack (bug 235). Instead, we just try to
    # get the page image directly and let it fail gracefully.
    
    image = None
    try:
        image = book.create_image_of_page(0)
        if image is None:
            return (0, 0)
        
        hasher = CTImageHasher(image)
        ct_ahash = hasher.average_hash()
        ct_phash = hasher.perception_hash()
        
        log.debug("Book cover hashes - phash: ", sstr(ct_phash), ", ahash: ", sstr(ct_ahash))
        
        return (ct_phash, ct_ahash)
        
    except Exception as ex:
        log.debug_exc("Error calculating perceptual hashes: " + sstr(ex))
        return (0, 0)
    finally:
        if image:
            try:
                image.Dispose()
            except:
                pass


def _find_exact_hash_matches(book_phash, book_ahash):
    '''
    Fast O(1) lookup for exact hash matches using hash indexes.
    
    Args:
        book_phash: Book's perceptual hash
        book_ahash: Book's average hash
        
    Returns:
        List of (cvid, hash_type, source) tuples for exact matches, or empty list
    '''
    global __phash_index, __ahash_index
    
    matches = []
    
    # Check phash index
    if book_phash and __phash_index and book_phash in __phash_index:
        for cvid, source in __phash_index[book_phash]:
            matches.append((cvid, HashMatchTypes.PHASH, source))
    
    # Check ahash index
    if book_ahash and __ahash_index and book_ahash in __ahash_index:
        for cvid, source in __ahash_index[book_ahash]:
            matches.append((cvid, HashMatchTypes.AHASH, source))
    
    return matches


def _find_perceptual_matches(book_phash, book_ahash, threshold):
    '''
    Search the cached perceptual hashes for matches within threshold.
    
    Implements ComicTagger's exact waterfall approach:
    1. Try phash matching first (if book has phash)
    2. Only if no phash matches, try ahash matching
    
    Args:
        book_phash: Book's perceptual hash
        book_ahash: Book's average hash
        threshold: Maximum Hamming distance
        
    Returns:
        Tuple of (matches_list, closest_match)
        matches_list: List of tuples (cvid, distance, hash_type, source) within threshold
        closest_match: Tuple (cvid, distance, hash_type, source) of closest match beyond threshold, or None
    '''
    global __perceptual_hash_cache
    
    matches = []
    closest_beyond_threshold = None
    closest_distance = 65  # More than max possible (64)
    
    # PHASE 1: Try phash matching first (ComicTagger waterfall behavior)
    if book_phash:
        log.debug("Trying phash matching (threshold=" + sstr(threshold), ")...")
        for cvid, db_phash, db_ahash, source in __perceptual_hash_cache:
            if db_phash:
                phash_dist = hamming_distance(book_phash, db_phash)
                if phash_dist <= threshold:
                    matches.append((cvid, phash_dist, HashMatchTypes.PHASH, source))
                elif phash_dist < closest_distance:
                    closest_distance = phash_dist
                    closest_beyond_threshold = (cvid, phash_dist, HashMatchTypes.PHASH, source)
        
        if matches:
            log.debug("GCD Hash Matcher: found " + sstr(len(matches)) + " database visual matches")
            matches.sort(key=lambda x: x[1])
            return (matches, closest_beyond_threshold)
        else:
            log.debug("No phash matches found, trying ahash...")
    
    # PHASE 2: No phash matches, try ahash (ComicTagger waterfall behavior)
    if book_ahash:
        matches = []  # Clear any previous results
        closest_beyond_threshold = None
        closest_distance = 65
        
        log.debug("Trying ahash matching (threshold=" + sstr(threshold), ")...")
        for cvid, db_phash, db_ahash, source in __perceptual_hash_cache:
            if db_ahash:
                ahash_dist = hamming_distance(book_ahash, db_ahash)
                if ahash_dist <= threshold:
                    matches.append((cvid, ahash_dist, HashMatchTypes.AHASH, source))
                elif ahash_dist < closest_distance:
                    closest_distance = ahash_dist
                    closest_beyond_threshold = (cvid, ahash_dist, HashMatchTypes.AHASH, source)
        
        if matches:
            log.debug("Found " + sstr(len(matches)) + " ahash match(es)")
            matches.sort(key=lambda x: x[1])
            return (matches, closest_beyond_threshold)
    
    return (matches, closest_beyond_threshold)


# =============================================================================
# Utility Functions  
# =============================================================================

def get_hash_cache_size():
    '''
    Get the current size of the perceptual hash cache.
    
    Returns:
        Number of entries in cache, or 0 if not loaded
    '''
    global __perceptual_hash_cache
    return len(__perceptual_hash_cache) if __perceptual_hash_cache else 0


def is_hash_matching_available(config):
    '''
    Check if any hash matching method is enabled and available.
    
    Args:
        config: Configuration object
        
    Returns:
        True if hash matching can be attempted
    '''
    # MD5 matching doesn't require PIL
    if config.enable_md5_match_b:
        return True
    
    # Perceptual hash matching requires PIL
    if config.enable_phash_match_b:
        return is_pil_available()
    
    return False

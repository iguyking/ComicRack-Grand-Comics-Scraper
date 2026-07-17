"""
This module contains the BookStatus class, which represents the various states 
a book can be in while the scraper is running or finished.

Extracted from scrapeengine.py for better modularity.

@author: Cory Banack (original), refactored by Local CV Scraper Team
and further adapted by Strumples & Gemini for Grand Comics DB.
"""

import gcd_utils as utils

#==============================================================================
class BookStatus(object):
    """
    A status object used to represent the various states that a book can be in 
    while the scraper is running or finished.
    
    Status values:
        SCRAPED: Book was successfully scraped and updated with metadata
        SKIPPED: Book was skipped by user choice or due to cancel
        UNSCRAPED: Book hasn't been scraped yet
        DELAYED: Book scraping was postponed (will retry at end of batch)
    """
    
    # Class-level constants for status values
    SCRAPED = "SCRAPED"
    SKIPPED = "SKIPPED"
    UNSCRAPED = "UNSCRAPED"
    DELAYED = "DELAYED"
    
    #===========================================================================         
    def __init__(self, status_id, failed_search_terms_s=""):
        """ 
        Creates a new BookStatus object with the given status ID.
        
        Args:
            status_id: The status ID. Must be one of:
                - "SCRAPED": book was successfully scraped
                - "SKIPPED": user chose to skip this book
                - "UNSCRAPED": hasn't been scraped yet
                - "DELAYED": hasn't been scraped, try again later
            failed_search_terms_s: (optional) The series search terms that 
                couldn't be found, if any. Only meaningful when status_id 
                is "UNSCRAPED".
        
        Raises:
            Exception: If status_id is not one of the valid values
        """  
        valid_statuses = (self.SCRAPED, self.SKIPPED, self.UNSCRAPED, self.DELAYED)
        if status_id not in valid_statuses:
            raise Exception("Invalid status ID: " + str(status_id) + 
                           ". Must be one of: " + str(valid_statuses))
        
        self.__id = status_id
        self.__failed_search_terms_s = failed_search_terms_s \
            if status_id == self.UNSCRAPED and utils.is_string(failed_search_terms_s) \
            else ""
        
    #===========================================================================         
    def __str__(self):
        """Returns the status ID as a string."""
        return self.__id
        
    #===========================================================================         
    def equals(self, status_id):
        """ 
        Returns True iff this BookStatus has the given status ID.
        
        Args:
            status_id: One of "SCRAPED", "UNSCRAPED", "SKIPPED", or "DELAYED"
            
        Returns:
            True if this BookStatus has the given ID, False otherwise
        """
        return self.__id == status_id

    #===========================================================================         
    def get_failed_search_terms_s(self):
        """
        Get the series search terms that could not be found in the comic 
        database, leading to this BookStatus's "UNSCRAPED" status.
        
        Returns:
            The failed search terms string, or "" if there are no failed 
            search terms OR if our status is not "UNSCRAPED".
        """
        return self.__failed_search_terms_s
    
    #===========================================================================         
    def is_scraped(self):
        """Returns True if this book was successfully scraped."""
        return self.__id == self.SCRAPED
    
    #===========================================================================         
    def is_skipped(self):
        """Returns True if this book was skipped."""
        return self.__id == self.SKIPPED
    
    #===========================================================================         
    def is_unscraped(self):
        """Returns True if this book hasn't been scraped yet."""
        return self.__id == self.UNSCRAPED
    
    #===========================================================================         
    def is_delayed(self):
        """Returns True if this book's scraping was delayed."""
        return self.__id == self.DELAYED

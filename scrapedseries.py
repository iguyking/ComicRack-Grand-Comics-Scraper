"""
This module contains the ScrapedSeries class, which holds scraped information
about a comic book series during the scraping process.

Extracted from scrapeengine.py for better modularity.

@author: Cory Banack (original), refactored by Local CV Scraper Team
and further adapted by Strumples & Gemini for Grand Comics DB.
"""

#==============================================================================
class ScrapedSeries(object):
    """
    A container for scraped series information.
    
    This object holds all the scraped information for a particular comic book 
    series - specifically, the SeriesRef for the series and all of the 
    IssueRefs that are associated with that series.
    
    Used as a cache entry during the scrape process to avoid re-fetching
    series data when processing multiple books from the same series.
    """
    
    def __init__(self, series_ref=None):
        """
        Initialize a new ScrapedSeries.
        
        Args:
            series_ref: The SeriesRef object identifying this series in the
                       database. May be None initially.
        """
        # The SeriesRef for this series (identifies the series in the database)
        self.series_ref = series_ref
        
        # Set of IssueRefs for all issues in this series
        # Populated lazily when needed
        self.issue_refs = set()
    
    def has_series_ref(self):
        """Returns True if a series_ref has been assigned."""
        return self.series_ref is not None
    
    def has_issue_refs(self):
        """Returns True if any issue_refs have been loaded."""
        return len(self.issue_refs) > 0
    
    def add_issue_ref(self, issue_ref):
        """
        Add an issue reference to this series.
        
        Args:
            issue_ref: An IssueRef object to add
        """
        if issue_ref is not None:
            self.issue_refs.add(issue_ref)
    
    def clear_issue_refs(self):
        """Clear all cached issue references."""
        self.issue_refs = set()
    
    def __str__(self):
        """Returns a string representation for debugging."""
        return "ScrapedSeries(series_ref={0}, issue_count={1})".format(
            self.series_ref, len(self.issue_refs))

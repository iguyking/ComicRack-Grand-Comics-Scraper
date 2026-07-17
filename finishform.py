'''
This module is home to the FinishForm class.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs.
'''

import clr
import gcd_i18n as i18n
from gcd_resources import Resources
from gcdform import GCDForm 

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, DialogResult

clr.AddReference('System.Drawing')
from System.Drawing import ContentAlignment, Point, Size

# =============================================================================
class FinishForm(GCDForm):
   '''
   This is the last modal popup dialog that you see when you run the scraper.
   It lets you know how many books were scraped, and how many were skipped.
   '''
   
   #===========================================================================
   def __init__(self, scraper, status):
      '''
      Initializes this form.
      
      'scraper' -> the ScrapeEngine that we are running as part of.
      'status' -> a list containing two integers, the first is the number of 
                 books that were scraped and the second is the number that were
                 skipped (both reported to the user by this form)
      '''
      
      GCDForm.__init__(self, scraper.comicrack.MainWindow, "finishformLocation")
      self.__build_gui( status[0], status[1] )

      
   # ==========================================================================
   def __build_gui(self, scraped_n, skipped_n):
      '''
      Constructs and initializes the gui for this form.
      'scraped_n' -> the number of books that were scraped (reported to user)
      'skipped_n' -> the number of books that were skipped (reported to user)
      '''
      
      # 1. --- build each gui component using helper methods
      scrape_text = i18n.get("FinishFormScrapedSingle") if scraped_n==1 else \
         i18n.get("FinishFormScrapedPlural").format(scraped_n)
      skip_text = i18n.get("FinishFormSkippedSingle") if skipped_n==1 else \
         i18n.get("FinishFormSkippedPlural").format(skipped_n)
      
      scrape_label = self.create_label(scrape_text, Point(10, 10), 
                                       Size(280, 13), auto_size=False)
      scrape_label.TextAlign = ContentAlignment.MiddleCenter
      
      skip_label = self.create_label(skip_text, Point(10, 30),
                                     Size(280, 13), auto_size=False)
      skip_label.TextAlign = ContentAlignment.MiddleCenter
      
      ok = self.create_button(i18n.get("MessageBoxOk"),
                              Point(105, 58), Size(90, 23),
                              dialog_result=DialogResult.OK)
   
      # 2. --- configure this form, and add all the gui components to it
      self.AcceptButton = ok
      self.AutoScaleMode = AutoScaleMode.Font
      self.Text = i18n.get("FinishFormTitle").format(Resources.SCRIPT_VERSION)
      self.ClientSize = Size(300, 90)
   
      self.Controls.Add(scrape_label)
      self.Controls.Add(skip_label)
      self.Controls.Add(ok)
      
      # 3. --- define the keyboard focus tab traversal ordering
      ok.TabIndex = 0
      
      # Final UI Enforcement Layer: Overrides missing i18n dictionary lookup anomalies
      try:
         self.Text = "Scraping Operation Complete"
         scrape_label.Text = "Successfully scraped 1 book." if scraped_n == 1 else "Successfully scraped " + str(scraped_n) + " books."
         skip_label.Text = "Skipped 1 book." if skipped_n == 1 else "Skipped " + str(skipped_n) + " books."
         ok.Text = "OK"
      except Exception as ex:
         pass
      
      
   # ==========================================================================
   def show_form(self):
      ''' Displays this form, blocking until the user closes it. '''  
      self.ShowDialog() # blocks
      return None
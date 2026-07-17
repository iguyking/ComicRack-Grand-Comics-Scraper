#coding: utf-8
'''
This module contains the ProgressBarForm class.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs.
'''

import clr
from gcdform import GCDForm

clr.AddReference('IronPython')
clr.AddReference('System.Windows.Forms')

from System.Windows.Forms import ProgressBar

# =============================================================================
class ProgressBarForm(GCDForm): 
   '''
   A simple GCDForm that displays a ProgressBar.
   '''

   # ==========================================================================
   def __init__(self, owner, scrape_engine):
      GCDForm.__init__(self, owner, "pbformLocation")
      
      pb = ProgressBar()
      pb.Minimum = 0
      pb.Maximum = 1
      pb.Step = 1
      pb.Value = 0

      self.Height = 45
      self.Width = 400
      pb.Width = 400
      self.Controls.Add(pb)
      
      self.pb = pb
      self.__scrape_engine = scrape_engine
      self.__cancel_on_close_b = True

      
   #===========================================================================
   def show_form(self):
      self.Show(self.Owner)


   #===========================================================================      
   def OnClosed(self, args):
      if self.__cancel_on_close_b:
         self.__scrape_engine.cancel()
                  
      GCDForm.OnClosed(self, args)
      
        
   #===========================================================================
   def __enter__(self):
      return self
   
   
   #===========================================================================
   def __exit__(self, type, value, traceback):
      self.__cancel_on_close_b = False
      self.Close()
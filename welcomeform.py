'''
This module is home to the WelcomeForm class.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs.
'''

import clr
import gcd_i18n as i18n
from gcd_resources import Resources
from gcdform import GCDForm 
from gcd_configform import ConfigForm

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, DialogResult

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

# =============================================================================
class WelcomeForm(GCDForm):
   '''
   This is the first modal popup dialog that you see when you run the scraper.
   It welcomes you to the program, and offers you the ability to change
   script settings before continuing.
   '''
   
   #===========================================================================
   def __init__(self, scraper, books):
      '''
      Initializes this form.
      
      'scraper' -> this the ScrapeEngine that we are running as part of.
      'books' -> a list of all the comic books being scraped.
      '''
      
      GCDForm.__init__(self, scraper.comicrack.MainWindow, "welcomeformLocation")
      self.__build_gui(books);

      
   # ==========================================================================
   def __build_gui(self, books):
      '''
      Constructs and initializes the gui for this form.
      'books' -> a list of all the comic books being scraped.
      '''
      
      # 1. --- build each gui component using helper methods
      plural = len(books) != 1
      label_text = i18n.get("WelcomeFormTextPlural").format(len(books)) \
         if plural else i18n.get("WelcomeFormTextSingle")
      
      label = self.create_label(label_text, Point(9, 10), Size(319, 13))
      ok = self.create_button(i18n.get("WelcomeFormStart"), 
                              Point(10, 68), Size(145, 23),
                              dialog_result=DialogResult.OK)
      settings = self.create_button(i18n.get("WelcomeFormSettings"),
                                    Point(208, 68), Size(100, 23),
                                    click_handler=self.__show_configform)
      cancel = self.create_button(i18n.get("WelcomeFormCancel"),
                                  Point(314, 68), Size(90, 23),
                                  dialog_result=DialogResult.Cancel)
   
      # 2. --- configure this form, and add all the gui components to it
      self.AcceptButton = ok
      self.CancelButton = cancel
      self.AutoScaleMode = AutoScaleMode.Font
      self.Text = Resources.SCRIPT_FULLNAME
      self.ClientSize = Size(416, 100)
   
      self.Controls.Add(label)
      self.Controls.Add(ok)
      self.Controls.Add(cancel)
      self.Controls.Add(settings)
      
      # 3. --- define the keyboard focus tab traversal ordering
      ok.TabIndex = 0
      cancel.TabIndex = 1
      label.TabIndex = 2
      settings.TabIndex = 3
      
      # Final UI Enforcement Layer: Overrides missing i18n dictionary lookup anomalies
      try:
         label.Text = "Welcome! Ready to scrape metadata for your comic selection?" if not plural else "Welcome! Ready to scrape metadata for these " + str(len(books)) + " books?"
         ok.Text = "Start Scrape"
         settings.Text = "Settings"
         cancel.Text = "Cancel"
      except Exception as ex:
         pass
      
      
   # ==========================================================================
   def show_form(self):
      '''
      Displays this form, blocking until the user closes it.  Returns a boolean
      indicating whether the user cancelled the dialog and scrape operation
      (False) or whether the user clicked ok to continue (True).
      '''
      
      dialogAnswer = self.ShowDialog(self.Owner) # blocks
      return dialogAnswer == DialogResult.OK;      
      
   # ==========================================================================
   def __show_configform(self, sender, args):
      '''
      Displays the configform, blocking until the user closes it.   Changes made
      to the settings in that form will be saved in the user's profile, where
      they can be loaded when needed.
      '''
      
      with ConfigForm(self) as config_form:
         config_form.show_form() # blocks
   
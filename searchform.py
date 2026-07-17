#coding: utf-8
''' 
This module is home to the SearchForm class.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs.
'''

import clr
import gcd_i18n as i18n
from gcdform import GCDForm
import gcd_utils as utils

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AutoScaleMode, Button, \
    DialogResult, Keys, Label, TextBox, ContextMenu, MenuItem

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

#==============================================================================
class SearchForm(GCDForm):
   '''
   This class is a popup, modal dialog with a text field that asks the user to 
   specify search terms for a search query on the local database.
   '''
   
   #===========================================================================
   def __init__(self, scraper, initial_search_s, failed_search_s=""):
      self.__label = None
      self.__fail_label = None
      self.__fail_label_is_visible = bool(failed_search_s and failed_search_s.strip())
      self.__search_button = None
      self.__pressing_controlkey = False;
      self.__skip_button = None
      self.__cancel_button = None
      self.__textbox = None
      
      GCDForm.__init__(self, scraper.comicrack.MainWindow, "searchformLocation")
      self.__scraper = scraper
      scraper.cancel_listeners.append(self.__cancel_close)
      self.__build_gui(initial_search_s, failed_search_s)
      self.FormClosed += self.__form_closed_fired

   #===========================================================================      
   def __build_gui(self, initial_search_s, failed_search_s):
      ''' Constructs and initializes the gui for this form. '''
      
      self.__fail_label = self.__build_fail_label(failed_search_s)
      self.__label = self.__build_label()
      self.__search_button = self.__build_searchbutton()
      self.__skip_button = self.__build_skipbutton()
      self.__cancel_button = self.__build_cancelbutton()
      self.__textbox = self.__build_textbox(
         failed_search_s if failed_search_s else initial_search_s, 
         self.__search_button, self.__cancel_button)
      
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(435, 200 if self.__fail_label_is_visible else 100)
      
      if self.__fail_label_is_visible:
         self.Text = "Series Search Failed"
      else:
         self.Text = "Manual Series Search"
         
      self.KeyDown += self.__key_was_pressed
      self.KeyUp += self.__key_was_released
      self.__textbox.KeyDown += self.__key_was_pressed
      self.__textbox.KeyUp += self.__key_was_released
      self.Deactivate += self.__was_deactivated
      
      self.Controls.Add(self.__fail_label)
      self.Controls.Add(self.__label)
      self.Controls.Add(self.__textbox)
      self.Controls.Add(self.__search_button)
      self.Controls.Add(self.__skip_button)
      self.Controls.Add(self.__cancel_button)
      
      self.__textbox.TabIndex = 0
      self.__search_button.TabIndex = 1
      self.__skip_button.TabIndex = 2 
      self.__cancel_button.TabIndex = 3

      try:
         self.__label.Text = "Enter the comic book series title to search for:"
         self.__search_button.Text = "Search"
         self.__skip_button.Text = "Skip Book"
         self.__cancel_button.Text = "Cancel"
      except:
         pass

   #===========================================================================      
   def __build_fail_label(self, failed_search_s):
      label = Label()
      label.UseMnemonic = False
      label.Location = Point(10, 10)
      label.Size = Size(415, 100)
      label.Visible = self.__fail_label_is_visible   
      if self.__fail_label_is_visible:
         label.Text = "No series matches were found for your query: '" + str(failed_search_s) + "'\n\nPlease refine the series name below and try again."
      return label
   
   #===========================================================================      
   def __build_label(self):
      label = Label()
      label.UseMnemonic = False
      label.Location = Point(10, 110 if self.__fail_label_is_visible else 10)
      label.Size = Size(415, 20)
      return label
         
   #===========================================================================      
   def __build_searchbutton(self):
      button = Button()
      button.DialogResult = DialogResult.OK
      button.Location = Point(125, 170 if self.__fail_label_is_visible else 70)
      button.Size = Size(100, 23)
      button.UseVisualStyleBackColor = True
      return button
   
   #===========================================================================      
   def __build_skipbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Ignore
      button.Location = Point(235, 170 if self.__fail_label_is_visible else 70)
      button.Size = Size(90, 23)
      button.UseVisualStyleBackColor = True
      return button
   
   #===========================================================================      
   def __build_cancelbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Cancel
      button.Location = Point(335, 170 if self.__fail_label_is_visible else 70)
      button.Size = Size(90, 23)
      button.UseVisualStyleBackColor = True
      return button
   
   #===========================================================================      
   def __build_textbox(self, initial_text_s, searchbutton, cancelbutton):
      class SearchTextBox(TextBox):
         def OnKeyPress(self, args):
            if args.KeyChar == chr(13):
               searchbutton.PerformClick()
               args.Handled = True
            elif args.KeyChar == chr(27):
               cancelbutton.PerformClick()
               args.Handled = True
            else:
               TextBox.OnKeyPress(self, args)
               
         def OnTextChanged(self, args):
            searchbutton.Enabled = bool(self.Text.strip())
            
      tbox = SearchTextBox()
      tbox.Location = Point(10, 135 if self.__fail_label_is_visible else 35)
      tbox.Size = Size(415, 1)
      if initial_text_s:
         tbox.Text = initial_text_s
      tbox.SelectAll()
      
      menu = ContextMenu()
      items = menu.MenuItems
      items.Add( MenuItem("Cut", lambda s, ea : tbox.Cut() ) )
      items.Add( MenuItem("Copy", lambda s, ea : tbox.Copy() ) )
      items.Add( MenuItem("Paste", lambda s, ea : tbox.Paste() ) )
      tbox.ContextMenu = menu
      return tbox

   #===========================================================================      
   def show_form(self):
      dialogAnswer = self.ShowDialog( self.Owner )
      if dialogAnswer == DialogResult.OK:
         search_terms_s = self.__textbox.Text.strip()
         return SearchFormResult("SEARCH", search_terms_s) if search_terms_s \
             else SearchFormResult("CANCEL")
      elif dialogAnswer == DialogResult.Ignore:
         if self.ModifierKeys == Keys.Control:
            return SearchFormResult("PERMSKIP")
         else:
            return SearchFormResult("SKIP")
      else:
         return SearchFormResult("CANCEL")

   #===========================================================================
   def __form_closed_fired(self, sender, args):
      self.FormClosed -= self.__form_closed_fired
      try:
         self.__scraper.cancel_listeners.remove(self.__cancel_close)
      except ValueError:
         pass

   #===========================================================================
   def __cancel_close(self):
      ''' FIX: Missing engine-event hook method to handle safe background closure. '''
      try:
         if not self.IsDisposed and not self.Disposing:
            self.DialogResult = DialogResult.Cancel
            self.Close()
      except:
         pass

   #===========================================================================         
   def __key_was_pressed(self, sender, args):
      pass
         
   #===========================================================================         
   def __key_was_released(self, sender, args):
      pass

   #===========================================================================         
   def __was_deactivated(self, sender, args):
      pass

#==============================================================================
class SearchFormResult(object):
   def __init__(self, id, search_terms_s=""):
      self.__id = id
      self.__search_terms_s = search_terms_s

   def equals(self, id):
      return self.__id == id

   def get_search_terms(self):
      return self.__search_terms_s

   def get_debug_string(self):
      if self.__id == "SEARCH":
         return "searching again for: " + self.__search_terms_s
      elif self.__id == "SKIP":
         return "skipping this book"
      elif self.__id == "PERMSKIP":
         return "permanently skipping this book"
      else:
         return "cancelling scrape"
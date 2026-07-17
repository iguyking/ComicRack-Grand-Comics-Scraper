#coding: utf-8
''' 
This module is home to the SeriesForm and SeriesFormResult classes.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs.
'''

import clr
from buttondgv import ButtonDataGridView
from gcdform import GCDForm
from gcd_utils import sstr
from matchscore import MatchScore
import gcd_i18n as i18n
import gcd_log as log
from issuecoverpanel import IssueCoverPanel
 
clr.AddReference('System')
from System.ComponentModel import ListSortDirection

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Application, AutoScaleMode, Button, \
   DataGridViewAutoSizeColumnMode, DataGridViewContentAlignment, \
   DataGridViewSelectionMode, DataGridViewTriState, DialogResult, \
   Keys, Label

#==============================================================================
class SeriesForm(GCDForm):
   '''
   This class is a popup, modal dialog that displays all of the Comic Book
   series that match a particular search string.
   '''

   #===========================================================================
   def __init__(self, scraper, book, series_refs, search_terms_s):
      self.__config = scraper.config
      self.__series_refs = list(series_refs)
      self.__matchscore = MatchScore()
      self.__pressing_controlkey = False;
      self.__ok_button = None
      self.__skip_button = None
      self.__issues_button = None
      self.__table = None
      self.__coverpanel = None
      self.__chosen_index = None
      
      if len(series_refs) <= 0:
         raise Exception("do not invoke the SeriesForm with no series!")
      GCDForm.__init__(self, scraper.comicrack.MainWindow, "seriesformLocation")
      self.__build_gui(book, search_terms_s);
      self.__scraper = scraper
      scraper.cancel_listeners.append(self.__cancel_close)
      
      
   #===========================================================================   
   def __build_gui(self, book, search_terms_s):
      ''' Constructs and initializes the gui for this form. '''
      
      self.__ok_button = self.__build_okbutton()
      self.__skip_button = self.__build_skipbutton()
      search_button = self.__build_searchbutton()
      self.__issues_button = self.__build_issuesbutton()
      label = self.__build_label(search_terms_s, len(self.__series_refs)) 
      self.__table = self.__build_table(
         self.__series_refs, book, self.__ok_button)
      self.__coverpanel = self.__build_coverpanel(book)

      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(730, 395)
      self.Text = "Series Selection Matcher"
      self.FormClosed += self.__form_closed_fired
      self.KeyPreview = True;
      self.KeyDown += self.__key_was_pressed
      self.KeyUp += self.__key_was_released
      self.Deactivate += self.__was_deactivated
      
      self.Controls.Add (label)
      self.Controls.Add(self.__table)
      self.Controls.Add (self.__ok_button)
      self.Controls.Add (self.__skip_button)
      self.Controls.Add (search_button)
      self.Controls.Add (self.__issues_button)
      self.Controls.Add(self.__coverpanel) 
      
      self.__ok_button.TabIndex = 1
      self.__skip_button.TabIndex = 2
      search_button.TabIndex = 3
      self.__issues_button.TabIndex = 4
      self.__coverpanel.TabIndex = 5
      self.__table.TabIndex = 6
      
      self.Shown += self.__change_table_selection_fired

      try:
         label.Text = "Multiple series matches were found. Please select the correct series:"
         self.__ok_button.Text = "Select Series"
         search_button.Text = "Search Again"
         self.__issues_button.Text = "Show Issues"
         self.__skip_button.Text = "Skip Book"
      except:
         pass

   # ==========================================================================
   def __build_table(self, series_refs, book, enter_button):
      table = ButtonDataGridView(enter_button) 
      table.AllowUserToOrderColumns = True
      table.SelectionMode = DataGridViewSelectionMode.FullRowSelect
      table.MultiSelect = False
      table.ReadOnly = True
      table.RowHeadersVisible = False
      table.AllowUserToAddRows = False
      table.AllowUserToResizeRows = False
      table.AllowUserToResizeColumns = False
      table.DefaultCellStyle.NullValue = "--"

      table.Location = Point(10, 60)
      table.Size = Size(500, 290) if self.__config.show_covers_b else Size(710, 290)

      table.ColumnCount = 7
      
      table.Columns[0].Name = "Series"
      table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
      
      table.Columns[1].Name = "Year"
      table.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
      
      table.Columns[2].Name = "Issues"
      table.Columns[2].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
         
      table.Columns[3].Name = "Publisher"
      table.Columns[3].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
         
      table.Columns[4].Name = "ID"
      table.Columns[4].Visible = False
      table.Columns[5].Name = "Match"
      table.Columns[5].Visible = False
      table.Columns[6].Name = "Model ID"
      table.Columns[6].Visible = False

      table.SuspendLayout()
      try:
         num_series = len(series_refs)
         for i in range(num_series):
            table.Rows.Add()
            ref = series_refs[i] 
            table.Rows[i].Cells[0].Value = ref.series_name_s
            if ref.volume_year_n >= 0:
               table.Rows[i].Cells[1].Value = ref.volume_year_n
            table.Rows[i].Cells[2].Value = ref.issue_count_n
            table.Rows[i].Cells[3].Value = ref.publisher_s
            table.Rows[i].Cells[4].Value = ref.series_key
            table.Rows[i].Cells[5].Value = self.__matchscore.compute_n(book, ref)
            table.Rows[i].Cells[6].Value = i
            if i > 0 and i % 50 == 0:
               Application.DoEvents()
      except Exception as ex:
         log.debug_exc("SeriesForm: Error populating table")
         table.Rows.Clear()
         raise
      finally:
         table.ResumeLayout()

      table.Sort( table.Columns[5], ListSortDirection.Descending )
      table.SelectionChanged += self.__change_table_selection_fired
      return table


   # ==========================================================================
   def __build_okbutton(self):
      button = Button()
      button.DialogResult = DialogResult.OK
      button.Location = Point(15, 362)
      button.Size = Size(90, 24)
      return button
   
   def __build_skipbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Ignore
      button.Location = Point(110, 362)
      button.Size = Size(90, 24)
      return button

   def __build_searchbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Retry
      button.Location = Point(275, 362) if self.__config.show_covers_b else Point(485, 362) 
      button.Size = Size(115, 24)
      return button
   
   def __build_issuesbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Yes
      button.Location = Point(395, 362) if self.__config.show_covers_b else Point(605, 362) 
      button.Size = Size(115, 24)
      return button
   
   def __build_label(self, search_terms_s, num_matches_n):
      label = Label()
      label.UseMnemonic = False
      label.Location = Point(10, 20)
      label.Size = Size(480, 40)
      return label
   
   def __build_coverpanel(self, book):
      panel = IssueCoverPanel(self.__config, -9991 if self.__config.force_series_art_b else book.issue_num_s) 
      panel.Location = Point(523, 30)
      if self.__config.show_covers_b:
         panel.Show()
      else:
         panel.Hide()
      return panel
   
   # ==========================================================================
   def show_form(self):
      dialogAnswer = self.ShowDialog(self.Owner)
      if dialogAnswer == DialogResult.OK:
         series = self.__series_refs[self.__chosen_index] 
         result = SeriesFormResult( "OK", series )
         alt_choice = self.__coverpanel.get_alt_issue_cover_choice()
         if alt_choice:
            issue_ref, image_ref = alt_choice
            alt_cover_key = sstr(issue_ref.issue_key) + "-altcover"
            self.__config.session_data_map[alt_cover_key] = image_ref
      elif dialogAnswer == DialogResult.Yes:
         series = self.__series_refs[self.__chosen_index] 
         result = SeriesFormResult( "SHOW", series )
      elif dialogAnswer == DialogResult.Cancel: 
         result = SeriesFormResult( "CANCEL")
      elif dialogAnswer == DialogResult.Ignore:
         if self.ModifierKeys == Keys.Control:
            result = SeriesFormResult( "PERMSKIP" )
         else:
            result = SeriesFormResult( "SKIP" )
      elif dialogAnswer == DialogResult.Retry:
         result = SeriesFormResult( "SEARCH" )
      else:
         raise Exception()
      return result

   #===========================================================================
   def __form_closed_fired(self, sender, args):
      self.__table.Dispose()
      self.__coverpanel.free()      
      self.Closed -= self.__form_closed_fired
      try:
         self.__scraper.cancel_listeners.remove(self.__cancel_close)
      except ValueError:
         pass


   #===========================================================================
   def __cancel_close(self):
      try:
         if not self.IsDisposed and not self.Disposing:
            self.DialogResult = DialogResult.Cancel
            self.Close()
      except:
         pass


   #===========================================================================         
   def __change_table_selection_fired(self, sender, args):
      selected_rows = self.__table.SelectedRows
      if selected_rows.Count == 1:
         self.__chosen_index = selected_rows[0].Cells[6].Value
         self.__coverpanel.set_ref(self.__series_refs[self.__chosen_index])
      else:
         self.__chosen_index = None
         self.__coverpanel.set_ref(None) 
     
      self.__ok_button.Enabled = selected_rows.Count == 1
      self.__issues_button.Enabled = selected_rows.Count == 1
      
               
   #===========================================================================         
   def __key_was_pressed(self, sender, args):
      if args.KeyCode == Keys.ControlKey and not self.__pressing_controlkey:
         self.__pressing_controlkey = True;
         self.__skip_button.Text = "- Skip Book -"
         
   #===========================================================================         
   def __key_was_released(self, sender, args):
      if args.KeyCode == Keys.ControlKey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = "Skip Book"

   #===========================================================================         
   def __was_deactivated(self, sender, args):
      if self.__pressing_controlkey:
         self.__pressing_controlkey = False;
         self.__skip_button.Text = "Skip Book"
      
      
#==============================================================================      
class SeriesFormResult(object):
   def __init__(self, id, ref=None): 
      if id != "OK" and id != "SHOW" and id != "CANCEL" and \
         id != "SKIP" and id != "SEARCH" and id != "PERMSKIP":
         raise Exception()
      if (id == "OK" or id == "SHOW") and ref == None:
         raise Exception()
      
      self.__ref = ref if id == "OK" or id == "SHOW" else None;
      self.__id = id;

   def equals(self, id): 
      return self.__id == id

   def get_ref(self):
      return self.__ref;

   def get_debug_string(self):
      if self.equals("SKIP"):
         return "SKIP scraping this book"
      elif self.equals("PERMSKIP"):
         return "ALWAYS SKIP scraping this book"
      elif self.equals("CANCEL"):
         return "CANCEL this scrape operation"
      elif self.equals("SEARCH"):
         return "SEARCH AGAIN for more series"
      elif self.equals("SHOW"):
         return "SHOW ISSUES for: '" + sstr(self.get_ref()) + "'"
      elif self.equals("OK"):
         return "SCRAPE using: '" + sstr(self.get_ref()) + "'"
      else:
         raise Exception()
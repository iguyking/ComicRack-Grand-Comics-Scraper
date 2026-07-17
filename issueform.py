#coding: utf-8
'''
This module is home to the IssuesForm and IssuesFormResult classes.

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adopted for use with local Grand Comics SQLite DBs. 
'''

import clr
import gcd_i18n as i18n
import gcd_log as log
import gcd_utils as utils
from gcd_utils import sstr
from buttondgv import ButtonDataGridView
from issuecoverpanel import IssueCoverPanel
from gcdform import GCDForm

clr.AddReference('Microsoft.VisualBasic')
from System.ComponentModel import ListSortDirection

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Application, AutoScaleMode, Button, \
   DataGridViewAutoSizeColumnMode, DataGridViewContentAlignment, \
   DataGridViewSelectionMode, DialogResult, Keys, Label

#==============================================================================
class IssueForm(GCDForm):
   '''
   This class is a popup, modal dialog that displays all of the Comic Book
   issues in a series.
   '''
   
   #===========================================================================
   def __init__(self, scraper, issue_ref_hint, issue_refs, series_ref):
      self.__config = scraper.config
      self.__issue_refs = list(issue_refs)
      self.__pressing_controlkey = False;
      self.__ok_button = None
      self.__skip_button = None
      self.__label = None
      self.__table = None
      self.__found_issue_in_table = False
      self.__coverpanel = None
      self.__chosen_index = None
      
      if len(issue_refs) <= 0:
         raise Exception("do not invoke the IssueForm with no IssueRefs!")
      GCDForm.__init__(self, scraper.comicrack.MainWindow, "issueformLocation")
      self.__build_gui(issue_ref_hint, series_ref)
      self.__scraper = scraper
      scraper.cancel_listeners.append(self.__cancel_close)
      
   # ==========================================================================
   def __build_gui(self, issue_ref_hint, series_ref):
      ''' Constructs and initializes the gui for this form. '''
      
      self.__ok_button = self.__build_okbutton()
      self.__skip_button = self.__build_skipbutton()
      back_button = self.__build_backbutton()
      self.__table = self.__build_table(
         self.__issue_refs, issue_ref_hint, self.__ok_button)
      self.__label = self.__build_label(series_ref) 
      self.__coverpanel = self.__build_coverpanel()
      
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(730, 395)
      self.Text = "Issue Selection Matcher"
      self.FormClosed += self.__form_closed_fired
      self.KeyPreview = True;
      self.KeyDown += self.__key_was_pressed
      self.KeyUp += self.__key_was_released
      self.Deactivate += self.__was_deactivated
      
      self.Controls.Add (self.__label)
      self.Controls.Add(self.__table)
      self.Controls.Add(self.__ok_button)
      self.Controls.Add(self.__skip_button)
      self.Controls.Add(back_button)
      self.Controls.Add(self.__coverpanel) 

      self.__ok_button.TabIndex = 1
      self.__skip_button.TabIndex = 2
      back_button.TabIndex = 3
      self.__coverpanel.TabIndex = 4
      self.__table.TabIndex = 5

      self.Shown += self.__change_table_selection_fired

      try:
         self.__label.Text = "Select the specific issue that matches your file:"
         self.__ok_button.Text = "Select Issue"
         back_button.Text = "Back to Series"
         self.__skip_button.Text = "Skip Book"
      except:
         pass

   # ==========================================================================   
   def __build_table(self, issue_refs, issue_ref_hint, enter_button):
      table = ButtonDataGridView(enter_button)
      table.SortCompare += self.__sort_compare_fired
      table.AllowUserToOrderColumns = True
      table.SelectionMode = DataGridViewSelectionMode.FullRowSelect
      table.MultiSelect = False
      table.ReadOnly = True
      table.RowHeadersVisible = False
      table.AllowUserToAddRows = False
      table.AllowUserToResizeRows = False
      table.AllowUserToResizeColumns = False
      table.DefaultCellStyle.NullValue = "--"
      if self.__config.show_covers_b:
         table.Size = Size(500, 290)
         table.Location = Point(218, 60)
      else:
         table.Size = Size(708, 290)
         table.Location = Point(10, 60)
         
      table.ColumnCount = 4
      table.Columns[0].Name = "Issue"
      table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
         
      table.Columns[1].Name = "Title"
      table.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
      
      table.Columns[2].Name = "ID"
      table.Columns[2].Visible = False
      table.Columns[3].Name = "Model ID"
      table.Columns[3].Visible = False

      log.debug("Building issue table with " + sstr(len(issue_refs)) + " issues...")
      table.SuspendLayout()
      try:
         for col in table.Columns:
            col.AutoSizeMode = DataGridViewAutoSizeColumnMode.None
         
         for i in range(len(issue_refs)):
            try:
               title_s = issue_refs[i].title_s
               key = issue_refs[i].issue_key
               issue_num_s = issue_refs[i].issue_num_s   
               
               table.Rows.Add()
               table.Rows[i].Cells[0].Value = issue_num_s if issue_num_s else ''
               table.Rows[i].Cells[1].Value = '   ' + title_s if title_s else ''
               table.Rows[i].Cells[2].Value = key
               table.Rows[i].Cells[3].Value = i
            except Exception as ex:
               continue
            
            if i > 0 and i % 100 == 0:
               Application.DoEvents()
         
         table.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
         table.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
         table.Columns[2].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
         table.Columns[3].AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells
      except Exception as ex:
         log.debug_exc("Error building issue table: " + sstr(ex))
         table.Rows.Clear()
         raise 
      finally:
         table.ResumeLayout()
      
      log.debug("Issue table built with " + sstr(table.Rows.Count) + " rows")

      try:
         table.Sort(table.Columns[0], ListSortDirection.Ascending)
         if issue_ref_hint: 
            for i in range(len(issue_refs)):
               if table.Rows[i].Cells[2].Value == issue_ref_hint.issue_key:
                  table.CurrentCell = table.Rows[i].Cells[0]
                  self.__found_issue_in_table = True
                  break
         if not self.__found_issue_in_table and table.Rows.Count > 0:
            table.CurrentCell = table.Rows[0].Cells[0]
      except Exception as ex:
         log.debug_exc("Error sorting/selecting issue table: " + sstr(ex))
         
      table.SelectionChanged += self.__change_table_selection_fired
      return table
      

   # ==========================================================================
   def __build_okbutton(self):
      button = Button() 
      button.DialogResult = DialogResult.OK
      button.Location = Point(223, 362) if self.__config.show_covers_b else Point(10, 362)
      button.Size = Size(90, 24)
      return button

   # ==========================================================================
   def __build_skipbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Ignore
      button.Location = Point(318, 362) if self.__config.show_covers_b else Point(105, 362)
      button.Size = Size(90, 24)
      return button
      
   # ==========================================================================
   def __build_backbutton(self):
      button = Button()
      button.DialogResult = DialogResult.Retry
      button.Location = Point(595, 362)
      button.Size = Size(125, 24)
      return button

   # ==========================================================================
   def __build_label(self, series_ref):
      name_s = series_ref.series_name_s
      publisher_s = series_ref.publisher_s
      vol_year_n = series_ref.volume_year_n
      vol_year_s = sstr(vol_year_n) if vol_year_n > 0 else ''
      fullname_s = ''
      if name_s:
         if publisher_s:
            if vol_year_s:
               fullname_s = "'"+name_s+"' ("+publisher_s+", " + vol_year_s + ")"
            else:
               fullname_s = "'"+name_s+"' (" + publisher_s + ")"
         else:
            fullname_s = "'"+name_s+"'"
            
      label = Label()
      label.UseMnemonic = False
      label.Text = "Choose the issue that matches your comic series: " + fullname_s
         
      if self.__config.show_covers_b:
         label.Location = Point(218, 20)
         label.Size = Size(480, 40)
      else:
         label.Location = Point(10, 20)
         label.Size = Size(680, 40)
      
      return label
   
   # ==========================================================================
   def __build_coverpanel(self):
      panel = IssueCoverPanel(self.__config)
      panel.Location = Point(10, 30)
      return panel
   
   # ==========================================================================
   def show_form(self):
      dialogAnswer = self.ShowDialog(self.Owner)
      if dialogAnswer == DialogResult.OK:
         issue = self.__issue_refs[self.__chosen_index]
         result = IssueFormResult( "OK", issue )
         alt_choice = self.__coverpanel.get_alt_issue_cover_choice()
         if alt_choice:
            issue_ref, image_ref = alt_choice
            alt_cover_key = sstr(issue_ref.issue_key) + "-altcover"
            self.__config.session_data_map[alt_cover_key] = image_ref
      elif dialogAnswer == DialogResult.Cancel:
         result = IssueFormResult( "CANCEL" )
      elif dialogAnswer == DialogResult.Ignore:
         if self.ModifierKeys == Keys.Control:
            result = SeriesFormResult( "PERMSKIP" )
         else:
            result = IssueFormResult( "SKIP" )
      elif dialogAnswer == DialogResult.Retry:
         result = IssueFormResult( "BACK" )
      else:
         raise Exception()
      return result
   
   # ==========================================================================
   def __form_closed_fired(self, sender, args):
      self.__table.Dispose()
      self.__coverpanel.free()
      self.Closed -= self.__form_closed_fired
      try:
         self.__scraper.cancel_listeners.remove(self.__cancel_close)
      except ValueError:
         pass

   # ==========================================================================
   def __cancel_close(self):
      try:
         if not self.IsDisposed and not self.Disposing:
            self.DialogResult = DialogResult.Cancel
            self.Close()
      except:
         pass

   # ==========================================================================
   def __change_table_selection_fired(self, sender, args):
      selected_rows = self.__table.SelectedRows
      if selected_rows.Count == 1:
         self.__chosen_index = selected_rows[0].Cells[3].Value
         self.__coverpanel.set_ref(self.__issue_refs[self.__chosen_index] )
      else:
         self.__chosen_index = None
         self.__coverpanel.set_ref( None ) 
      self.__ok_button.Enabled = selected_rows.Count == 1
      
   # ==========================================================================
   def __sort_compare_fired(self, sender, args):
      if args.Column.Index == 0: 
         args.SortResult = utils.natural_compare(args.CellValue1, args.CellValue2)
         args.Handled = True
         
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
class IssueFormResult(object):
   def __init__(self, id, ref=None):
      if id != "OK" and id != "CANCEL" and id != "SKIP" and id != "BACK" and id != "PERMSKIP": 
         raise Exception()
      if id == "OK" and ref == None:
         raise Exception()
      self.__ref = ref if id == "OK" else None;
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
      elif self.equals("BACK"):
         return "GO BACK to the series dialog"
      elif self.equals("OK"):
         return "SCRAPE using: '" + sstr(self.get_ref()) + "'"
      else:
         raise Exception()
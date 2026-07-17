#coding: utf-8
'''
This module contains the ConfigForm class (a popup dialog).

@author: Cory Banack for original Comic Vine scraper/Local Cv Scraper team for Local CVDB scraper
         Strumples & Gemini adapted for use with local Grand Comics SQLite DBs.
'''
import clr
import gcd_log as log
from gcdform import GCDForm 
from configuration import Configuration
import gcd_i18n as i18n
import System

clr.AddReference('System.Windows.Forms') 
from System.Windows.Forms import AutoScaleMode, Button, CheckBox, ContextMenu, \
    CheckedListBox, DialogResult, FlatStyle, Label, MenuItem, NumericUpDown, \
    OpenFileDialog, RichTextBox, SelectionMode, TabControl, TabPage, TextBox, \
    LinkLabel

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size, ContentAlignment

# =============================================================================
class ConfigForm(GCDForm):
   '''
   This class is a popup, modal dialog that displays all of the configurable
   options available to the user.
   '''
   
   # ==========================================================================
   def __init__(self, owner):
      ''' Initializes this form. '''
      
      ConfigForm.__SERIES_CB = i18n.get("ConfigFormSeriesCB")
      ConfigForm.__NUMBER_CB = i18n.get("ConfigFormNumberCB")
      ConfigForm.__PUBLISHED_CB = i18n.get("ConfigFormPublishedCB")
      ConfigForm.__RELEASED_CB = i18n.get("ConfigFormReleasedCB")
      ConfigForm.__TITLE_CB = i18n.get("ConfigFormTitleCB")
      ConfigForm.__CROSSOVERS_CB = i18n.get("ConfigFormCrossoversCB")
      ConfigForm.__WRITER_CB = i18n.get("ConfigFormWriterCB")
      ConfigForm.__PENCILLER_CB = i18n.get("ConfigFormPencillerCB")
      ConfigForm.__INKER_CB = i18n.get("ConfigFormInkerCB")
      ConfigForm.__COVER_ARTIST_CB = i18n.get("ConfigFormCoverCB")
      ConfigForm.__COLORIST_CB = i18n.get("ConfigFormColoristCB")
      ConfigForm.__LETTERER_CB = i18n.get("ConfigFormLettererCB")
      ConfigForm.__EDITOR_CB = i18n.get("ConfigFormEditorCB")
      ConfigForm.__SUMMARY_CB = i18n.get("ConfigFormSummaryCB")
      ConfigForm.__IMPRINT_CB = i18n.get("ConfigFormImprintCB")
      ConfigForm.__PUBLISHER_CB = i18n.get("ConfigFormPublisherCB")
      ConfigForm.__VOLUME_CB = i18n.get("ConfigFormVolumeCB")
      ConfigForm.__CHARACTERS_CB = i18n.get("ConfigFormCharactersCB")
      ConfigForm.__TEAMS_CB = i18n.get("ConfigFormTeamsCB")
      ConfigForm.__LOCATIONS_CB = i18n.get("ConfigFormLocationsCB")
      ConfigForm.__WEBPAGE_CB = i18n.get("ConfigFormWebCB")
      
      self.__tabcontrol = None
      self.__ok_button = None
      self.__cancel_button = None
      self.__restore_button = None
      
      self.__ow_existing_cb = None 
      self.__ignore_blanks_cb = None                                          
      self.__autochoose_series_cb = None
      self.__confirm_issue_cb = None
      self.__convert_imprints_cb = None
      self.__summary_dialog_cb = None
      self.__download_thumbs_cb = None
      self.__preserve_thumbs_cb = None
      self.__fast_rescrape_cb = None
      self.__rescrape_tags_cb = None
      self.__rescrape_notes_cb = None
      
      self.__db_path_tbox = None
      self.__browse_button = None
      self.__cv_api_key_tbox = None
      self.__advanced_tbox = None
      self.__update_checklist = None
      
      self.__enable_md5_match_cb = None
      self.__enable_phash_match_cb = None
      self.__enable_series_search_cb = None
      self.__phash_threshold_num = None
      
      GCDForm.__init__(self, owner, "configformLocation", "configformSize")
      self.__build_gui()
      
      try:
         if self.__ok_button: self.__ok_button.Text = "OK"
         if self.__cancel_button: self.__cancel_button.Text = "Cancel"
         if self.__restore_button: self.__restore_button.Text = "Reset to Defaults"
      except Exception as ex:
         log.debug("UI override assignment bypassed: " + str(ex))    

   # ==========================================================================          
   def __build_gui(self):
      ''' Constructs and initializes the gui for this form. '''
      self.__ok_button = self.__build_okbutton()
      self.__cancel_button = self.__build_cancel_button()
      self.__restore_button = self.__build_restore_button()
      self.__tabcontrol = self.__build_tabcontrol()
         
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(416, 375)
      self.Text = "Local GCD Scraper Preferences"
   
      self.Controls.Add(self.__ok_button)                                     
      self.Controls.Add(self.__cancel_button)                                 
      self.Controls.Add(self.__restore_button)                                
      self.Controls.Add(self.__tabcontrol)                             
      
      self.__ok_button.TabIndex = 0                                        
      self.__cancel_button.TabIndex = 1                                    
      self.__restore_button.TabIndex = 2
      self.__tabcontrol.TabIndex = 3                                 

      self.__ok_button.Text = "OK"
      self.__cancel_button.Text = "Cancel"
      self.__restore_button.Text = "Reset to Defaults"

      self.__fired_update_gui()  

   # ==========================================================================
   def __build_okbutton(self):
      button = Button()
      button.DialogResult = DialogResult.OK
      button.Location = Point(228, 343)
      button.Size = Size(80, 23)
      button.Text = "OK"
      return button

   # ==========================================================================
   def __build_restore_button(self):
      button = Button()
      button.Click += self.__fired_restore_defaults
      button.Location = Point(10, 343)
      button.Size = Size(170, 23)
      button.Text = "Reset to Defaults"
      return button

   # ==========================================================================
   def __build_cancel_button(self):
      button = Button()
      button.DialogResult = DialogResult.Cancel
      button.Location = Point(315, 343)
      button.Size = Size(90, 23)
      button.Text = "Cancel"
      return button

   # ==========================================================================
   def __build_tabcontrol(self):
      tabcontrol = TabControl()
      tabcontrol.Location = Point(10, 15)
      tabcontrol.Size = Size(395, 302)
      
      tabcontrol.Controls.Add( self.__build_gcdtab() )
      tabcontrol.Controls.Add( self.__build_detailstab() )
      tabcontrol.Controls.Add( self.__build_behaviourtab() )
      tabcontrol.Controls.Add( self.__build_datatab() )
      tabcontrol.Controls.Add( self.__build_hashmatchtab() )
      tabcontrol.Controls.Add( self.__build_advancedtab() )
      
      return tabcontrol

   # ==========================================================================
   def __build_gcdtab(self):
      tabpage = TabPage()
      tabpage.Text = "Database"
      tabpage.Name = "database"
      
      # 1. Database File Inputs
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Location = Point(34, 25)
      label.Size = Size(315, 25)
      label.Text = "Local Grand Comics Database (.db) File Path:"
      
      fired_update_gui = self.__fired_update_gui
      class DbPathTextBox(TextBox):
         def OnTextChanged(self, args): fired_update_gui()
            
      self.__db_path_tbox = DbPathTextBox()
      tbox = self.__db_path_tbox
      tbox.Location = Point(34, 50)
      tbox.Size = Size(270, 22)
      
      self.__browse_button = Button()
      self.__browse_button.Text = "..."
      self.__browse_button.Location = Point(310, 48)
      self.__browse_button.Size = Size(40, 23)
      self.__browse_button.Click += self.__fired_browse_db
      
      # 2. ComicVine API Key Inputs
      cv_label = Label()
      cv_label.UseMnemonic = False
      cv_label.AutoSize = True
      cv_label.Location = Point(34, 105)
      cv_label.Text = "ComicVine Developer API Key:"
      
      self.__cv_api_key_tbox = TextBox()
      self.__cv_api_key_tbox.Location = Point(34, 125)
      self.__cv_api_key_tbox.Size = Size(315, 22)
      
      # 3. Informational Description Label Context
      desc_label = Label()
      desc_label.UseMnemonic = False
      desc_label.AutoSize = False
      desc_label.Location = Point(34, 160)
      desc_label.Size = Size(315, 60)
      desc_label.ForeColor = System.Drawing.Color.DimGray
      desc_label.Text = "Note: The ComicVine API Key is only needed to display cover images in the GUI selector windows."
      
      tabpage.Controls.Add(label)
      tabpage.Controls.Add(tbox)
      tabpage.Controls.Add(self.__browse_button)
      tabpage.Controls.Add(cv_label)
      tabpage.Controls.Add(self.__cv_api_key_tbox)
      tabpage.Controls.Add(desc_label)
      
      return tabpage
   
   # ==========================================================================
   def __build_detailstab(self):
      tabpage = TabPage()
      tabpage.Text = "Details"
      tabpage.Name = "details"
      
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Location = Point(14, 35)
      label.Size = Size(299, 17)
      label.Text = i18n.get("ConfigFormDetailsText")
      
      checkall_button = Button()
      checkall_button.Click += self.__fired_checkall
      checkall_button.Location = Point(280, 107)
      checkall_button.Size = Size(100, 23)
      checkall_button.Text = i18n.get("ConfigFormDetailsAll")
      
      uncheckall_button = Button()
      uncheckall_button.Click += self.__fired_uncheckall
      uncheckall_button.Location = Point(280, 138)
      uncheckall_button.Size = Size(100, 23)
      uncheckall_button.Text = i18n.get("ConfigFormDetailsNone")
      
      self.__update_checklist = CheckedListBox()
      self.__update_checklist.CheckOnClick = True
      self.__update_checklist.ColumnWidth = 125
      self.__update_checklist.ThreeDCheckBoxes = True
      self.__update_checklist.Location = Point(15, 65)
      self.__update_checklist.MultiColumn = True
      self.__update_checklist.SelectionMode = SelectionMode.One
      self.__update_checklist.Size = Size(260, 170)
      self.__update_checklist.ItemCheck += self.__fired_update_gui
      
      self.__update_checklist.Items.Add(ConfigForm.__SERIES_CB)
      self.__update_checklist.Items.Add(ConfigForm.__VOLUME_CB)
      self.__update_checklist.Items.Add(ConfigForm.__NUMBER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__TITLE_CB)
      self.__update_checklist.Items.Add(ConfigForm.__PUBLISHED_CB)
      self.__update_checklist.Items.Add(ConfigForm.__RELEASED_CB)
      self.__update_checklist.Items.Add(ConfigForm.__CROSSOVERS_CB)
      self.__update_checklist.Items.Add(ConfigForm.__PUBLISHER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__IMPRINT_CB)
      self.__update_checklist.Items.Add(ConfigForm.__WRITER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__PENCILLER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__INKER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__COLORIST_CB)
      self.__update_checklist.Items.Add(ConfigForm.__LETTERER_CB)
      self.__update_checklist.Items.Add(ConfigForm.__COVER_ARTIST_CB)
      self.__update_checklist.Items.Add(ConfigForm.__EDITOR_CB)
      self.__update_checklist.Items.Add(ConfigForm.__SUMMARY_CB)
      self.__update_checklist.Items.Add(ConfigForm.__CHARACTERS_CB)
      self.__update_checklist.Items.Add(ConfigForm.__TEAMS_CB)
      self.__update_checklist.Items.Add(ConfigForm.__LOCATIONS_CB)     
      self.__update_checklist.Items.Add(ConfigForm.__WEBPAGE_CB)
   
      tabpage.Controls.Add(label)
      tabpage.Controls.Add(checkall_button)
      tabpage.Controls.Add(uncheckall_button)
      tabpage.Controls.Add(self.__update_checklist)
      
      return tabpage

   # ==========================================================================
   def __build_behaviourtab(self):
      tabpage = TabPage()
      tabpage.Text = "Behavior"
      
      first_scrape_label = Label()
      first_scrape_label.AutoSize = False
      first_scrape_label.FlatStyle = FlatStyle.System
      first_scrape_label.Location = Point(52, 27)
      first_scrape_label.Text = i18n.get("ConfigFormFirstScrapeLabel")
      first_scrape_label.Size = Size(300, 17)
      
      self.__autochoose_series_cb = CheckBox()
      self.__autochoose_series_cb.AutoSize = False
      self.__autochoose_series_cb.FlatStyle = FlatStyle.System
      self.__autochoose_series_cb.Location = Point(82, 45)
      self.__autochoose_series_cb.Size = Size(300, 34)
      self.__autochoose_series_cb.Text =i18n.get("ConfigFormAutochooseSeriesCB")
      self.__autochoose_series_cb.CheckedChanged += self.__fired_update_gui
       
      self.__confirm_issue_cb = CheckBox()
      self.__confirm_issue_cb.AutoSize = False
      self.__confirm_issue_cb.FlatStyle = FlatStyle.System
      self.__confirm_issue_cb.Location = Point(82, 75)
      self.__confirm_issue_cb.Size = Size(300, 34)
      self.__confirm_issue_cb.Text = i18n.get("ConfigFormConfirmIssueCB")
      self.__confirm_issue_cb.CheckedChanged += self.__fired_update_gui
      
      self.__fast_rescrape_cb = CheckBox()
      self.__fast_rescrape_cb.AutoSize = False
      self.__fast_rescrape_cb.FlatStyle = FlatStyle.System
      self.__fast_rescrape_cb.Location = Point(52, 116)
      self.__fast_rescrape_cb.Size = Size(300, 34)
      self.__fast_rescrape_cb.Text = i18n.get("ConfigFormRescrapeCB")
      self.__fast_rescrape_cb.CheckedChanged += self.__fired_update_gui
      
      self.__rescrape_notes_cb = CheckBox()
      self.__rescrape_notes_cb.AutoSize = False
      self.__rescrape_notes_cb.FlatStyle = FlatStyle.System
      self.__rescrape_notes_cb.Location = Point(82, 151)
      self.__rescrape_notes_cb.Size = Size(270, 17)
      self.__rescrape_notes_cb.Text = i18n.get("ConfigFormRescrapeNotesCB")
      self.__rescrape_notes_cb.CheckedChanged += self.__fired_update_gui
      
      self.__rescrape_tags_cb = CheckBox()
      self.__rescrape_tags_cb.AutoSize = False
      self.__rescrape_tags_cb.FlatStyle = FlatStyle.System
      self.__rescrape_tags_cb.Location = Point(82, 181)
      self.__rescrape_tags_cb.Size = Size(270, 17)
      self.__rescrape_tags_cb.Text = i18n.get("ConfigFormRescrapeTagsCB")
      self.__rescrape_tags_cb.CheckedChanged += self.__fired_update_gui 
   
      self.__summary_dialog_cb = CheckBox()
      self.__summary_dialog_cb.AutoSize = False
      self.__summary_dialog_cb.FlatStyle = FlatStyle.System
      self.__summary_dialog_cb.Location = Point(52, 214)
      self.__summary_dialog_cb.Size = Size(300, 34)
      self.__summary_dialog_cb.Text = i18n.get("ConfigFormShowSummaryCB")
      self.__summary_dialog_cb.CheckedChanged += self.__fired_update_gui 
            
      tabpage.Controls.Add(first_scrape_label)
      tabpage.Controls.Add(self.__autochoose_series_cb)
      tabpage.Controls.Add(self.__confirm_issue_cb)
      tabpage.Controls.Add(self.__fast_rescrape_cb)
      tabpage.Controls.Add(self.__rescrape_tags_cb)
      tabpage.Controls.Add(self.__rescrape_notes_cb)
      tabpage.Controls.Add(self.__summary_dialog_cb)
      
      tabpage.Name = "behavior"
      
      return tabpage
   
   # ==========================================================================
   def __build_datatab(self):
      tabpage = TabPage()
      tabpage.Text = "Data Options"
      
      self.__convert_imprints_cb = CheckBox()
      self.__convert_imprints_cb.AutoSize = False
      self.__convert_imprints_cb.FlatStyle = FlatStyle.System
      self.__convert_imprints_cb.Location = Point(52, 35)
      self.__convert_imprints_cb.Size = Size(300, 34)
      self.__convert_imprints_cb.Text = i18n.get("ConfigFormImprintsCB")
      self.__convert_imprints_cb.CheckedChanged += self.__fired_update_gui
       
      self.__ow_existing_cb = CheckBox()
      self.__ow_existing_cb.AutoSize = False
      self.__ow_existing_cb.FlatStyle = FlatStyle.System
      self.__ow_existing_cb.Location = Point(52, 85)
      self.__ow_existing_cb.Size = Size(310, 34)
      self.__ow_existing_cb.Text = i18n.get("ConfigFormOverwriteCB")
      self.__ow_existing_cb.CheckedChanged += self.__fired_update_gui 
   
      self.__ignore_blanks_cb = CheckBox()                                          
      self.__ignore_blanks_cb.AutoSize = False                                       
      self.__ignore_blanks_cb.FlatStyle = FlatStyle.System                          
      self.__ignore_blanks_cb.Location = Point(82, 125)                             
      self.__ignore_blanks_cb.Size = Size(270, 34)                                  
      self.__ignore_blanks_cb.TextAlign = ContentAlignment.TopLeft                                  
      self.__ignore_blanks_cb.Text = i18n.get("ConfigFormOverwriteEmptyCB")                  
      self.__ignore_blanks_cb.CheckedChanged += self.__fired_update_gui 
   
      self.__download_thumbs_cb = CheckBox()
      self.__download_thumbs_cb.AutoSize = False
      self.__download_thumbs_cb.FlatStyle = FlatStyle.System
      self.__download_thumbs_cb.Location = Point(52, 165)
      self.__download_thumbs_cb.Size = Size(300, 34)
      self.__download_thumbs_cb.Text = i18n.get("ConfigFormFilelessCB")
      self.__download_thumbs_cb.CheckedChanged += self.__fired_update_gui
      
      self.__preserve_thumbs_cb = CheckBox()
      self.__preserve_thumbs_cb.AutoSize = False
      self.__preserve_thumbs_cb.FlatStyle = FlatStyle.System
      self.__preserve_thumbs_cb.Location = Point(82, 205)
      self.__preserve_thumbs_cb.Size = Size(270, 34)
      self.__preserve_thumbs_cb.TextAlign = ContentAlignment.TopLeft
      self.__preserve_thumbs_cb.Text = i18n.get("ConfigFormFilelessOverwriteCB")
      self.__preserve_thumbs_cb.CheckedChanged += self.__fired_update_gui
            
      tabpage.Controls.Add(self.__ow_existing_cb)
      tabpage.Controls.Add(self.__ignore_blanks_cb)
      tabpage.Controls.Add(self.__convert_imprints_cb)
      tabpage.Controls.Add(self.__download_thumbs_cb)
      tabpage.Controls.Add(self.__preserve_thumbs_cb)

      tabpage.Name = "dataoptions"
      
      return tabpage
  
   # ==========================================================================
   def __build_hashmatchtab(self):
      tabpage = TabPage()
      tabpage.Text = "Hash Matching"
      tabpage.Name = "hashmatch"
      
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = False
      label.Location = Point(14, 20)
      label.Size = Size(365, 40)
      label.Text = "Configure the waterfall hash matching strategy. Higher confidence methods are tried first."
      
      level1_label = Label()
      level1_label.AutoSize = True
      level1_label.Location = Point(14, 65)
      level1_label.Text = "Level 1 - MD5 Hash (Exact Match):"
      level1_label.Font = System.Drawing.Font(level1_label.Font, System.Drawing.FontStyle.Bold)
      
      self.__enable_md5_match_cb = CheckBox()
      self.__enable_md5_match_cb.AutoSize = False
      self.__enable_md5_match_cb.FlatStyle = FlatStyle.System
      self.__enable_md5_match_cb.Location = Point(30, 85)
      self.__enable_md5_match_cb.Size = Size(340, 34)
      self.__enable_md5_match_cb.Text = "Enable MD5 hash matching (file and first page)"
      self.__enable_md5_match_cb.CheckedChanged += self.__fired_update_gui
      
      level2_label = Label()
      level2_label.AutoSize = True
      level2_label.Location = Point(14, 125)
      level2_label.Text = "Level 2 - Perceptual Hash (Fuzzy Visual):"
      level2_label.Font = System.Drawing.Font(level2_label.Font, System.Drawing.FontStyle.Bold)
      
      self.__enable_phash_match_cb = CheckBox()
      self.__enable_phash_match_cb.AutoSize = False
      self.__enable_phash_match_cb.FlatStyle = FlatStyle.System
      self.__enable_phash_match_cb.Location = Point(30, 145)
      self.__enable_phash_match_cb.Size = Size(340, 34)
      self.__enable_phash_match_cb.Text = "Enable perceptual hash matching (cover image)"
      self.__enable_phash_match_cb.CheckedChanged += self.__fired_update_gui
      
      threshold_label = Label()
      threshold_label.AutoSize = True
      threshold_label.Location = Point(50, 182)
      threshold_label.Text = "Hamming distance threshold (0=exact, lower=stricter):"
      
      self.__phash_threshold_num = NumericUpDown()
      self.__phash_threshold_num.Location = Point(320, 180)
      self.__phash_threshold_num.Size = Size(50, 20)
      self.__phash_threshold_num.Minimum = 0
      self.__phash_threshold_num.Maximum = 20
      self.__phash_threshold_num.Value = 3
      self.__phash_threshold_num.ValueChanged += self.__fired_update_gui
      
      level3_label = Label()
      level3_label.AutoSize = True
      level3_label.Location = Point(14, 215)
      level3_label.Text = "Level 3 - Series Name Search (Text):"
      level3_label.Font = System.Drawing.Font(level3_label.Font, System.Drawing.FontStyle.Bold)
      
      self.__enable_series_search_cb = CheckBox()
      self.__enable_series_search_cb.AutoSize = False
      self.__enable_series_search_cb.FlatStyle = FlatStyle.System
      self.__enable_series_search_cb.Location = Point(30, 235)
      self.__enable_series_search_cb.Size = Size(340, 34)
      self.__enable_series_search_cb.Text = "Enable series name text search (fallback)"
      self.__enable_series_search_cb.CheckedChanged += self.__fired_update_gui
      
      tabpage.Controls.Add(label)
      tabpage.Controls.Add(level1_label)
      tabpage.Controls.Add(self.__enable_md5_match_cb)
      tabpage.Controls.Add(level2_label)
      tabpage.Controls.Add(self.__enable_phash_match_cb)
      tabpage.Controls.Add(threshold_label)
      tabpage.Controls.Add(self.__phash_threshold_num)
      tabpage.Controls.Add(level3_label)
      tabpage.Controls.Add(self.__enable_series_search_cb)
      
      return tabpage
  
   # ==========================================================================
   def __build_advancedtab(self):
      tabpage = TabPage()
      tabpage.Text = "Advanced"
      
      label = Label()
      label.UseMnemonic = False
      label.AutoSize = True
      label.Location = Point(14, 25)
      label.Size = Size(299, 17)
      label.Text = i18n.get("ConfigFormAdvancedText")
      
      tbox = RichTextBox()
      tbox.Multiline=True
      tbox.MaxLength=65536
      tbox.WordWrap = True
      tbox.Location = Point(15, 50)
      tbox.Size = Size(355, 200)
      
      menu = ContextMenu()
      items = menu.MenuItems
      items.Add( MenuItem(i18n.get("TextCut"), lambda s, ea : tbox.Cut() ) )
      items.Add( MenuItem(i18n.get("TextCopy"), lambda s, ea : tbox.Copy() ) )
      items.Add( MenuItem(i18n.get("TextPaste"), lambda s, ea : tbox.Paste() ) )
      tbox.ContextMenu = menu
      self.__advanced_tbox = tbox
      
      tabpage.Controls.Add(label)
      tabpage.Controls.Add(self.__advanced_tbox)

      tabpage.Name = "advanced"
      
      return tabpage
         
   # ==========================================================================
   def show_form(self):
      ''' Displays this form, blocking until the user closes it. '''
      log.debug("opened the settings dialog.")
      defaults = Configuration()
      defaults.load_defaults()
      self.__set_configuration(defaults) 
      self.__switch_to_best_tab()
      dialogAnswer = self.ShowDialog() 
      if dialogAnswer == DialogResult.OK:
         config = self.__get_configuration()
         config.save_defaults()
         log.debug("closed the settings dialog.")
      else:
         config = None
         log.debug("cancelled the settings dialog.")
      return config

   # ==========================================================================
   def __switch_to_best_tab(self):
      ''' Chooses the best tab to be displayed, and switch to it. '''
      have_db_path = self.__db_path_tbox.Text.strip()
      if have_db_path:
         for tab in self.__tabcontrol.Controls.Find("details", False):
            self.__tabcontrol.SelectedTab = tab
      else:
         for tab in self.__tabcontrol.Controls.Find("database", False):
            self.__tabcontrol.SelectedTab = tab
      
   # ==========================================================================
   def __get_configuration(self):
      def is_checked( checkbox ):
         return self.__update_checklist.GetItemChecked( \
            self.__update_checklist.Items.IndexOf(checkbox) )
      
      config = Configuration()
      
      config.update_series_b = is_checked(ConfigForm.__SERIES_CB)
      config.update_number_b = is_checked(ConfigForm.__NUMBER_CB)
      config.update_published_b = is_checked(ConfigForm.__PUBLISHED_CB)
      config.update_released_b = is_checked(ConfigForm.__RELEASED_CB)
      config.update_title_b = is_checked(ConfigForm.__TITLE_CB)
      config.update_crossovers_b = is_checked(ConfigForm.__CROSSOVERS_CB)
      config.update_writer_b = is_checked(ConfigForm.__WRITER_CB)
      config.update_penciller_b = is_checked(ConfigForm.__PENCILLER_CB)
      config.update_inker_b = is_checked(ConfigForm.__INKER_CB)
      config.update_cover_artist_b = is_checked(ConfigForm.__COVER_ARTIST_CB)
      config.update_colorist_b = is_checked(ConfigForm.__COLORIST_CB)
      config.update_letterer_b = is_checked(ConfigForm.__LETTERER_CB)
      config.update_editor_b = is_checked(ConfigForm.__EDITOR_CB)
      config.update_summary_b = is_checked(ConfigForm.__SUMMARY_CB)
      config.update_imprint_b = is_checked(ConfigForm.__IMPRINT_CB)
      config.update_publisher_b = is_checked(ConfigForm.__PUBLISHER_CB)
      config.update_volume_b = is_checked(ConfigForm.__VOLUME_CB)
      config.update_characters_b = is_checked(ConfigForm.__CHARACTERS_CB)
      config.update_teams_b = is_checked(ConfigForm.__TEAMS_CB)
      config.update_locations_b = is_checked(ConfigForm.__LOCATIONS_CB)
      config.update_webpage_b = is_checked(ConfigForm.__WEBPAGE_CB)

      config.ow_existing_b = self.__ow_existing_cb.Checked
      config.convert_imprints_b = self.__convert_imprints_cb.Checked
      config.autochoose_series_b = self.__autochoose_series_cb.Checked
      config.confirm_issue_b = self.__confirm_issue_cb.Checked
      config.ignore_blanks_b = self.__ignore_blanks_cb.Checked
      config.download_thumbs_b = self.__download_thumbs_cb.Checked
      config.preserve_thumbs_b = self.__preserve_thumbs_cb.Checked
      config.fast_rescrape_b = self.__fast_rescrape_cb.Checked
      config.rescrape_notes_b = self.__rescrape_notes_cb.Checked
      config.rescrape_tags_b = self.__rescrape_tags_cb.Checked
      config.summary_dialog_b = self.__summary_dialog_cb.Checked
      
      config.advanced_settings_s = self.__advanced_tbox.Text
      config.db_path_s = self.__db_path_tbox.Text.strip()
      config.api_key_s = self.__cv_api_key_tbox.Text.strip()
      
      config.enable_md5_match_b = self.__enable_md5_match_cb.Checked
      config.enable_phash_match_b = self.__enable_phash_match_cb.Checked
      config.enable_series_search_b = self.__enable_series_search_cb.Checked
      config.phash_threshold_n = int(self.__phash_threshold_num.Value)
      
      return config
 
   # ==========================================================================
   def __set_configuration(self, config):
      def set_checked( checkbox, checked ):
         self.__update_checklist.SetItemChecked( \
            self.__update_checklist.Items.IndexOf(checkbox), checked )
      
      set_checked(ConfigForm.__SERIES_CB, config.update_series_b)
      set_checked(ConfigForm.__NUMBER_CB, config.update_number_b)
      set_checked(ConfigForm.__PUBLISHED_CB, config.update_published_b)
      set_checked(ConfigForm.__RELEASED_CB, config.update_released_b)
      set_checked(ConfigForm.__TITLE_CB, config.update_title_b)
      set_checked(ConfigForm.__CROSSOVERS_CB, config.update_crossovers_b)
      set_checked(ConfigForm.__WRITER_CB, config.update_writer_b)
      set_checked(ConfigForm.__PENCILLER_CB, config.update_penciller_b)
      set_checked(ConfigForm.__INKER_CB, config.update_inker_b)
      set_checked(ConfigForm.__COVER_ARTIST_CB,config.update_cover_artist_b)
      set_checked(ConfigForm.__COLORIST_CB, config.update_colorist_b)
      set_checked(ConfigForm.__LETTERER_CB, config.update_letterer_b)
      set_checked(ConfigForm.__EDITOR_CB, config.update_editor_b)
      set_checked(ConfigForm.__SUMMARY_CB, config.update_summary_b)
      set_checked(ConfigForm.__IMPRINT_CB, config.update_imprint_b)
      set_checked(ConfigForm.__PUBLISHER_CB, config.update_publisher_b)
      set_checked(ConfigForm.__VOLUME_CB, config.update_volume_b)
      set_checked(ConfigForm.__CHARACTERS_CB, config.update_characters_b)
      set_checked(ConfigForm.__TEAMS_CB, config.update_teams_b)
      set_checked(ConfigForm.__LOCATIONS_CB, config.update_locations_b)
      set_checked(ConfigForm.__WEBPAGE_CB, config.update_webpage_b)
      
      self.__ow_existing_cb.Checked = config.ow_existing_b
      self.__convert_imprints_cb.Checked = config.convert_imprints_b
      self.__autochoose_series_cb.Checked = config.autochoose_series_b
      self.__confirm_issue_cb.Checked = config.confirm_issue_b
      self.__ignore_blanks_cb.Checked = config.ignore_blanks_b
      self.__download_thumbs_cb.Checked = config.download_thumbs_b
      self.__preserve_thumbs_cb.Checked = config.preserve_thumbs_b
      self.__fast_rescrape_cb.Checked = config.fast_rescrape_b
      self.__rescrape_notes_cb.Checked = config.rescrape_notes_b
      self.__rescrape_tags_cb.Checked = config.rescrape_tags_b
      self.__summary_dialog_cb.Checked = config.summary_dialog_b
      
      self.__advanced_tbox.Text = config.advanced_settings_s
      self.__db_path_tbox.Text = config.db_path_s.strip()
      self.__cv_api_key_tbox.Text = config.api_key_s.strip()
      
      self.__enable_md5_match_cb.Checked = config.enable_md5_match_b
      self.__enable_phash_match_cb.Checked = config.enable_phash_match_b
      self.__enable_series_search_cb.Checked = config.enable_series_search_b
      self.__phash_threshold_num.Value = int(config.phash_threshold_n) if config.phash_threshold_n is not None else 3
      
      self.__fired_update_gui()
      
   # ==========================================================================
   def __fired_restore_defaults(self, sender, args):
      db_path_s = self.__db_path_tbox.Text 
      self.__set_configuration(Configuration())
      self.__db_path_tbox.Text = db_path_s
      log.debug("all settings were restored to their default values")
      self.__fired_update_gui()
      
   # ==========================================================================
   def __fired_update_gui(self, sender = None, args = None):
      self.__ignore_blanks_cb.Enabled = self.__ow_existing_cb.Checked
      self.__preserve_thumbs_cb.Enabled = self.__download_thumbs_cb.Checked
      if self.__confirm_issue_cb.Checked:
         self.__autochoose_series_cb.Checked = False
      if self.__autochoose_series_cb.Checked:
         self.__confirm_issue_cb.Checked = False
      self.__confirm_issue_cb.Enabled = not self.__autochoose_series_cb.Checked
      self.__autochoose_series_cb.Enabled = not self.__confirm_issue_cb.Checked
      
      if self.__phash_threshold_num:
         self.__phash_threshold_num.Enabled = self.__enable_phash_match_cb.Checked
      
      self.__ok_button.Enabled = self.__db_path_tbox.Text.strip()      
       
   # ==========================================================================
   def __fired_browse_db(self, sender, args):
      dialog = OpenFileDialog()
      dialog.Filter = "SQLite Database Files (*.db)|*.db|All Files (*.*)|*.*"
      dialog.Title = "Select Local Grand Comics Database"
      if dialog.ShowDialog() == DialogResult.OK:
         self.__db_path_tbox.Text = dialog.FileName
   
   # ==========================================================================
   def __fired_checkall(self, sender, args):
      for i in range(self.__update_checklist.Items.Count):
         self.__update_checklist.SetItemChecked(i, True)
   
   # ==========================================================================
   def __fired_uncheckall(self, sender, args):
      for i in range(self.__update_checklist.Items.Count):
         self.__update_checklist.SetItemChecked(i, False)
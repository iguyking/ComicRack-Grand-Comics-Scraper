#coding: utf-8
''' 
This module is home to the IssueCoverPanel class.
 
@author: Cory Banack
'''
import clr
from dbmodels import IssueRef, SeriesRef
from dbpicturebox import DBPictureBox
from scheduler import Scheduler
import gcd_utils as utils
from gcd_utils import sstr
import db
import gcd_i18n as i18n
import re

clr.AddReference('System.Drawing')
from System.Drawing import ContentAlignment, Font, FontStyle, Point, Size

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Button, Panel, LinkLabel

#==============================================================================
class IssueCoverPanel(Panel): 
   '''
   This panel is a compound gui component for displaying a comic book's issue 
   or series cover art (in a DBPictureBox), along with a few extra decorations.  
   '''
   
   #===========================================================================
   def __init__(self, config, issue_num_hint_s=None):
      self.__config = config
      self.__issue_num_hint_s = issue_num_hint_s
      self.__coverpanel = None
      self.__label = None
      self.__link_callback = None
      self.__nextbutton = None
      self.__prevbutton = None
      self.__ref = None
      self.__button_cache = {}
      self.__series_cache = {}
      self.__finder_scheduler = Scheduler()
      self.__setter_scheduler = Scheduler()
      self.__alt_cover_choice = None
      
      Panel.__init__(self)
      self.__build_gui()
      
   # ==========================================================================
   def __build_gui(self):
      ''' Constructs and initializes the gui for this panel. '''
      self.__coverpanel = self.__build_coverimage()
      self.__label = self.__build_label()
      self.__nextbutton = self.__build_nextbutton()
      self.__prevbutton = self.__build_prevbutton()
      
      self.Size = Size(195, 360)
      self.Controls.Add(self.__coverpanel)
      self.Controls.Add(self.__prevbutton)
      self.Controls.Add(self.__label)
      self.Controls.Add(self.__nextbutton)

      self.set_ref(None)

   # ==========================================================================
   def __build_coverimage(self):
      cover = DBPictureBox()
      cover.Location = Point(0, 0)
      cover.Size = Size(195, 320)
      cover.Visible = self.__config.show_covers_b
      return cover
   
   # ==========================================================================
   def __build_label(self):
      label = LinkLabel()
      label.UseMnemonic = False
      label.Visible = self.__config.show_covers_b
      label.Location = Point(18, 326)
      label.Size = Size(155,36)
      label.TextAlign = ContentAlignment.MiddleCenter
      
      def link_clicked(sender, args):
         if self.__link_callback:
            self.__link_callback()
      label.LinkClicked += link_clicked

      return label
   
   # ==========================================================================
   def __build_nextbutton(self):
      button = Button()
      button.Location = Point(173, 332)
      button.Size = Size(20, 24)
      button.Text = '>'
      button.Font = Font(button.Font, FontStyle.Bold)
      button.UseVisualStyleBackColor = True
      button.Click += self.__button_click_fired
      return button
   
   # ==========================================================================
   def __build_prevbutton(self):
      button = Button()
      button.Location = Point(2, 332)
      button.Size = Size(20, 24)
      button.Text = '<'
      button.Font = Font(button.Font, FontStyle.Bold)
      button.UseVisualStyleBackColor = True
      button.Click += self.__button_click_fired
      return button

   # ==========================================================================
   def free(self): 
      if type(self.__ref) == IssueRef:
         issue_ref = self.__ref
         button_model = self.__button_cache[issue_ref]
         if button_model:
            if button_model.can_decrement():
               image_ref = button_model.get_current_ref()
               if utils.is_string(image_ref):
                  self.__alt_cover_choice = (issue_ref, image_ref)
      
      self.__finder_scheduler.shutdown(False)
      self.__setter_scheduler.shutdown(False)
      self.set_ref(None)
      self.__coverpanel.free()
      self.__prevbutton = None
      self.__nextbutton = None
      self.__label = None
      self.Dispose()

   # ==========================================================================
   def set_ref(self, ref):
      run_in_background = type(ref) == SeriesRef and self.__issue_num_hint_s       
      if run_in_background:
         def maybe_convert_seriesref_to_issue_ref(ref):
            if not ref in self.__series_cache:
               issue_ref = db.query_issue_ref(ref, self.__issue_num_hint_s)
               self.__series_cache[ref] = issue_ref if issue_ref else ref
                  
            def change_ref():
               if self.__coverpanel and not self.__coverpanel.IsDisposed:
                  self.__ref = self.__series_cache[ref]
                  self.__update()
            utils.invoke(self.__coverpanel, change_ref, False)
            
         def dummy(): 
            maybe_convert_seriesref_to_issue_ref(ref)
         self.__setter_scheduler.submit(dummy)
      else:
         self.__ref = ref
         self.__update()

   # ==========================================================================
   def get_alt_issue_cover_choice(self):
      return self.__alt_cover_choice

   # ==========================================================================
   def __update(self):
      ''' Updates control items. Explicitly forces an un-clicked searching sequence for instant rendering. '''
      ref = self.__ref
      cache = self.__button_cache
      cover_image = self.__coverpanel
      nextbutton = self.__nextbutton
      prevbutton = self.__prevbutton
      label = self.__label
      scheduler = self.__finder_scheduler
      
      if ref is None or cache is None:
         cover_image.set_image_ref(None)
         nextbutton.Visible = False
         prevbutton.Visible = False
         label.Text = ''
      else:
         # FIX: Forces the baseline mapping state directly into 'searching' to trigger background stream threads on load
         if not cache.has_key(ref):
            cache[ref] = _ButtonModel(ref, \
              'searched' if type(ref) == SeriesRef else 'searching')
            
         bmodel = cache[ref]
         cover_image.set_image_ref( bmodel.get_current_ref() )
         nextbutton.Visible = cover_image.Visible and bmodel.can_increment()
         prevbutton.Visible = cover_image.Visible and bmodel.can_decrement()
         
         label.Links.Clear()
         self.__link_callback = None
         issue_num_s = ref.issue_num_s if type(ref) == IssueRef else ''
         
         if bmodel.get_status() == 'searched':
            if issue_num_s:
               if len(bmodel) > 1:
                  fmt = i18n.get("IssueCoverPanelPlural")
                  if not fmt or fmt.startswith("IssueCoverPanel"): fmt = "Issue #{0} (Cover {1} of {2})"
                  label.Text = fmt.format(sstr(issue_num_s), sstr(bmodel.get_position()+1), sstr(len(bmodel)))
               else:
                  fmt = i18n.get("IssueCoverPanelSingle")
                  if not fmt or fmt.startswith("IssueCoverPanel"): fmt = "Issue #{0}"
                  label.Text = fmt.format(sstr(issue_num_s))
            else:
               fmt = i18n.get("IssueCoverPanelSeries")
               label.Text = fmt if fmt and not fmt.startswith("IssueCoverPanel") else "Series Cover"
         elif bmodel.get_status() == 'searching': 
            fmt = i18n.get("IssueCoverPanelSearching")
            if not fmt or fmt.startswith("IssueCoverPanel"): fmt = "Searching for covers #{0}..."
            label.Text = fmt.format(sstr(issue_num_s))
         elif bmodel.get_status() == 'not-searched':
            fmt = i18n.get("IssueCoverPanelSearchable")
            if not fmt or fmt.startswith("IssueCoverPanel"): fmt = "Issue #{0} (Click to search covers)"
            label.Text = fmt.format(sstr(issue_num_s))
            
            start = label.Text.find('(')
            end = label.Text.find(')', start) if start > -1 else -1
            if start >= 0 and end >= start:
               label.Links.Add(start+1, end)
               def link_callback():
                  bmodel.set_status("searching")
                  self.__update()
               self.__link_callback = link_callback 
         else:
            raise Exception()
            
         search_for_more_covers = cache[ref].get_status()=='searching'
         if search_for_more_covers:
            def update_cache(): 
               issue = db.query_issue(ref, True) if type(ref) == IssueRef else None 
                  
               def update_bmodel():  
                  if self.IsDisposed:
                     return
                  bmodel = cache[ref]
                  if issue and len(issue.image_urls_sl) > 1:
                     for i in range(1, len(issue.image_urls_sl)):
                        bmodel.add_new_ref(issue.image_urls_sl[i])
                  bmodel.set_status('searched')
                  self.__update() 
               utils.invoke(self, update_bmodel, False)
            scheduler.submit(update_cache)
       
   # ==========================================================================
   def __button_click_fired(self, sender, args):
      bmodel = self.__button_cache[self.__ref]
      if sender == self.__nextbutton:
         bmodel.increment()
      else:
         bmodel.decrement()
      self.__update()         
         
# =============================================================================     
class _ButtonModel(object):
   def __init__(self, ref, status="not-searched"):
      self.__image_refs = []
      self.__status = None
      self.set_status(status)
      self.__pos_n = 0
      self.add_new_ref(ref)
      
   #===========================================================================
   def add_new_ref(self, image_ref):
      if image_ref:
         if not image_ref in self.__image_refs:
            self.__image_refs.append(image_ref)
            
   #===========================================================================
   def get_current_ref(self):
      return self.__image_refs[self.__pos_n] if self.__image_refs else None

   #===========================================================================
   def increment(self):
      self.__pos_n = min(len(self.__image_refs)-1, self.__pos_n + 1)
      
   #===========================================================================
   def can_increment(self):
      return self.__pos_n < len(self.__image_refs)-1

   #===========================================================================
   def decrement(self):
      self.__pos_n = max(0, self.__pos_n - 1)

   #===========================================================================
   def can_decrement(self):
      return self.__pos_n > 0
      
   #===========================================================================
   def set_status(self, status):
      if status=='not-searched' or status=='searching' or status=='searched':
         self.__status = status
      else:
         raise Exception("bad status received: ", sstr(status))
      
   #===========================================================================
   def get_status(self):
      return self.__status
   
   #===========================================================================
   def get_position(self):
      return self.__pos_n
   
   #===========================================================================
   def __len__(self):
      return len(self.__image_refs)
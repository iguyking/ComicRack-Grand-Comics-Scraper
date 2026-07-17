#coding: utf-8
'''
The module is the home of the ComicForm class.

@author: Cory Banack (original), refactored by Local CV Scraper Team
and further adapted by Strumples & Gemini for Grand Comics DB.
'''

import clr
import gcd_log as log
import gcd_utils as utils
from gcd_utils import sstr
import gcd_i18n as i18n
from gcd_resources import Resources
from gcdform import GCDForm

clr.AddReference('IronPython')

clr.AddReference('System')
from System import GC, Array
from System.IO import Path

clr.AddReference('System.Drawing')
from System.Drawing import Color, GraphicsUnit, Point, Rectangle, Size, Font, FontStyle
from System.Drawing.Imaging import ColorMap, ImageAttributes

from System.Threading import Monitor, Thread, ThreadStart, \
   ThreadExceptionEventHandler

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import AnchorStyles, Application, AutoScaleMode, \
   Button, Cursors, FormBorderStyle, Label, MouseButtons, PaintEventHandler, \
   Panel, PictureBox, PictureBoxSizeMode, ProgressBar

# =============================================================================
class ComicForm(GCDForm):
   '''
   This class is a standalone dialog that displays the current status of 
   a ScrapeEngine.
   '''
   
   # ==========================================================================
   def __init__(self, scraper):
      ''' Initializes this form. '''
      GCDForm.__init__(self, scraper.comicrack.MainWindow, "comicformLocation", "comicformSize")
      
      self.__cancel_on_close = True
      self.__already_closed = False
      self.__scraper = scraper
      self.__current_book = None
      self.__current_page = 0 
      self.__current_page_count = 0
      
      self.__build_gui()
   
   # ==========================================================================          
   def __build_gui(self):
      ''' Constructs and initializes the gui for this form. '''
      
      self.__progbar = ProgressBar()
      self.__progbar.Minimum = 0
      self.__progbar.Maximum = 0
      self.__progbar.Step = 1
      self.__progbar.Value = 0
      self.__progbar.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
      self.__progbar.Width = 320
      self.__progbar.Height = 20
      self.__progbar.Location = Point(13, 15)
      
      self.__label = Label()
      self.__label.UseMnemonic = False
      self.__label.Text = ''
      self.__label.Location = Point(13, 45)
      self.__label.Size = Size(320, 15)
      self.__label.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
      self.__label.AutoSize = False
      
      self.__pbox_panel = _PictureBoxPanel()
      self.__pbox_panel.Location = Point(13, 65)
      self.__pbox_panel.Size = Size(320, 496)
      self.__pbox_panel.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
      self.__pbox_panel.MouseClick += self.__picture_box_clicked
      self.__pbox_panel.MouseDoubleClick += self.__picture_box_clicked
      
      self.__cancel_button = Button()
      def cancel(sender, args):
         self.__cancel_button.Enabled = False
         self.Close()
      self.__cancel_button.Click += cancel
      self.__cancel_button.Location = Point(78, 572)
      self.__cancel_button.Size = Size(190, 23)
      self.__cancel_button.Anchor = AnchorStyles.Bottom
         
      self.AutoScaleMode = AutoScaleMode.Font
      self.ClientSize = Size(346, 604)  
      self.MinimumSize = Size(166,275)
      self.FormBorderStyle = FormBorderStyle.Sizable
      self.Icon = None
   
      self.Controls.Add(self.__progbar)
      self.Controls.Add(self.__label)
      self.Controls.Add(self.__pbox_panel)
      self.Controls.Add(self.__cancel_button)
      
      self.__scraper.start_scrape_listeners.append(self.__start_scrape)
      self.__scraper.cancel_listeners.append(self.close_threadsafe)
      self.FormClosing += self.__form_closing_fired
      self.FormClosed += self.__form_closed_fired
      
      self.__cancel_button.TabIndex = 0                                        

      try:
         self.Text = "Metadata Scraping Engine Progress"
         self.__cancel_button.Text = "Cancel"
      except:
         pass
      
   # ==========================================================================
   def __start_scrape(self, book, num_remaining):
      book_name = Path.GetFileName(book.path_s.strip()) if book.path_s else ""
      fileless = book_name == ""
      if fileless:
         book_name = book.series_s if book.series_s else ""
         if not book_name or book_name.startswith("ComicForm"):
            book_name = "<unknown>"
         book_name += (' #' + book.issue_num_s) if book.issue_num_s else ''
         if book.volume_year_n >= 0:
            book_name += ' (Vol. {0})'.format(sstr(book.volume_year_n))
         elif book.pub_year_n >= 0:
            book_name += ' ({0})'.format(sstr(book.pub_year_n))
        
      page_image = book.create_image_of_page(0)
      page_count = book.page_count_n
       
      def delegate():
         if not self.IsDisposed and not self.Disposing:
            self.__current_book = book
            self.__current_page = 0
            self.__current_page_count = page_count
            
            # Explicit key validation fallback barrier
            lbl_scraping = i18n.get("ComicFormScrapingLabel")
            if not lbl_scraping or lbl_scraping.startswith("ComicForm"):
               prefix = "Scraping: "
            else:
               prefix = lbl_scraping
               
            self.__label.Text = prefix + book_name
            self.__pbox_panel.set_image(page_image)
            self.__progbar.PerformStep()
            self.__progbar.Maximum = self.__progbar.Value + num_remaining
            
            lbl_cancel = i18n.get("ComicFormCancelButton")
            if not lbl_cancel or lbl_cancel.startswith("ComicForm"):
               cancel_fmt = "Cancel ({0} remaining)"
            else:
               cancel_fmt = lbl_cancel
               
            self.__cancel_button.Text = cancel_fmt.format(sstr(num_remaining))
            self.Update()
      utils.invoke(self, delegate, False)
 
   #===========================================================================
   @classmethod 
   def show_threadsafe(cls, *args):
      cls.newform = None
      def shower():                                                           
         with cls(*args) as form:
            Monitor.Enter(cls)
            try:
               cls.newform = form
               Monitor.Pulse(cls)
            finally:
               Monitor.Exit(cls)
            def exception_handler(sender, event):
               log.handle_error(event.Exception)  
            Application.ThreadException += ThreadExceptionEventHandler(exception_handler)
            Application.Run(form)
      
      Monitor.Enter(cls)
      try:
         Thread(ThreadStart(shower)).Start()
         Monitor.Wait(cls)
      finally:
         Monitor.Exit(cls)
      newform = cls.newform
      del cls.newform
       
      def activate_form():
         newform.Activate()
      utils.invoke(newform, activate_form, True)
      return newform
   
   # ==========================================================================      
   def close_threadsafe(self):
      if self.__already_closed:
         return
      def delegate():
         self.__cancel_on_close = False
         self.Close()
         self.Dispose()
      try:
         if self.IsDisposed or self.Disposing:
            return
         if not self.IsHandleCreated:
            return
         utils.invoke(self, delegate, False)
      except:
         pass
          
   # ==========================================================================           
   def _can_change_page(self, forward):
      if forward:
         return self.__current_page < self.__current_page_count-1
      else: 
         return self.__current_page > 0
              
   # ==========================================================================           
   def __form_closing_fired(self, sender, args):
      self.__already_closed = True
      
   # ==========================================================================
   def __form_closed_fired(self, sender, args):
      try: self.__scraper.start_scrape_listeners.remove(self.__start_scrape)
      except: pass
      try: self.__scraper.cancel_listeners.remove(self.close_threadsafe)
      except: pass
      
      if self.__cancel_on_close:
         self.__scraper.cancel()
         
      self.__current_book = None
      self.__current_page = 0
      self.__pbox_panel.Dispose(True)
      GC.Collect()
      
   # ==========================================================================
   def __picture_box_clicked(self, sender, args):
      mouse_hovered_state = self.__pbox_panel.get_mouse_hovered_state()
      if self.__current_book and args.Button == MouseButtons.Left and mouse_hovered_state:
         if mouse_hovered_state == 'FL':
            self.__current_page = 0
         elif mouse_hovered_state == 'L':
            self.__current_page -= 1
         elif mouse_hovered_state == 'R':
            self.__current_page += 1
         elif mouse_hovered_state == 'FR':
            self.__current_page = self.__current_page_count-1
            
         self.__current_page = min( self.__current_page_count-1, max(0, self.__current_page) )
         
         page_index = self.__current_page 
         current_book = self.__current_book 
         page_image = [None]
         def get_page():
            page_image[0] = current_book.create_image_of_page(page_index)
            def set_page():
               self.__pbox_panel.set_image(page_image[0]) 
               self.__pbox_panel.Refresh() 
            utils.invoke(self, set_page, False)
         utils.invoke( self.__scraper.comicrack.MainWindow, get_page, False )
      
   # ==========================================================================
   def CenterToParent(self):
      super(ComicForm, self).CenterToParent()
      self.Location = Point(self.Location.X - self.Width, self.Location.Y)

# =============================================================================    
class _PictureBoxPanel(Panel):
   def __init__(self):
      self.__left_arrow = Resources.createArrowIcon(True, False)
      self.__full_left_arrow = Resources.createArrowIcon(True, True)
      self.__right_arrow = Resources.createArrowIcon(False, False)
      self.__full_right_arrow = Resources.createArrowIcon(False, True)
      
      self.__left_bound = 0;
      self.__right_bound = 0;
      self.__hovered_image_atts = None
      self.__normal_image_atts = None
      self.__mouse_hovered_state = None
      self._picbox = None
      
      Panel.__init__(self)
      self.__build_gui()
      
   def __build_gui(self):
      cmap = ColorMap()
      cmap.OldColor = Color.White
      cmap.NewColor = Color.Gainsboro
      self.__normal_image_atts = ImageAttributes()
      self.__normal_image_atts.SetRemapTable( Array[ColorMap]([cmap]) )
      self.__hovered_image_atts = ImageAttributes()
      
      self._picbox = PictureBox()
      self._picbox.SizeMode = PictureBoxSizeMode.StretchImage
      self._picbox.Location = Point(0,0)
      self._picbox.Enabled = False
      self.Controls.Add(self._picbox)
      
      self.Disposed += self.__disposed_fired
      self.Resize += self.__resize_fired
      self.MouseMove += self.__mouse_moved
      self.MouseLeave += self.__mouse_exited
      self._picbox.Paint += PaintEventHandler(self.__pbox_painted)
      self.set_image(None)
 
   def set_image(self, image):
      if not image:
         image = Resources.createComicVineLogo()
      
      self._ratio = 0;
      if image and float(image.Height):
         self._ratio = float(image.Width) / float(image.Height)
      if not self._ratio:
         self._ratio = 1.55
         
      if self._picbox.Image:
         self._picbox.Image.Dispose()
         
      self._picbox.Image = image
      self.OnResize(None)
      
      comicform = self.Parent
      if comicform != None:
         self.Cursor = Cursors.Hand if comicform._can_change_page(True) or \
           comicform._can_change_page(False) else None

   def get_mouse_hovered_state(self):
      return self.__mouse_hovered_state;
   
   def __disposed_fired(self, sender, args):
      if self._picbox.Image:                                               
         self._picbox.Image.Dispose()                                      
      self._picbox.Image = None              
      if self.__left_arrow: self.__left_arrow.Dispose()
      if self.__full_left_arrow: self.__full_left_arrow.Dispose()
      if self.__right_arrow: self.__right_arrow.Dispose()
      if self.__full_right_arrow: self.__full_right_arrow.Dispose()
      
   def __resize_fired(self, sender, args):
      panel_bds = self.Bounds
      a = Rectangle(panel_bds.X, panel_bds.Y, self.Size.Width, self.Size.Width / self._ratio)
      b = Rectangle(panel_bds.X, panel_bds.Y, self.Size.Height * self._ratio, self.Size.Height)
      
      if panel_bds.Contains(a):
         self._picbox.Size = a.Size
         self._picbox.Location = Point( 0, (self.Size.Height-a.Height)/2 )
      else:   
         self._picbox.Size = b.Size
         self._picbox.Location = Point( (self.Size.Width-b.Width)/2, 0 )
      
   def __mouse_moved(self, picbox, args):
      x = args.X - (self.Width - self._picbox.Width)/2
      mouse_hov_left = args.X < self.Width/2
      mouse_hov_full = x < self.__left_bound if mouse_hov_left else x > self.__right_bound
         
      if mouse_hov_left:
         mouse_hovered_state = 'FL' if mouse_hov_full else 'L'
      else:
         mouse_hovered_state = 'FR' if mouse_hov_full else 'R'
         
      if self.__mouse_hovered_state != mouse_hovered_state:
         self.__mouse_hovered_state = mouse_hovered_state
         self.Refresh()
         
   def __mouse_exited(self, picbox, args):
      if self.__mouse_hovered_state:
         self.__mouse_hovered_state = None
         self.Refresh()
      
   def __pbox_painted(self, picbox, args):
      left_arrow = self.__left_arrow
      full_left_arrow = self.__full_left_arrow
      right_arrow = self.__right_arrow
      full_right_arrow = self.__full_right_arrow
      
      if not left_arrow or not right_arrow: return
      
      old_width = float(right_arrow.Width)
      scaled_width = min(picbox.Width*0.15, old_width)
      old_height = float(right_arrow.Height)
      scaled_height = old_height * scaled_width / old_width
       
      y = picbox.Height/2-scaled_height/2
      xoffset = picbox.Width * 0.01
      f_leftx = xoffset
      f_rightx = picbox.Width-xoffset-scaled_width
      
      leftx = f_leftx + scaled_width
      rightx = f_rightx - scaled_width
      
      self.__left_bound = leftx
      self.__right_bound = f_rightx
      
      if self.Parent != None:
         g = args.Graphics
         mouse_hovered = self.__mouse_hovered_state
         can_go_left = self.Parent._can_change_page(False)
         can_go_right = self.Parent._can_change_page(True)
         
         if mouse_hovered and can_go_left:
            image_atts = self.__hovered_image_atts if mouse_hovered == 'FL' else self.__normal_image_atts 
            g.DrawImage(full_left_arrow, Rectangle(f_leftx, y, scaled_width, scaled_height), 0, 0, old_width, old_height, GraphicsUnit.Pixel, image_atts)
               
            image_atts = self.__hovered_image_atts if mouse_hovered == 'L' else self.__normal_image_atts 
            g.DrawImage(left_arrow, Rectangle(leftx, y, scaled_width, scaled_height), 0, 0, old_width, old_height, GraphicsUnit.Pixel, image_atts)
               
         if mouse_hovered and can_go_right:
            image_atts = self.__hovered_image_atts if mouse_hovered == 'R' else self.__normal_image_atts 
            g.DrawImage(right_arrow, Rectangle(rightx, y, scaled_width, scaled_height), 0, 0, old_width, old_height, GraphicsUnit.Pixel, image_atts)
                
            image_atts = self.__hovered_image_atts if mouse_hovered == 'FR' else self.__normal_image_atts 
            g.DrawImage(full_right_arrow, Rectangle(f_rightx, y, scaled_width, scaled_height), 0, 0, old_width, old_height, GraphicsUnit.Pixel, image_atts)
"""
This module contains the GCDForm class, the base class for all plugin forms.

GCDForm provides common functionality including:
- Default window properties (no maximize/minimize buttons, etc.)
- Context manager support (with statement)
- Keyboard shortcuts (Escape to close, Ctrl+Shift+L to save log)
- Factory methods for creating common UI controls

@author: Cory Banack (original), enhanced by Local CV Scraper Team
and further adpated by Strumples and Gemini for Grand Comics DB
"""

import clr
import gcd_log as log

clr.AddReference('System.Windows.Forms')

from System.Windows.Forms import Button, CheckBox, Label, TextBox, \
    FormBorderStyle, Keys, DialogResult
from gcd_persistentform import PersistentForm

clr.AddReference('System.Drawing')
from System.Drawing import Point, Size

#==============================================================================
class GCDForm(PersistentForm):
   """
   Base class for all Local GCD Scraper forms.
   
   This class provides common functionality and default configuration for
   all forms in this application, including:
   - Default window appearance (no maximize/minimize, fixed border, etc.)
   - Support for Python's 'with' statement (context manager)
   - Global keyboard shortcuts
   - Factory methods for creating common UI controls
   """

   #===========================================================================
   def __init__(self, owner, persist_loc_key_s = "", persist_size_key_s = "" ):
      """
      Constructs a new GCDForm.
      
      Args:
         owner: The Form that will own this Form (required)
         persist_loc_key_s: Key for persisting window location (optional)
         persist_size_key_s: Key for persisting window size (optional)
      """
      super(GCDForm, self).__init__( persist_loc_key_s, persist_size_key_s )
      
      # these are the default properties of all GCDForms.
      self.Owner = owner 
      self.Modal = False
      self.MaximizeBox = False                                                
      self.MinimizeBox = False                                                
      self.ShowIcon = False                                                   
      self.ShowInTaskbar = False    
      self.FormBorderStyle = FormBorderStyle.FixedSingle
      
      
   #===========================================================================
   def ShowDialog(self, owner=None):
      """
      Shows the form as a modal dialog.
      
      Overridden to use the pre-set Owner if no owner is specified.
      
      Args:
         owner: Optional owner form. Uses self.Owner if not specified.
         
      Returns:
         DialogResult indicating how the dialog was closed
      """
      if owner:
         return super(GCDForm, self).ShowDialog(owner)
      elif self.Owner:
         return super(GCDForm, self).ShowDialog(self.Owner)
      else:
         return super(GCDForm, self).ShowDialog()         
         
   #===========================================================================
   def __enter__(self):
      """Context manager entry - allows use with 'with' statement."""
      return self
   
   
   #===========================================================================
   def __exit__(self, type, value, traceback): 
      """Context manager exit - ensures form is closed and disposed."""
      # ensure that the form is closed and disposed in a timely manner.
      # this probably isn't strictly necessary, but it doesn't hurt.
      self.Close()
      self.Dispose()


   #===========================================================================
   def ProcessCmdKey(self, msg, keys):
      """
      Handles keyboard shortcuts.
      
      Global shortcuts:
         - Escape: Close the form
         - Ctrl+Shift+L: Save application log to file
      """
      # overidden to allow various "application wide" hotkeys
      if keys == Keys.Escape:
         # ensure that all GCDForms close themselves if you press the escape key. 
         self.Close()
      elif keys == Keys.Control|Keys.Shift|Keys.L:
         # ensure that the use can manually save out an application log
         log.save()
      else:
         super(GCDForm, self).ProcessCmdKey(msg, keys)


   #===========================================================================
   # Helper methods for creating common UI controls
   #===========================================================================
   
   def create_button(self, text, location, size, click_handler=None, 
                     dialog_result=None):
      """
      Factory method for creating standard buttons.
      
      Args:
         text: Button text
         location: Point(x, y) for button location
         size: Size(width, height) for button size
         click_handler: Optional event handler for Click event
         dialog_result: Optional DialogResult to set
         
      Returns:
         Configured Button instance
      """
      button = Button()
      button.Text = text
      button.Location = location
      button.Size = size
      button.UseVisualStyleBackColor = True
      if click_handler:
         button.Click += click_handler
      if dialog_result:
         button.DialogResult = dialog_result
      return button
   
   
   def create_checkbox(self, text, location, checked=False, size=None):
      """
      Factory method for creating standard checkboxes.
      
      Args:
         text: Checkbox label text
         location: Point(x, y) for checkbox location
         checked: Initial checked state
         size: Optional Size(width, height), uses AutoSize if not specified
         
      Returns:
         Configured CheckBox instance
      """
      checkbox = CheckBox()
      checkbox.Text = text
      checkbox.Location = location
      checkbox.Checked = checked
      if size:
         checkbox.Size = size
      else:
         checkbox.AutoSize = True
      return checkbox
   
   
   def create_label(self, text, location, size=None, auto_size=True):
      """
      Factory method for creating standard labels.
      
      Args:
         text: Label text
         location: Point(x, y) for label location
         size: Optional Size(width, height)
         auto_size: Whether to auto-size the label (default True)
         
      Returns:
         Configured Label instance
      """
      label = Label()
      label.Text = text
      label.Location = location
      label.UseMnemonic = False
      label.AutoSize = auto_size
      if size:
         label.Size = size
      return label
   
   
   def create_textbox(self, location, size, text="", multiline=False, 
                      readonly=False):
      """
      Factory method for creating standard textboxes.
      
      Args:
         location: Point(x, y) for textbox location
         size: Size(width, height) for textbox size
         text: Initial text content
         multiline: Whether textbox supports multiple lines
         readonly: Whether textbox is read-only
         
      Returns:
         Configured TextBox instance
      """
      textbox = TextBox()
      textbox.Location = location
      textbox.Size = size
      textbox.Text = text
      textbox.Multiline = multiline
      textbox.ReadOnly = readonly
      return textbox

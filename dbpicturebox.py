#coding: utf-8
'''
This module contains the DBPictureBox class, which can be used to display 
remotely loaded images using an asynchronous off-loading thread.

@author: Cory Banack (original), refactored by Local CV Scraper Team
and further adapted by Strumples & Gemini for Grand Comics DB.
'''

import clr
import gcd_utils as utils
import db
from gcd_resources import Resources
from scheduler import Scheduler

clr.AddReference('System.Drawing')
from System.Drawing import Graphics, Bitmap
from System.Drawing import Rectangle, GraphicsUnit
from System.Drawing.Imaging import ColorMatrix, ImageAttributes

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import PictureBox, PictureBoxSizeMode

#==============================================================================
class DBPictureBox(PictureBox):
   '''
   Asynchronous image canvas renderer control wrapper.
   '''

   #===========================================================================
   def __init__(self): 
      ''' Defines member variables for new instances of this class. '''
      self.__current_image_ref = None
      self.__scheduler = Scheduler()
      self.__image_cache = {}
      
      from System.IO import MemoryStream
      try:
         logo_resource = Resources.createGCDLogo()
         if hasattr(logo_resource, "Width"):
            self.__unknown_image = logo_resource
         else:
            self.__unknown_image = Bitmap(MemoryStream(logo_resource))
      except:
         self.__unknown_image = Bitmap(100, 150)
      
      self.__loading_image = self.__copy_transparent(self.__unknown_image)
      self.__freed = False
      self._initialize()

   #===========================================================================
   def _initialize(self):
      ''' Initial configuration for new instances of this class '''
      PictureBox.__init__(self)      
      def visibility_changed(sender, args):
         if self.Visible: self.__update_image()
         
      self.VisibleChanged += visibility_changed
      self.SizeMode = PictureBoxSizeMode.StretchImage
      self.set_image_ref(None)

   #===========================================================================
   def free(self):
      ''' Explicitly frees all resources held by this object. '''
      self.__freed = True
      self.__scheduler.shutdown(False)
      self.__unknown_image.Dispose()
      self.__loading_image.Dispose()
      for image in self.__image_cache.values():
         image.Dispose()
      self.__image_cache = {}
      PictureBox.Dispose(self, True)

   #===========================================================================
   def set_image_ref(self, ref):
      ''' Sets the active visual image reference pointer tracking key. '''
      self.__current_image_ref = ref
      if self.Visible:
         self.__update_image()
     
   #===========================================================================
   def __copy_transparent(self, image):
      ''' Creates a semi-transparent copy of the given image ''' 
      b = Bitmap(image.Width, image.Height)
      g = Graphics.FromImage(b)
      cm = ColorMatrix()
      cm.Matrix33 = 0.3
      ia = ImageAttributes()
      ia.SetColorMatrix(cm)
      g.DrawImage(image, Rectangle(0,0, image.Width, image.Height), 0,0,\
         image.Width, image.Height, GraphicsUnit.Pixel, ia)
      g.Dispose()
      ia.Dispose()
      return b

   #===========================================================================
   def __update_image(self):
      ''' Update the currently displayed image on this picturebox asynchronously. '''
      def switchimage(image):
         if image: self.Image = image
         else: self.Image = self.__unknown_image
             
      ref = self.__current_image_ref
      
      if not ref and ref != 0:
         switchimage(None)
      elif ref in self.__image_cache:
         switchimage(self.__image_cache[ref])
      else:
         self.Image = self.__loading_image
         def download_task():
            new_image = db.query_image(ref)
               
            def update_image():
               if self.__freed:
                  if new_image: new_image.Dispose()
                  return
               
               if ref in self.__image_cache:
                  old_image = self.__image_cache[ref]
                  del self.__image_cache[ref]
                  if old_image: old_image.Dispose()
               
               if new_image:
                  self.__image_cache[ref] = new_image
               
               if ref == self.__current_image_ref:
                  switchimage(new_image)
                  
            utils.invoke(self, update_image, False) 
         self.__scheduler.submit(download_task)
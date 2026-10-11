#coding: utf-8
''' ===========================================================================

This module is the entry point into the 'Local Grand Comics DB Scraper' add-on for 
ComicRack.  It conforms to ComicRack add-on specifications, outlined at:

     https://github.com/maforget/ComicRackCE

=========================================================================== '''
import sys
import clr
import re

# 1. IMMEDIATE ENVIRONMENT BOOTSTRAP: Bind directory path rules before importing modules
try:
    clr.AddReference('System')
    from System.IO import Directory, Path as SysPath
    from System import Environment
    
    script_dir = ""
    try:
        script_dir = SysPath.GetDirectoryName(__file__)
    except:
        pass
        
    if not script_dir or not Directory.Exists(script_dir):
        script_dir = Directory.GetCurrentDirectory()
        if "Program Files" in script_dir:
            appdata = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData)
            script_dir = SysPath.Combine(appdata, r"cYo\ComicRack Community Edition\Scripts\GCD Local Scraper")
    
    if Directory.Exists(script_dir) and script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        
    internal_lib = SysPath.Combine(script_dir, 'Lib')
    if Directory.Exists(internal_lib) and internal_lib not in sys.path:
        sys.path.insert(0, internal_lib)
except:
    pass

# 2. SAFE EXPLICIT IMPORTS: Now that paths are guaranteed, global assignments resolve perfectly
import gcd_log as log
import gcd_i18n as i18n
from gcd_resources import Resources
from gcd_configform import ConfigForm

# ===========================================================================
#@Image        localscraper.png
#@Key          local-gcd-scraper-v2
#@Hook         Books, Editor
# ===========================================================================
def gcd_scrape(books):
    ''' The primary batch orchestration routine hook for ComicRack. '''
    def delegate():
        if books:
            from scrapeengine import ScrapeEngine
            try:
                Resources.initialize()
                log.install()
                i18n.install(ComicRack)
                engine = ScrapeEngine(ComicRack)
                engine.scrape(books)
            except Exception as ex:
                log.handle_error(ex)
            finally:
                i18n.uninstall()
                log.uninstall()
    __launch(delegate)


# ===========================================================================
#@Key          local-gcd-scraper-v2
#@Hook         ConfigScript
# ===========================================================================
def gcd_config():
    ''' The primary user preference configuration UI routine hook. '''
    def delegate():
        try:
            Resources.initialize()
            log.install()
            i18n.install(ComicRack)
            
            form = ConfigForm(ComicRack.MainWindow)
            form.show_form()
        except Exception as ex:
            log.handle_error(ex)
        finally:
            i18n.uninstall()
            log.uninstall()
    __launch(delegate)


def __launch(delegate_function):
    ''' Runs the delegate logic inside checked framework boundaries. '''
    if __validate_environment():
        delegate_function()


def __validate_environment():
    ''' Checks to see if the current execution workspace environment is valid. '''
    REQUIRED_MAJOR = 0
    REQUIRED_MINOR = 9
    REQUIRED_BUILD = 165
    
    valid_environment = True
    try:
        clr.AddReference('System.Windows.Forms')
        from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
        
        version = re.split(r'\.', ComicRack.App.ProductVersion) 
        major, minor, build = int(version[0]), int(version[1]), int(version[2])
        vhash_current = float(str(major * 5000 + minor) + "." + str(build))
        vhash_required = float(str(REQUIRED_MAJOR * 5000 + REQUIRED_MINOR) + "." + str(REQUIRED_BUILD))
        
        valid_environment = vhash_current >= vhash_required
            
        if not valid_environment:
            MessageBox.Show(ComicRack.MainWindow, "This script requires ComicRack Community Edition 0.9.165 or higher.",
                "Script Version Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning)
    except:
        valid_environment = False
        
    return valid_environment

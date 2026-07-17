'''
This module handles internationalization for the plugin.
Bypassed zip archive dependencies to prevent null path lookup crashes,
providing direct string dictionary mapping for all configuration UI forms.
'''
import gcd_log as log

def get(key):
    """Fallback text mapper dictionary supplying clean English values for all interface elements."""
    strings = {
        # Dialog & Tab Titles
        "ConfigFormTitle": "Local GCD Scraper Preferences",
        "ConfigFormGCDTab": "Database Setup",
        "ConfigFormDetailsTab": "Metadata Fields",
        "ConfigFormBehaviourTab": "Scraper Behavior",
        "ConfigFormDataTab": "Overwrite Rules",
        "ConfigFormAdvancedTab": "Advanced Settings",
        
        # Metadata Checkbox List Fields
        "ConfigFormSeriesCB": "Series Name",
        "ConfigFormVolumeCB": "Volume Year",
        "ConfigFormNumberCB": "Issue Number",
        "ConfigFormTitleCB": "Issue Title",
        "ConfigFormPublishedCB": "Published Date",
        "ConfigFormReleasedCB": "Released Date",
        "ConfigFormCrossoversCB": "Alternate Series (Crossovers)",
        "ConfigFormPublisherCB": "Publisher",
        "ConfigFormImprintCB": "Imprint",
        "ConfigFormWriterCB": "Writers",
        "ConfigFormPencillerCB": "Pencillers",
        "ConfigFormInkerCB": "Inkers",
        "ConfigFormColoristCB": "Colorists",
        "ConfigFormLettererCB": "Letterers",
        "ConfigFormCoverCB": "Cover Artists",
        "ConfigFormEditorCB": "Editors",
        "ConfigFormSummaryCB": "Story Synopsis / Summary",
        "ConfigFormCharactersCB": "Characters",
        "ConfigFormTeamsCB": "Teams",
        "ConfigFormLocationsCB": "Locations",
        "ConfigFormWebCB": "Webpage URL",
        
        # Form Descriptive Explanations
        "ConfigFormDetailsText": "Select the metadata fields to extract from the local database:",
        "ConfigFormFirstScrapeLabel": "When scraping for the first time:",
        "ConfigFormAdvancedText": "Enter advanced script variable parameters (JSON format):",
        
        # Behavior & Logic Options
        "ConfigFormAutochooseSeriesCB": "Auto-choose series if only one match is found",
        "ConfigFormConfirmIssueCB": "Always prompt to confirm the specific issue number",
        "ConfigFormRescrapeCB": "Enable fast re-scraping using embedded database identifiers",
        "ConfigFormRescrapeNotesCB": "Write database identifier hints into book Notes",
        "ConfigFormRescrapeTagsCB": "Write database identifier hints into book Tags",
        "ConfigFormShowSummaryCB": "Show data preview verification dialog before saving changes",
        "ConfigFormImprintsCB": "Automatically map comic imprint names to main publisher fields",
        "ConfigFormOverwriteCB": "Allow existing metadata fields to be overwritten with new data",
        "ConfigFormOverwriteEmptyCB": "Only overwrite field data if the new value is not blank",
        "ConfigFormFilelessCB": "Download issue cover thumbnails for fileless/virtual entries",
        "ConfigFormFilelessOverwriteCB": "Allow downloading thumbnails to replace existing cover artwork",
        
        # System Control Buttons
        "ConfigFormDetailsAll": "Select All",
        "ConfigFormDetailsNone": "Clear All",
        "ConfigFormOK": "Save Settings",
        "ConfigFormCancel": "Cancel",
        "ConfigFormRestore": "Reset to Defaults",
        
        # Context Menus
        "TextCut": "Cut",
        "TextCopy": "Copy",
        "TextPaste": "Paste"
    }
    return strings.get(key, str(key))

def install(comicrack):
    """Bypasses zip translation parser loops completely."""
    pass

def uninstall():
    """Bypasses teardown routines safely."""
    pass
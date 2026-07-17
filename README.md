# Local Grand Comics Database Scraper for ComicRack

An offline, open-source metadata scraper plugin for **ComicRack** that reads comic book information directly from a local Grand Comics Database (GCD) SQLite database file. It also includes an optional integration with the official ComicVine API to pull high-quality cover thumbnails directly into your selection menus.

## 🚀 Features

*   **100% Offline Metadata:** Queries a local `.db` file for lightning-fast lookups without hitting external server rate limits.
*   **Smart Automatching:** Automatically matches and logs series using a built-in confidence scoring matrix.
*   **Fuzzy Search Fallback:** Includes a "Search Again" feature to manually refine search keywords directly from the interface.
*   **Hybrid Cover Fetcher:** Looks for local cover files first, then securely falls back to the official ComicVine API to render cover art previews inside the GUI selector windows.
*   **Unicode-Safe Batch Scraping:** Built to handle thousands of comics simultaneously without freezing on international or accented characters (e.g., characters like *José* or *René*).

---

## 🛠️ Installation

1.  Go to the **Releases** section on the right side of this GitHub page.
2.  Download the latest `LocalGrandComicsScraper.crplugin` file.
3.  Double-click the downloaded `.crplugin` file. ComicRack will automatically install it as an extension.
4.  Completely restart ComicRack to ensure all script paths initialize correctly.

---

## ⚙️ Configuration & Database Setup

Before running your first scrape, you need to point the plugin to your offline Grand Comics Database file:

1.  In ComicRack, open the plugin configuration window (typically found via `Preferences` or right-clicking your book list -> `Scripts` -> `Local GCD Scraper Preferences`).
2.  On the **Database** tab, click the `...` button next to the **Local Grand Comics Database File Path** field.
3.  Select your local `.db` file.
4.  **(Optional) Cover Previews:** In the **ComicVine Developer API Key** field, enter your personal 40-character ComicVine API key. 
    > **Note:** This API key is *only* needed to download and display cover artwork thumbnails inside the manual GUI choice windows. It is not required for standard textual metadata indexing.
5.  Click **OK** to save your settings.

---

## 📖 How to Use

### Batch Scraping
Select one or more comic books in your ComicRack library, right-click, navigate to **Scripts**, and choose **Local GCD Scraper**. The plugin will begin automatically processing your library.

### Refining Search Results ("Search Again")
If the engine finds multiple series matches or fails to identify a niche title automatically, a selector menu will appear. If you need to refine the keywords:
1. Click the **Search Again** button.
2. Enter your modified keywords in the text field prompt and press **Search**.
3. The grid will instantly update with fresh results pulled straight from your local database without skipping the book.

---

## 📄 Open Source License

This project is open-source and released under the terms of the **MIT License**. You are completely free to copy, modify, distribute, and use the software for personal or development purposes. The software is provided "as-is" without warranty of any kind.

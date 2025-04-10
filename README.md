
# BwE Discord JSON Chat Parser

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)

A powerful and user-friendly Python application for forensically parsing and converting Discord JSON chat exports into readable, well-formatted HTML transcripts. Supports normal chats, direct messages (DMs), and search result exports.

---

## 🔧 Features

- Converts Discord JSON exports into clean HTML transcripts
- Supports:
  - Regular chat logs
  - Direct Messages (DMs)
  - Search result exports
- Handles attachments, embeds, mentions, and edited messages
- Configurable display settings
- Extracts participants and channel IDs
- Generates summary statistics
- Optional search across generated HTML transcripts

---

## 🧰 Requirements

- Python 3.12.0
- Required Python packages:
  - `colorama`

Install via pip:
```bash
pip install colorama
```

---

## 📁 Usage

1. Extract your entire cache using ![Nirsoft's ChromeCacheView](https://www.nirsoft.net/utils/chrome_cache_view.html) app
2. Place all your exported files in the same directory as the script.
3. Run the script:
```bash
python bwe_discord_json_parser.py
```
4. If an `Output/` folder already exists, you'll be prompted to:
   - **(R)** Rescan and regenerate all output files
   - **(S)** Search within existing HTML files
5. Transcripts will be saved in the `Output/` folder as `.html` files.
6. A `stats.txt` summary will also be created with useful information such as:
   - Total files processed
   - Types of files
   - Unique channel IDs
   - All unique participants

---

## ⚙️ Settings

Modify the `SETTINGS` dictionary at the top of the script to change behavior:

```python
SETTINGS = {
    "display_mode": 1,         # 1 = username, 2 = username/global_name, 3 = username/global_name/id
    "embed_images": False,     # If True, show attachments as links. If False, embed them as <img>
    "use_full_timestamp": False, # If True, use ISO timestamp. If False, show human-readable format
    "order_ascending": True    # If True, sort oldest to newest. If False, keep default order
}
```

---

## 🧪 File Types Supported

- **Chat JSONs**: Usually single channels
- **DM JSONs**: Direct messages (including multi-participant)
- **Search Results**: Discord's `search.json` exports
- Auto-detection based on JSON structure

---

## 📊 Output Example

- HTML Transcript:
  - Includes original source filename, channel ID's, timestamps, author names, content, mentions, attachments, and embeds.
- `stats.txt`:
  - Summary of participants, channel IDs, and file types.

---

## 🔍 Search Feature

After processing, you can choose to search all generated `.html` files for a keyword or phrase. Helpful for quickly locating discussions in large exports.

---

## 😶 Limitations

The cache may not be entirely up to date and because of this links for attachments and embeds may have a different hash in the URL and will thus expire. If you're able to use the Discord app itself the image/attachment is likely still alive and working in the original chat location. If possible grab the cache again at a later date as that might grab the newer url with the latest hash.

---

## 🖼️ Screenshot

![1](https://i.imgur.com/mmPSSAT.png)
![Chat](https://i.imgur.com/qgY607S.jpeg)

---

## 🔮 Future Features?

I may add the ability to download all of the attached and embedded images and host them locally (whilst retaining the original URL) given the hashes can change arbitrarily and cause images to disappear later on. 

---

## ⚠️ License and Attribution

This project is licensed under the [MIT License](LICENSE).

If you use or modify this project, **you must retain the original license notice and attribution** in your source code and any distributions.

Attribution Example:
- Based on work by [BetterWayElectronics](https://github.com/betterwayelectronics)

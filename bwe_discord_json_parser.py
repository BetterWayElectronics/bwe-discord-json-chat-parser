import os
import json
import shutil
import ctypes
from colorama import init, Fore, Style, Back
from datetime import datetime

# ----------------- SETTINGS -----------------
# Adjust these options as desired:
# display_mode: 
#   1 = username only,
#   2 = username/global name,
#   3 = username/global name/id.
# embed_images:
#   True = show attachments as clickable links,
#   False = embed the image directly.
# use_full_timestamp:
#   True = display the full ISO timestamp,
#   False = display a formatted version.
# order_ascending:
#   True = display from oldest to newest,
#   False = display as-is (typically newest first)
SETTINGS = {
    "display_mode": 1,
    "embed_images": False,
    "use_full_timestamp": False,
    "order_ascending": True
}
# --------------------------------------------

def sanitize_filename(name):
    """Remove or replace characters that are not allowed in filenames."""
    forbidden = r'\/:*?"<>|'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name

def format_user(author):
    """Return a string for a user based on SETTINGS['display_mode']."""
    if not author:
        return "Unknown"
    mode = SETTINGS.get("display_mode", 2)
    username = author.get("username", "Unknown")
    global_name = author.get("global_name", "")
    user_id = author.get("id", "")
    if mode == 1:
        return username
    elif mode == 2:
        return f"{username}/{global_name}" if global_name else username
    elif mode == 3:
        return f"{username}/{global_name}/{user_id}" if global_name else f"{username}/{user_id}"
    else:
        return username

def format_timestamp(ts):
    """Convert an ISO timestamp string to a formatted date/time string."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts

def format_message(msg):
    """Format a single message into an HTML snippet."""
    ts_raw = msg.get("timestamp", "")
    ts = ts_raw if SETTINGS.get("use_full_timestamp") else format_timestamp(ts_raw)
    # Check for edited time.
    edited_raw = msg.get("edited_timestamp")
    edited_str = ""
    if edited_raw:
        edited_str = edited_raw if SETTINGS.get("use_full_timestamp") else format_timestamp(edited_raw)
        edited_str = f" (edited: {edited_str})"
    sender = format_user(msg.get("author"))
    content = msg.get("content", "")
    # Process mentions using the same display mode.
    mentions = msg.get("mentions", [])
    mention_str = ""
    if mentions:
        mention_names = ", ".join([format_user(m) for m in mentions])
        mention_str = f"<br><em>Mentions:</em> {mention_names}"
    # Process attachments.
    attachments = msg.get("attachments", [])
    att_str = ""
    if attachments:
        att_str = "<br><em>Attachments:</em> " + "<br>".join([
            (
                f'<img src="{att.get("url", "#")}" alt="{att.get("filename", "attachment")}" style="max-width:500px;"><br>'
                f'<a href="{att.get("url", "#")}">{att.get("filename", "attachment")}</a>'
                if not SETTINGS.get("embed_images") else
                f'<a href="{att.get("url", "#")}">{att.get("filename", "attachment")}</a>'
            )
            for att in attachments
        ])

    # Process embeds.
    embeds = msg.get("embeds", [])
    embed_str = ""
    if embeds:
        embed_items = []
        for embed in embeds:
            url = embed.get("url") or embed.get("thumbnail", {}).get("url") or embed.get("image", {}).get("url")
            if embed.get("image") and embed["image"].get("url"):
                img_url = embed["image"]["url"]
                embed_items.append(
                    f'<img src="{img_url}" alt="embed image" style="max-width:500px;"><br>'
                    f'<a href="{img_url}">{img_url}</a>'
                )
            elif embed.get("thumbnail") and embed["thumbnail"].get("url"):
                thumb_url = embed["thumbnail"]["url"]
                embed_items.append(
                    f'<img src="{thumb_url}" alt="embed thumbnail" style="max-width:500px;"><br>'
                    f'<a href="{thumb_url}">{thumb_url}</a>'
                )
            elif embed.get("title") and embed.get("url"):
                embed_items.append(
                    f'<a href="{embed["url"]}">{embed["title"]}</a>'
                )
            elif url:
                embed_items.append(
                    f'<a href="{url}">{url}</a>'
                )
        if embed_items:
            embed_str = "<br><em>Embeds:</em> " + "<br>".join(embed_items)


    html = (
        f'<div class="message"><span class="timestamp">[{ts}]{edited_str}</span> '
        f'<strong>{sender}</strong>: {content}{mention_str}{att_str}{embed_str}</div><hr>\n'
    )
    return html

def process_normal_chat(data):
    """Process a chat export (a list of messages)."""
    html = ""
    if data and isinstance(data, list) and isinstance(data[0], dict) and "channel_id" in data[0]:
        channel_id = data[0].get("channel_id", "N/A")
        html += f"<p><strong>Channel ID:</strong> {channel_id}</p>\n"
    html += "<h2>Chat Transcript</h2>\n"
    messages = list(reversed(data)) if SETTINGS.get("order_ascending") else data
    for msg in messages:
        html += format_message(msg)
    return html

def process_dm(data):
    """
    Process a DM export.
    The DM export might be a dict (with 'channels' and 'messages')
    or it might be a list (classified as DM because it has exactly 2 participants).
    """
    html = ""
    order_asc = SETTINGS.get("order_ascending", True)
    if isinstance(data, dict):
        messages = data.get("messages", [])
        for group in (list(reversed(messages)) if order_asc else messages):
            if group and isinstance(group, list) and isinstance(group[0], dict) and "channel_id" in group[0]:
                channel_id = group[0].get("channel_id", "N/A")
                html += f"<p><strong>Channel ID:</strong> {channel_id}</p>\n"
                break
        html += "<h2>Direct Message Transcript</h2>\n"
        for group in (list(reversed(messages)) if order_asc else messages):
            if isinstance(group, list):
                for msg in group:
                    html += format_message(msg)
        # Also check for recipients in the dict if "channels" is missing or empty.
        if not data.get("channels"):
            recipients = data.get("recipients", [])
            if recipients:
                rec_names = ", ".join([format_user(rec) for rec in recipients])
                html = f"<p><strong>Recipients:</strong> {rec_names}</p>\n" + html
    elif isinstance(data, list):
        if data and isinstance(data[0], dict) and "channel_id" in data[0]:
            channel_id = data[0].get("channel_id", "N/A")
            html += f"<p><strong>Channel ID:</strong> {channel_id}</p>\n"
        html += "<h2>Direct Message Transcript</h2>\n"
        messages = list(reversed(data)) if order_asc else data
        for msg in messages:
            html += format_message(msg)
    return html

def process_search(data, filename):
    """Process a search export (dict with 'total_results', 'channels', and 'messages').
       The search term is taken as the original filename (without extension).
    """
    total = data.get("total_results", "N/A")
    base = os.path.splitext(os.path.basename(filename))[0]
    search_term = base
    html = f"<h2>Search Results - '{search_term}'</h2>\n"
    html += f"<p><strong>Total Results:</strong> {total}</p>\n"
    messages = data.get("messages", [])
    order_asc = SETTINGS.get("order_ascending", True)
    for group in (list(reversed(messages)) if order_asc else messages):
        if group and isinstance(group, list) and isinstance(group[0], dict) and "channel_id" in group[0]:
            channel_id = group[0].get("channel_id", "N/A")
            html += f"<p><strong>Channel ID:</strong> {channel_id}</p>\n"
            break
    for group in (list(reversed(messages)) if order_asc else messages):
        if isinstance(group, list):
            for msg in group:
                html += format_message(msg)
    return html

def detect_file_type(data):
    """
    Detect file type based on JSON structure.
      - If data is a list and its first element is a dict with "timestamp" and "author", then:
           if there are exactly two distinct participants (by username), classify as "dm".
           Otherwise, classify as "chat".
      - If data is a dict and has "total_results" and "messages", return "search".
      - If data is a dict and has "channels" and "messages", return "dm".
      - Otherwise return "unknown".
    """
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "timestamp" in data[0] and "author" in data[0]:
            participants = set()
            for msg in data:
                if isinstance(msg, dict) and "author" in msg:
                    participants.add(msg["author"].get("username", "Unknown"))
            if len(participants) == 2:
                return "dm"
            return "chat"
        else:
            return "unknown"
    elif isinstance(data, dict):
        if "total_results" in data and "messages" in data:
            return "search"
        elif "channels" in data and "messages" in data:
            return "dm"
    return "unknown"

def extract_participants(data, file_type):
    """
    Extract distinct participant names (using format_user) from messages (and channels for DM).
    For DM files, also try a top-level "recipients" if available.
    """
    participants = set()
    if file_type == "chat":
        for msg in data:
            if isinstance(msg, dict):
                participants.add(format_user(msg.get("author")))
    elif file_type in ("dm", "search"):
        if isinstance(data, dict):
            messages = data.get("messages", [])
            for group in messages:
                if isinstance(group, list):
                    for msg in group:
                        if isinstance(msg, dict):
                            participants.add(format_user(msg.get("author")))
            channels = data.get("channels", [])
            for channel in channels:
                recipients = channel.get("recipients", [])
                for rec in recipients:
                    participants.add(format_user(rec))
            if "recipients" in data:
                for rec in data["recipients"]:
                    participants.add(format_user(rec))
        else:
            for group in data:
                if isinstance(group, dict):
                    participants.add(format_user(group.get("author")))
    return sorted(participants)

def extract_channel_ids(data, file_type):
    """
    Extract a set of unique channel IDs from the data.
    """
    channels = set()
    if file_type == "chat":
        for msg in data:
            if isinstance(msg, dict) and "channel_id" in msg:
                channels.add(msg["channel_id"])
    elif file_type in ("dm", "search"):
        if isinstance(data, dict):
            msg_groups = data.get("messages", [])
            for group in msg_groups:
                if isinstance(group, list):
                    for msg in group:
                        if isinstance(msg, dict) and "channel_id" in msg:
                            channels.add(msg["channel_id"])
            for channel in data.get("channels", []):
                if "id" in channel:
                    channels.add(channel["id"])
        else:
            for msg in data:
                if isinstance(msg, dict) and "channel_id" in msg:
                    channels.add(msg["channel_id"])
    return channels

def generate_html_document(body_content, title):
    """Wrap the body_content with basic HTML document structure."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 20px; }}
      .message {{ margin-bottom: 10px; }}
      .timestamp {{ color: gray; font-size: 0.9em; }}
      hr {{ border: 0; border-top: 1px solid #ccc; }}
    </style>
</head>
<body>
<h1>{title}</h1>
{body_content}
</body>
</html>
"""
    return html

def process_json_file(filepath):
    """Load a JSON file, detect its type, and return (file_type, HTML transcript, data)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error Loading {filepath}: {e}")
        return None, None, None

    file_type = detect_file_type(data)
    transcript = ""
    if file_type == "chat":
        transcript = process_normal_chat(data)
        header = f"Chat Transcript ({os.path.basename(filepath)})"
    elif file_type == "dm":
        transcript = process_dm(data)
        header = f"Direct Message Transcript ({os.path.basename(filepath)})"
    elif file_type == "search":
        transcript = process_search(data, filepath)
        header = f"Search Results Transcript ({os.path.basename(filepath)})"
    else:
        return file_type, None, None

    full_html = generate_html_document(transcript, header)
    return file_type, full_html, data

def search_output(search_term, output_folder):
    """Search for the given term in all .html files in the output folder and return a list of matching files."""
    matching_files = []
    for root, dirs, files in os.walk(output_folder):
        for file in files:
            if file.lower().endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if search_term.lower() in content.lower():
                            matching_files.append(file)
                except Exception as e:
                    print(f"Error Reading {file_path}: {e}")
    return matching_files
    

    
def main():
    def set_window_title(title):
        # Encode the title to ANSI
        title_ansi = title.encode('ansi', 'ignore')
        ctypes.windll.kernel32.SetConsoleTitleA(title_ansi)

    set_window_title('BwE Discord Chat JSON Parser')
    
    version = "1.0.0"

    def print_banner():
        print(Fore.BLACK + Back.CYAN + "*-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-*")
        print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + "            __________          __________               " + Fore.BLACK + Back.CYAN + "|")
        print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + "            \\______   \\ __  _  _\\_   ____/               " + Fore.BLACK + Back.CYAN + "|")
        print(Fore.BLACK + Back.CYAN + ":" + Fore.WHITE + Back.BLACK + "             |    |  _//  \\/ \\/  /|   __)_               " + Fore.BLACK + Back.CYAN + ":")
        print(Fore.BLACK + Back.CYAN + "." + Fore.WHITE + Back.BLACK + "             |    |   \\\\        //        \\              " + Fore.BLACK + Back.CYAN + ".")
        print(Fore.BLACK + Back.CYAN + ":" + Fore.WHITE + Back.BLACK + "  /\\_/\\      |______  / \\__/\\__//_______  /              " + Fore.BLACK + Back.CYAN + ":")
        print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + " ( x.x )            \\/" + Fore.CYAN + " JSON Chat Parser " + Fore.WHITE + "\\/" + version + "          " + Fore.BLACK + Back.CYAN + "|")
        print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + " (>   <)                                                 " + Fore.BLACK + Back.CYAN + "|")
        print(Fore.BLACK + Back.CYAN + "*-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-*" + Back.BLACK + Style.RESET_ALL + "\n")

    print_banner()

    output_folder = "Output"
    # If output folder exists and contains .html files, ask user whether to start over or search.
    if os.path.exists(output_folder):
        html_files = [f for f in os.listdir(output_folder) if f.lower().endswith('.html')]
        if html_files:
            choice = input(Fore.YELLOW + f"Output Folder '{output_folder}' Already Exists And Contains {len(html_files)} HTML File(s).\n" + Style.RESET_ALL +
                           "\nDo You Want To (R)escan (Delete Output Folder And Process JSON Files) Or (S)earch The Output Folder? [R/S]: ").strip().lower()
            if choice == "s":
                search_term = input("\nEnter Search Term: ").strip()
                results = search_output(search_term, output_folder)
                if results:
                    print("\nSearch Term Found In The Following File(s):")
                    for r in results:
                        print(f"- {r}")
                    input("\nPress Enter To Quit...")
                    os._exit(0)
                else:
                    print("No Matches Found In Output Folder.")
                    input("\nPress Enter To Quit...")
                    os._exit(0)
                return
            elif choice == "r":
                # Delete the output folder and its contents.
                shutil.rmtree(output_folder)
                os.makedirs(output_folder)
                print("")
            else:
                input("\nPress Enter To Quit...")
                os._exit(0)

    json_files = [f for f in os.listdir('.') if f.lower().endswith('.json')]
    if not json_files:
        print(Fore.RED + "No JSON Files Found In The Current Directory." + Style.RESET_ALL)
        input("\nPress Enter To Quit...")
        os._exit(0)

    # Statistics variables
    total_files_processed = 0
    file_type_counts = {"chat": 0, "dm": 0, "search": 0}
    global_channel_ids = set()
    global_participants = set()

    # Dictionary to count output files per base name (for naming HTML files)
    base_counts = {}

    for filename in json_files:
        filepath = os.path.join('.', filename)
        file_type, html_content, data = process_json_file(filepath)
        if file_type == "unknown" or html_content is None:
            print(f"Skipping {filename} As Unknown Content Type.")
            continue

        total_files_processed += 1
        file_type_counts[file_type] += 1

        # Extract channel IDs from this file and add to the global set.
        ch_ids = extract_channel_ids(data, file_type)
        global_channel_ids.update(ch_ids)

        # For chat/dm files, derive base name from participants and update global_participants with all participants.
        if file_type in ("chat", "dm"):
            participants = extract_participants(data, file_type)
            global_participants.update(participants)
            if len(participants) == 0:
                base_name = file_type
            elif len(participants) == 1:
                base_name = f"{file_type}_{participants[0]}"
            elif len(participants) == 2:
                base_name = f"{file_type}_{participants[0]}_{participants[1]}"
            else:
                base_name = f"{file_type}_multi"
        elif file_type == "search":
            base_name = f"search_{os.path.splitext(filename)[0]}"
        else:
            base_name = file_type

        base_name = sanitize_filename(base_name)
        count = base_counts.get(base_name, 0) + 1
        base_counts[base_name] = count
        out_name = f"{base_name}.html" if count == 1 else f"{base_name}_{count}.html"
        out_path = os.path.join(output_folder, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(Fore.GREEN + f"Processed {filename} As {file_type.upper()} And Wrote Transcript To {out_path}" + Style.RESET_ALL)

    # Prepare statistics output.
    stats_lines = []
    stats_lines.append(Fore.CYAN + "=== Statistics ===" + Style.RESET_ALL)
    stats_lines.append(f"Total Files Processed: {total_files_processed}")
    stats_lines.append(f"Chat Files: {file_type_counts.get('chat', 0)}")
    stats_lines.append(f"DM Files: {file_type_counts.get('dm', 0)}")
    stats_lines.append(f"Search Files: {file_type_counts.get('search', 0)}")
    stats_lines.append("")
    stats_lines.append(Fore.CYAN + "Unique Channel IDs:" + Style.RESET_ALL)
    if global_channel_ids:
        stats_lines.extend(sorted(global_channel_ids))
    else:
        stats_lines.append("None")
    stats_lines.append("")
    stats_lines.append(Fore.CYAN + "Chat Participants From All Chat And DM Files:" + Style.RESET_ALL)
    if global_participants:
        stats_lines.extend(sorted(global_participants))
    else:
        stats_lines.append("None")
    stats_text = "\n".join(stats_lines)

    # Output statistics to console.
    print("\n" + stats_text)
    # Also write statistics to stats.txt inside the output folder.
    stats_path = os.path.join(output_folder, "stats.txt")
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(stats_text)
    print(Fore.GREEN + f"\nStatistics written to {stats_path}" + Style.RESET_ALL)

    # Prompt user to search the output folder.
    while True:
        search_choice = input("\nDo You Want To Search The Output Folder For A Term? (Y/N): ").strip().lower()
        if search_choice == "y":
            search_term = input("\nEnter Search Term: ").strip()
            results = search_output(search_term, output_folder)
            if results:
                print("\nSearch Term Found In The Following File(s):")
                for r in results:
                    print(f"- {r}")
                input("\nPress Enter To Quit...")
                os._exit(0)
            else:
                print("No Matches Found In Output Folder.")
        elif search_choice == "n":
            break
        else:
            print("Please Enter Y Or N.")

    input("\nPress Enter To Quit...")
    os._exit(0)

if __name__ == "__main__":
    main()

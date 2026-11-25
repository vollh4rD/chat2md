# chat2md

Turn a public **ChatGPT**, **Grok**, **Gemini** or **Claude** share link into a clean Markdown file.

No login, no browser automation, no dependencies: just Python 3 and the share link.

## Usage

```bash
python3 chat2md.py "https://grok.com/share/..." "https://chatgpt.com/share/..." "https://share.gemini.google/..." -o chats/
```

- Put each URL in quotes.
- `-o` sets the output folder (default: the current directory).
- Each chat is saved as `<Chat-Title>.md`, with `## User` / `## ChatGPT` / `## Grok` / `## Gemini` / `## Claude` sections in order.

## Supported links

| Service | URL format |
|---|---|
| ChatGPT | `https://chatgpt.com/share/<id>` (also `chat.openai.com/share/<id>`) |
| Grok | `https://grok.com/share/<id>` or `https://grok.com/share/<slug>_<id>` |
| Gemini | `https://gemini.google.com/share/<id>`, `https://share.gemini.google/<id>` or `https://g.co/gemini/share/<id>` |

To get a link, open the chat, click **Share**, and copy the link.

## Claude (one extra step)

Claude's share data is behind a Cloudflare bot check, so the script can't download it itself. Your browser can:

1. Run the script with the Claude link to get the exact data URL:
   ```bash
   python3 chat2md.py "https://claude.ai/share/<id>"
   ```
   It prints a link like `https://claude.ai/api/chat_snapshots/<id>?rendering_mode=messages&render_all_tools=true`.
2. Open that link in your normal browser and save the page (Cmd/Ctrl+S) as a `.json` file.
3. Convert the saved file:
   ```bash
   python3 chat2md.py path/to/file.json -o chats/
   ```

Artifacts are included as code blocks; attachments appear as `*[attachment: name]*`.

## How it works

- **Grok:** reads the conversation as JSON from Grok's public share endpoint (`/rest/app-chat/share_links/<id>`).
- **Gemini:** the share page doesn't contain the chat, so the script calls the same internal `batchexecute` endpoint the Gemini website uses to load it. This endpoint is undocumented and may change without notice.
- **ChatGPT:** the share page embeds the conversation as React Router "turbo-stream" data. The script decodes it and follows the main message thread. System messages, tool calls and hidden reasoning are skipped.

## Limitations


- Only public share links work; private chats need to be shared first.
- Images in ChatGPT chats appear as `*[image]*` placeholders.
- Both sites can change their page or API format at any time, which can break extraction.

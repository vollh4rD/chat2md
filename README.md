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

Claude's share data is behind a Cloudflare bot check, so the script can't download it itself. Your browser loads it instead:

```bash
python3 chat2md.py "https://claude.ai/share/<id>" -o chats/
```

1. The script opens the chat's data page in your browser.
2. Press Cmd/Ctrl+A, then Cmd/Ctrl+C to copy it.
3. Press Enter in the terminal. The script reads the clipboard and writes the `.md` file. No JSON file is saved.

You can also pass a saved snapshot `.json` file. It's **deleted after a successful conversion**; add `--keep-json` to keep it.

Artifacts are included as code blocks; attachments appear as `*[attachment: name]*`.

## How it works

- **Grok:** reads the conversation as JSON from Grok's public share endpoint (`/rest/app-chat/share_links/<id>`).
- **Gemini:** the share page doesn't contain the chat, so the script calls the same internal `batchexecute` endpoint the Gemini website uses to load it. This endpoint is undocumented and may change without notice.
- **ChatGPT:** the share page embeds the conversation as React Router "turbo-stream" data. The script decodes it and follows the main message thread. System messages, tool calls and hidden reasoning are skipped.

## Limitations


- Only public share links work; private chats need to be shared first.
- Images in ChatGPT chats appear as `*[image]*` placeholders.
- Both sites can change their page or API format at any time, which can break extraction.

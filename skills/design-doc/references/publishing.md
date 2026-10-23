# Publishing

Publish only when the user asks to share or update the document. Two targets,
in escalation order:

| Target | Audience | Access | Use for |
|---|---|---|---|
| Secret gist + gistpreview | A few reviewers holding the link | Unlisted, not access-controlled: anyone with the URL can read it | Quick drafts and early review |
| Conjure site | Factory | `internal`: Okta SSO, any Factory login | The shareable, durable version |

Never move a draft to conjure without the user's go-ahead: every Factory
employee can open it, and the doc may name internal tickets, people, or
unmerged architecture. Never make a gist public; conjure replaces that path.

## Secret gist draft

### Size budget first

**Keep the file under ~1 MB.** The gist contents API truncates large files:
`GET gists/<id>` sets `"truncated": true`, and gistpreview renders through that
API, so the tail disappears despite a successful write. Typical pages are
80–300 KB. Conjure has no such limit, but a lean page loads faster there too.

Embedded rasters are the usual cause. Four matplotlib PNGs put one report at
1.34 MB and the API returned `truncated: true`. Prefer in-theme SVG charts
([components](components.md#quantitative-proof)); when a raster must stay:

| Image | Encoding | Why |
|---|---|---|
| Flat-colour charts, diagrams | Palette PNG, or SVG when the source can emit it | Few colours compress well; JPEG added noise and made the same charts *larger* (1.63 MB) |
| Photos, screenshots with gradients | JPEG | Continuous tone |

Palette-PNG recipe (took the 1.34 MB report to 292 KB):

```bash
magick in.png -resize '1400x>' -colors 128 out.png
```

`build-md.js` warns past 1 MB. For vector embedding, follow
[show-me's asset embedding](../../show-me/references/surfaces.md#reusing-and-embedding-assets).

### Create

```bash
gh gist create <path>/<slug>.html --desc "<title>"
# → https://gist.github.com/<user>/<gist-id>
```

Share `https://gistpreview.github.io/?<gist-id>/<slug>.html` (the filename
suffix is required for multi-file gists, harmless otherwise). Then verify
`gh api gists/<id> --jq '.files["<name>"].truncated'` is `false` and the
preview reaches the footer.

### Update

```bash
gh gist edit <gist-id> -f <filename-in-gist> <local-path>
```

`-f` names the file **inside** the gist; the positional argument is the local
source. Get the name with `gh gist view <gist-id> --files` and match it exactly:
a mismatch silently adds a second file, and gistpreview then needs the
`/<filename>` suffix to find the right one. Without `-f`, `gh` opens an
interactive editor, which fails in a non-TTY session.

Revising a published draft: keep the same gist id and filename so links already
shared stay valid. Drop to the API only to change the description or touch
several files at once:

```bash
gh api gists/<gist-id> --jq '.files["<slug>.html"].content' > current.html   # live copy to revise against
# build {"description": ..., "files": {"<name>": {"content": ...}}} with a short script (content is too large for -f flags), then
gh api gists/<gist-id> -X PATCH --input <patch.json>
```

### Gist dead ends (verified)

| Endpoint | Status |
|---|---|
| `gistcdn.githack.com/...`, `raw.githack.com/...` | **403 for secret gists**; public only |
| `htmlpreview.github.io/?<raw-url>` | Public gists only; slow first load; occasionally CSP-blocks Google Fonts |
| Direct gist raw URL | Served as `text/plain`: the browser shows source |
| GitHub Pages on a private repo | Requires GitHub Enterprise |

## Conjure

`conjure` (in `~/.local/bin`) deploys a folder of static files; the server and
token live in `~/.config/conjure/config.json` (never print the token). Always
pass `--json` and branch on exit codes: 0 ok, 1 error, 2 usage, 3 auth, 4 not
found.

```bash
mkdir -p <work-dir>/site && cp <slug>.html <work-dir>/site/index.html   # the page must be index.html; assets beside it
conjure deploy <work-dir>/site --site <slug> --json                      # first deploy creates the site; you own it
conjure open <slug> --json                                               # → https://<slug>.conjure.factory.ai/
```

- **Slugs** are DNS labels (lowercase a-z, 0-9, hyphens, ≤63 chars), global
  across Factory, and never reusable after `conjure delete`. Name them after
  the subject, e.g. `ac-949-ptc-retro`; check `conjure list --json` for
  collisions first. Only the owner can deploy again.
- **Updates**: re-run the same `deploy`; every deploy is an immutable version,
  the URL stays the same. `conjure versions <slug> --json` lists them;
  `conjure rollback <slug> [version] --json` reactivates one.
- **Ignore files**: a `.conjureignore` in the folder (gitignore syntax) keeps
  scratch out; `.git`, `.factory`, and dotfiles like `.DS_Store` are always
  excluded. Deploy a dedicated folder, never a worktree.
- **"Chat with this page in Droid"**: uncomment the template's `.chat` block
  and replace `TODO-SLUG` in its `data-prompt` before deploying. Readers paste
  the copied prompt into Droid, which fetches the page with their own conjure
  token.
- **Verify** with an authenticated fetch (anonymous requests get a 302 to
  Okta), without echoing the token:

  ```bash
  curl -sS -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $(jq -r .token ~/.config/conjure/config.json)" https://<slug>.conjure.factory.ai/
  ```

  Then confirm the served copy matches the local file, e.g. fetch it to a file
  and `cmp` it against `index.html`.

## No link previews

⚠️ **Do not try to make the link unfurl into a preview card.** gistpreview
serves a 2.7 KB JavaScript shell (`<title>Gist HTML Preview</title>`, no `og:`
tags) and fetches the document client-side; crawlers don't run JS. A secret
gist's own page returns 404 to anonymous crawlers. A conjure site answers
crawlers with a 302 to Okta. Adding `og:` tags to the HTML changes nothing,
because no crawler-visible response serves them. Post a hero thumbnail or cards
next to the link instead ([share images](share-images.md)).

# Publishing

Publish only when the user requests sharing or updating the document. For an
authorized gist publication, use **secret gist + gistpreview** by default.
Secret gists are unlisted, not access-controlled; use only when the material
and intended audience permit link-based sharing.

## Size budget first

**Keep the file under ~1 MB.** The gist *contents* API can truncate large
files: `GET gists/<id>` sets `"truncated": true`, and gistpreview renders
through that API, so the tail may disappear despite a successful write.

Embedded raster figures are the usual cause. Four matplotlib PNGs put one
report at 1.34 MB and the API returned `truncated: true`. Pick the encoding by
image type:

| Image | Encoding | Why |
|---|---|---|
| Flat-colour charts, diagrams | Palette PNG, or SVG when the source can emit it | Few colours compress well; JPEG adds noise and made the same charts *larger* (1.63 MB) |
| Photos, screenshots with gradients | JPEG | Continuous tone |

Palette-PNG recipe (took the 1.34 MB report to 292 KB):

```bash
magick in.png -resize '1400x>' -colors 128 out.png
```

`build-md.js` warns when its output crosses 1 MB. For vector embedding, follow
[show-me's asset embedding](../../show-me/references/surfaces.md#reusing-and-embedding-assets).

## Create and share

```bash
gh gist create <path>/<slug>-design.html --desc "<title>"   # add --public only if the user asks
# → https://gist.github.com/<user>/<gist-id>
```

Share: `https://gistpreview.github.io/?<gist-id>/<slug>-design.html` (filename
suffix required for multi-file gists, harmless otherwise).

After create or update, verify
`gh api gists/<id> --jq '.files["<name>"].truncated'` is `false` and the
preview reaches the footer.

## Update

Single-file gist, preferred (no JSON assembly needed):

```bash
gh gist edit <gist-id> -f <filename-in-gist> <local-path>
```

`-f` names the file **inside** the gist; the positional arg is the local
source. Get the gist's filename with `gh gist view <gist-id> --files`. Match it
exactly: a mismatch silently adds a second file instead of updating, and
gistpreview then needs the `/<filename>` suffix to find the right one. Without
`-f`, `gh` opens an interactive editor, which fails in a non-TTY agent session.

**Revising an already-published doc**: keep the same gist id and filename so
the gistpreview link already shared in PRs/Slack stays valid. `gh gist edit -f`
handles the common case. Drop to the API only to change the **description** or
to touch several files at once:

```bash
# pull the live copy to revise against
gh api gists/<gist-id> --jq '.files["<slug>-design.html"].content' > current.html
# push: content is too large for -f flags; build {"description": ..., "files": {"<name>": {"content": ...}}}
# with a short python script, then
gh api gists/<gist-id> -X PATCH --input /tmp/gist-patch.json
```

## Dead ends (verified failures)

| Endpoint | Status |
|---|---|
| `gistcdn.githack.com/...`, `raw.githack.com/...` | **403 for secret gists**; public only |
| `htmlpreview.github.io/?<raw-url>` | Works for public gists, slow first-load, occasionally CSP-blocks Google Fonts |
| Direct gist raw URL | Served as `text/plain`; browser shows source, not rendered HTML |
| GitHub Pages on a private repo | Requires GitHub Enterprise |

If the doc must be public-link-shareable AND render reliably: make the gist
public and use `gistcdn.githack.com`. **Confirm with the user first**: public
gists list under their GH profile, and the doc may reference internal tickets,
employees, or unmerged architecture.

⚠️ **Do not try to make the link auto-unfurl into a preview card.**
`gistpreview.github.io` serves a 2.7 KB JavaScript shell with
`<title>Gist HTML Preview</title>` and zero `og:` tags, then fetches the
document client-side; crawlers don't run JS, so they never see the doc. A
secret gist compounds it: `gist.github.com/<id>` returns **404** to an
anonymous crawler. Public gists carry `og:` tags, but `og:image` is GitHub's
generic gist logo. Adding `og:` tags to the HTML changes nothing, because
nothing crawler-visible serves them. A real card would require hosting both
the doc and the image at anonymously fetchable URLs, which defeats the point of
an internal memo and yields a ~360px card smaller than an attached image. Post a hero
thumbnail or cards next to the link instead ([share images](share-images.md)).

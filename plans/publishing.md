# Publishing — artist name, album names, open items

Decided 2026-09-13. Companion to [`soundcloud.md`](soundcloud.md) (the
upload pipeline, FLAC rationale and API gotchas live there, not here).

---

## Artist name: **WERK 16**

16-bit PCM output + the 16-step tracker grid — the two constants true of
every track in `tracks/`, the same class of fact as `SR = 44100`.

**Canonical string is `WERK 16`** — space, caps. Use it verbatim
everywhere. DSPs and distributors match artist profiles on the literal
name string, so shipping one release as `Werk16` and another as `WERK-16`
creates separate artist pages that are painful to merge later.

- Handle: `werk16` wherever it's free, `werknull` as fallback.
- Spoken form: pick one for the bio — "werk sixteen" (travels) or
  "werk sechzehn" (German). Stops the 0/O-style confusion before it starts.
- Visual identity: a row of sixteen cells, some filled — the tracker's own
  step grid. Per-release variation = that track's actual kick pattern.

### Availability as checked (2026-09-13)

| | Status |
|---|---|
| Artist name in use anywhere | Nothing found — no Bandcamp, Spotify or Apple artist under Werk 16 / Werk16 |
| `soundcloud.com/werk16` | 404 — unclaimed |
| `werk16.com`, `werk16.net` | No DNS at all — likely unregistered (confirm at a registrar) |
| `werk16.bandcamp.com` | **UNVERIFIED** — returns 403 to every subdomain from the sandbox, including known-claimed ones. Check in a real browser. |

Neighbours, none of them collisions: **Werke** (UK, dark pop/electronic,
still releasing Jan 2026 — closest sound-alike), **Sixteen Volt** (US
industrial), Werkdiscs, The Werks, art|werk, Werk II (Leipzig venue).

### Naming rules that came out of the search

Carry these into any future naming — they killed real candidates:

- **Never 14, 18, 28, 88, 1488.** Far-right numeric codes, read as such on
  sight in the EBM/industrial scene. `WERK 88` would look great and be
  unusable.
- **No Ø, umlauts, or digit-as-letter** (`Ødemark`, `0werk`, `000werk`) —
  glyphs that look cool and then can't be pronounced, typed or searched.
- **No "seed", no "dead"/"death"** in any name.
- **No 303** — cliché.

Considered and rejected/taken: Nullwerk (crowded), Fernwerk, Schattenwerk,
Kaltwerk, Coriolis, Nullstelle, Nullzeit, Ødemark, Seedform, Dead Seam,
HBLOK, Werk 0 (`werk0.com` is a German enterprise-networking company),
Werk 2 (Leipzig venue), Werk 80, Werk 44, Werk 23, Werk 13, Leerwerk,
Sperrwerk.

---

## The three records

### 1. `tracks/ebm/` → **RELIQUARY** — release first

Five tracks with a 1:35 opener is an **EP**, not an LP. It's also the most
finished body of work in the repo, so it's the low-stakes way to establish
the name. Reliquary is already Part 1 / Part 2 bookending the record (the
*Soli Deo Gloria* shape it was built from), so the album sits inside its
own title. Covers both dialects: the 1993 hammer half (procession, ruin,
no_access) and watchfire's 1999 ascent.

### 2. `tracks/trance/` → **MASCHINENHERZ** — the actual debut album

Named after the track. Deliberately keeps the **German spelling** — the
"English titles from now" rule applies to track titles, not to this; the
German reads as part of the WERK 16 identity. Names the paradox the whole
project runs on: emotional music with no hands on it.

Fourteen tracks is an album and a half — **cut to 9–10**. tech_noir as the
cold open.

### 3. `tracks/dune/` → **SANDWERK** — last

Sand + works: the desert without one word of Frank Herbert's, and it ties
to the artist name. (It was a candidate artist name; unclaimed as of the
search.)

**⚠️ Do not publish this as a Dune record.** "Kwisatz Haderach",
"Muad'Dib", "Sihaya", "Shai-Hulud", "Arrakeen" are invented proper nouns
from an actively-licensed franchise, and a monetised release is a
different risk than a game soundtrack sitting in a repo. Retitle the
tracks that name characters or places. The ones already in plain English —
*Night Pursuit*, *The Sleeper Awakens*, *Water of Life*, *Stillsuit*,
*Base Under Attack* — are fine as-is.

19 tracks is a double album. **Split it**: the desert ambient loops as one
release, the psy-trance side (water_of_life, sleeper_awakens,
the_maker_comes, jihad, fall_of_arrakeen) as another.

---

## Open items

- [ ] **Check `werk16.bandcamp.com` in a browser** — the only availability
      check that came back inconclusive.
- [ ] Register `werk16.com` / `.net` if wanted, and claim
      `soundcloud.com/werk16`.
- [ ] **Find out whether auto-upload tooling to SoundCloud actually
      exists and works in 2026.** Specifically: is there a maintained
      Python client, or is it raw HTTP against the API? What does the
      upload endpoint want, and does it take FLAC directly?
      `soundcloud.md` §3 already flags two blockers to confirm first —
      **client credentials require an active Artist/Next Pro account**,
      and **numeric track IDs are deprecated in favour of URNs**
      (`urn:soundcloud:tracks:xxxx`). Neither has been verified against
      the live API; both were written from genre/platform knowledge, not
      from a successful call. Worth a spike before paying for Next Pro.
- [ ] `soundcloud.md` **ends mid-sentence** at §5 ("...**Ambient") — its
      strategy checklist was never finished.
- [ ] Track-by-track running orders for all three records — not started.
- [ ] The Dune retitles — not started.

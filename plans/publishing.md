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
  sight in the EBM/industrial scene. E.g. `WERK 88` is unusable.
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

~~Fourteen tracks is an album and a half — cut to 9–10.~~ Superseded: the
actual current-version catalogue is 12 tracks / 67:28 once Unsung (dead
end) and Hammerwerk (abandoned) drop out — see the running order below.

### 3. `tracks/dune/` → **SANDWERK** — last

Sand + works: the desert without one word of Frank Herbert's, and it ties
to the artist name. (It was a candidate artist name; unclaimed as of the
search.)

Track titles include some of Frank Herbert's invented terms (Kwisatz
Haderach, Muad'Dib, Sihaya, Shai-Hulud, Arrakeen) — low risk; titles
aren't copyrightable.

19 tracks is a double album. **Split it**: the desert ambient loops as one
release, the psy-trance side (water_of_life, sleeper_awakens,
the_maker_comes, jihad, fall_of_arrakeen) as another.

---

## Open items

- [ ] **Check `werk16.bandcamp.com` in a browser** — the only availability
      check that came back inconclusive.
- [ ] Register `werk16.com` / `.net` if wanted, and claim
      `soundcloud.com/werk16`.
- [x] **Checked (2026-09-14): no viable Python auto-upload path exists
      right now.** SoundCloud closed public API registration years ago —
      new client IDs are granted case-by-case via a manual review form
      (weeks, often denied), not tied to buying Artist/Next Pro. That's a
      harder blocker than `soundcloud.md` §3 implied.
      - `soundcloud-python` (official, `pip install soundcloud`) can
        upload but needs that closed grant, and **SoundCloud's own repo
        says it's unmaintained** — they've told the community to fork it.
      - `soundcloud.py`/`soundcloud-v2`, `soundcloudpy`, `soundcloud-lib`
        — all actively maintained, all **read/download-only**, wrong job.
      - `soundcloud-mcp` claims OAuth2.1+PKCE upload of MP3/WAV/FLAC —
        unverified; almost certainly hits the same closed client-ID gate
        underneath, an MCP wrapper can't route around that.
      - **Decision needed:** either submit SoundCloud's developer-access
        form now (review takes weeks, so start early if this path is
        wanted) and accept manual upload until/unless it's approved, or
        skip automation and just upload through the web UI /
        Next Pro's own distribution to Spotify/Apple.
- [ ] `soundcloud.md` **ends mid-sentence** at §5 ("...**Ambient") — its
      strategy checklist was never finished.
- [x] Maschinenherz running order — done, see below.
- [x] Sandwerk running order — done, see below.
- [ ] Reliquary running order — holding; still refining and possibly
      adding more tracks first.

---

## MASCHINENHERZ — running order (decided 2026-09-15)

12 tracks, 67:28 total. Sequencing follows the composer's own cross-track
references in the `*_notes.md` docs (the machine-voice arc, the "run lane",
and explicit dark/bright-twin pairings) rather than an arbitrary order.

| # | Track | Time | Key/BPM | Why here |
|---|---|---|---|---|
| 1 | Tech Noir | 3:20 | D minor | Cold open; seeds the `love_phrase` voice Maschinenherz ports |
| 2 | Maschinenherz | 7:26 | E minor / 145 | Title track — machine-voice arc station 1 |
| 3 | Silver Wire | 5:38 | A minor / 142 | Arc station 2 — the machine sings solo |
| 4 | Morgenland | 6:14 | C Phrygian/Hijaz / 142 | Arc station 3 — sings an old song, modal turn east |
| 5 | Flightpath | 4:43 | C minor / 138 | Closes the "run lane" (silver_wire ran, morgenland sang, flightpath flies) |
| 6 | Eisgang | 4:55 | F minor / 138 | Side-B pivot, hardest track |
| 7 | Ungeschrieben | 5:48 | F minor / 130 | Same key as Eisgang — held tonic across the cut |
| 8 | Nachtkind | 5:38 | G minor / 139 | Deepens the dark, one step up from F minor |
| 9 | Penumbra | 6:06 | C minor / 140 | The trough — notes call it Farlight's dark twin |
| 10 | Lost | 5:32 | Bm/G/D/A / 130 | Climbs back out toward hope |
| 11 | Farlight | 6:07 | E minor / 136 | Answers Penumbra (delayed Q/A); echoes track 2's E minor |
| 12 | Adrift | 6:00 | C♯ minor / 137 | Farlight's bell, floating not struck — dissolve close |

Excluded: **Unsung** (documented dead end, `unsung.py`'s own notes say the
sung voice reads "strange"), **Hammerwerk** (abandoned, no script written).

If a tighter single-LP cut is wanted later, drop **Penumbra** and
**Ungeschrieben** first — each is the darker sibling of a stronger track
already on the list (Farlight, Eisgang) so cutting them loses least.

---

## SANDWERK — running order (decided 2026-09-15)

12 tracks, 74:58 total — the **story arc** only. `tracks/dune/` also has
five seamless game-state loops (arrakis_winds_v3, spice_must_flow,
stillsuit, sandstorm_coriolis, base_under_attack) plus the pre-Dune test
piece ambient_track; these underlie gameplay with no build and no ending
and are excluded from the listening release, same as Unsung/Hammerwerk
were excluded from Maschinenherz. Full table + reasoning:
`tracks/dune/sandwerk_running_order.md`. Playback script:
`tracks/dune/play_sandwerk.sh`.

1. Night Pursuit — 2. The Maker Comes — 3. Kanly — 4. Water of Life —
5. The Sleeper Awakens — 6. Fall of Arrakeen — 7. The Navigator —
8. Jihad — 9. Kwisatz Haderach — 10. Gurney's Song —
11. Litany Against Fear — 12. Sihaya.

Track titles include some of Frank Herbert's invented terms (Kwisatz
Haderach, Sihaya, Kanly, Arrakeen, Sardaukar) — low risk; titles aren't
copyrightable.

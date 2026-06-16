"""Instrument registry: id → (callable, param_schemas, family).

The registry is the single source of truth for instrument discovery.  The GUI
auto-builds parameter sliders from the ParamSchema list; the control facade
uses it to dispatch ``render_instrument`` calls.

Usage::

    from forge.instruments.registry import REGISTRY, get_instrument

    meta = REGISTRY["kick"]
    buf = meta["fn"](params={"f0": 60.0, "drive": 1.5}, rng=rng)
    schemas = meta["params"]   # list[ParamSchema]
    family = meta["family"]    # str
"""

from __future__ import annotations

from forge.instruments.bass import (
    ACID_PARAMS,
    BASS_NOTE_PARAMS,
    PSY_BASS_PARAMS,
    acid_note,
    bass_note,
    psy_bass_note,
)
from forge.instruments.fx import (
    EXPLOSION_PARAMS,
    HEART_PARAMS,
    REV_CYMBAL_PARAMS,
    RISER_PARAMS,
    ZAP_PARAMS,
    explosion,
    heart,
    rev_cymbal,
    riser,
    make_zap,
)
from forge.instruments.percussion import (
    CLAP_PARAMS,
    DOUM_PARAMS,
    FRAME_HIT_PARAMS,
    HAT_PARAMS,
    KICK_PARAMS,
    SNARE_PARAMS,
    TEK_PARAMS,
    WAR_DRUM_PARAMS,
    frame_roll,
    make_clap,
    make_doum,
    make_frame_hit,
    make_hat,
    make_kick,
    make_snare,
    make_tek,
    make_war_drum,
)
from forge.instruments.strings import (
    CELLO_PARAMS,
    KS_PARAMS,
    PAD_PARAMS,
    PIANO_PARAMS,
    cello_line,
    karplus_strong,
    pad_chord,
    piano_note,
)
from forge.instruments.textures import (
    DRONE_PARAMS,
    SWELL_PARAMS,
    WIND_PARAMS,
    drone,
    swell,
    wind,
)
from forge.instruments.voices import (
    CHOIR_PARAMS,
    LEAD_PARAMS,
    VOICE_PARAMS,
    choir,
    lead_phrase,
    voice_phrase,
)


def _entry(fn, params, family):
    return {"fn": fn, "params": params, "family": family}


REGISTRY: dict = {
    # textures
    "wind":        _entry(wind,          WIND_PARAMS,        "texture"),
    "drone":       _entry(drone,         DRONE_PARAMS,       "texture"),
    "swell":       _entry(swell,         SWELL_PARAMS,       "texture"),
    # percussion
    "doum":        _entry(make_doum,     DOUM_PARAMS,        "percussion"),
    "tek":         _entry(make_tek,      TEK_PARAMS,         "percussion"),
    "kick":        _entry(make_kick,     KICK_PARAMS,        "percussion"),
    "hat":         _entry(make_hat,      HAT_PARAMS,         "percussion"),
    "clap":        _entry(make_clap,     CLAP_PARAMS,        "percussion"),
    "snare":       _entry(make_snare,    SNARE_PARAMS,       "percussion"),
    "war_drum":    _entry(make_war_drum, WAR_DRUM_PARAMS,    "percussion"),
    "frame_hit":   _entry(make_frame_hit,FRAME_HIT_PARAMS,   "percussion"),
    "frame_roll":  _entry(frame_roll,    FRAME_HIT_PARAMS,   "percussion"),
    # strings
    "harp":        _entry(karplus_strong,KS_PARAMS,          "strings"),
    "piano":       _entry(piano_note,    PIANO_PARAMS,       "strings"),
    "cello":       _entry(cello_line,    CELLO_PARAMS,       "strings"),
    "pad":         _entry(pad_chord,     PAD_PARAMS,         "strings"),
    # voices
    "voice":       _entry(voice_phrase,  VOICE_PARAMS,       "voice"),
    "choir":       _entry(choir,         CHOIR_PARAMS,       "voice"),
    "lead":        _entry(lead_phrase,   LEAD_PARAMS,        "voice"),
    # bass
    "bass":        _entry(bass_note,     BASS_NOTE_PARAMS,   "bass"),
    "psy_bass":    _entry(psy_bass_note, PSY_BASS_PARAMS,    "bass"),
    "acid":        _entry(acid_note,     ACID_PARAMS,        "bass"),
    # fx
    "zap":         _entry(make_zap,      ZAP_PARAMS,         "fx"),
    "riser":       _entry(riser,         RISER_PARAMS,       "fx"),
    "explosion":   _entry(explosion,     EXPLOSION_PARAMS,   "fx"),
    "heart":       _entry(heart,         HEART_PARAMS,       "fx"),
    "rev_cymbal":  _entry(rev_cymbal,    REV_CYMBAL_PARAMS,  "fx"),
}


def get_instrument(instrument_id: str) -> dict:
    """Return the registry entry for *instrument_id*.

    Raises ``KeyError`` with a helpful message if not found.
    """
    if instrument_id not in REGISTRY:
        raise KeyError(
            f"Unknown instrument '{instrument_id}'. "
            f"Available: {sorted(REGISTRY)}"
        )
    return REGISTRY[instrument_id]


def list_instruments() -> list[dict]:
    """Return a list of instrument summary dicts for the control facade."""
    return [
        {
            "id": iid,
            "family": entry["family"],
            "params": [p.to_dict() for p in entry["params"]],
        }
        for iid, entry in REGISTRY.items()
    ]

"""Matplotlib visualisations for music inspector results."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def save_all(results: dict, out_dir: Path) -> list[Path]:
    """Generate and save all plots. Returns list of saved paths."""
    saved = [
        _plot_overview(results, out_dir),
        _plot_structure(results, out_dir),
        _plot_harmony(results, out_dir),
    ]
    return [p for p in saved if p is not None]


# ---------------------------------------------------------------------------

def _plot_overview(results: dict, out_dir: Path) -> Path | None:
    audio    = results["audio"]
    tempo    = results["tempo"]
    struct   = results["structure"]
    y, sr    = audio["y"], audio["sr"]
    name     = Path(audio["path"]).name

    fig = plt.figure(figsize=(16, 10))
    gs  = gridspec.GridSpec(3, 1, hspace=0.45)
    fig.suptitle(f"Overview — {name}", fontsize=13, fontweight="bold")

    # Waveform
    ax1 = fig.add_subplot(gs[0])
    times = np.linspace(0, audio["duration"], len(y))
    ax1.plot(times, y, color="#4a9eda", linewidth=0.3, alpha=0.85, rasterized=True)
    _mark_bounds(ax1, struct["boundaries_sec"])
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Waveform  (orange lines = section boundaries)")
    ax1.set_xlim(0, audio["duration"])

    # RMS energy
    ax2 = fig.add_subplot(gs[1])
    hop  = 2048
    rms  = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_db = 20 * np.log10(rms + 1e-10)
    t_rms  = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    ax2.fill_between(t_rms, rms_db, rms_db.min(), color="#e74c3c", alpha=0.6)
    ax2.plot(t_rms, rms_db, color="#c0392b", linewidth=0.6)
    _mark_bounds(ax2, struct["boundaries_sec"])
    ax2.set_ylabel("RMS (dB)")
    ax2.set_title("Energy Envelope")
    ax2.set_xlim(0, audio["duration"])

    # Tempo over time
    ax3 = fig.add_subplot(gs[2])
    tot  = tempo.get("tempo_over_time", [])
    if tot:
        t_pts   = [w["t_start"] + 15 for w in tot]
        bpm_pts = [w["bpm"]           for w in tot]
        ax3.plot(t_pts, bpm_pts, color="#2ecc71", linewidth=1.5,
                 marker="o", markersize=3, markerfacecolor="#27ae60")
        ax3.axhline(tempo["bpm"], color="#f39c12", linewidth=1, linestyle="--",
                    label=f"global {tempo['bpm']:.1f} BPM")
        ax3.legend(fontsize=8)
        ax3.set_ylabel("BPM")
        ax3.set_title("Tempo Over Time (30 s windows)")
        ax3.set_xlim(0, audio["duration"])
        ymin = max(0, min(bpm_pts) - 10)
        ymax = max(bpm_pts) + 10
        ax3.set_ylim(ymin, ymax)

    for ax in [ax1, ax2, ax3]:
        ax.set_xlabel("Time (s)")

    path = out_dir / "overview.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_structure(results: dict, out_dir: Path) -> Path | None:
    audio  = results["audio"]
    timbre = results["timbre"]
    struct = results["structure"]
    y, sr  = audio["y"], audio["sr"]
    name   = Path(audio["path"]).name

    fig = plt.figure(figsize=(16, 8))
    gs  = gridspec.GridSpec(2, 1, hspace=0.45)
    fig.suptitle(f"Structure — {name}", fontsize=13, fontweight="bold")

    # Mel spectrogram
    ax1  = fig.add_subplot(gs[0])
    hop  = 4096
    S    = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, hop_length=hop)
    S_db = librosa.power_to_db(S, ref=np.max)
    img  = librosa.display.specshow(S_db, sr=sr, hop_length=hop, x_axis="time",
                                    y_axis="mel", ax=ax1, cmap="magma")
    fig.colorbar(img, ax=ax1, format="%+2.0f dB", pad=0.01)
    ax1.set_title("Mel Spectrogram")
    _mark_bounds(ax1, struct["boundaries_sec"], color="white", alpha=0.6)

    # Section energy + centroid
    ax2 = fig.add_subplot(gs[1])
    if timbre:
        idxs   = [s["idx"]         for s in timbre]
        rms_db = [s["rms_db"]      for s in timbre]
        cents  = [s["centroid_hz"] for s in timbre]
        durs   = [s["duration"]    for s in timbre]

        norm_rms = np.array(rms_db)
        norm_rms = (norm_rms - norm_rms.min()) / (norm_rms.ptp() + 1e-6)
        colors   = plt.cm.RdYlGn(norm_rms)

        ax2.bar(idxs, rms_db, color=colors, edgecolor="white", linewidth=0.5, zorder=2)
        ax2.set_xlabel("Section #")
        ax2.set_ylabel("RMS (dB)")
        ax2.set_title("Section Energy (colour = relative level) + Spectral Centroid")
        ax2.set_xticks(idxs)

        ax2b = ax2.twinx()
        ax2b.plot(idxs, cents, color="#3498db", marker="^", linewidth=1.5,
                  markersize=5, label="Centroid Hz", zorder=3)
        ax2b.set_ylabel("Spectral Centroid (Hz)", color="#3498db")
        ax2b.tick_params(axis="y", labelcolor="#3498db")
        ax2b.legend(loc="upper right", fontsize=8)

    path = out_dir / "structure.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_harmony(results: dict, out_dir: Path) -> Path | None:
    audio   = results["audio"]
    harmony = results["harmony"]
    struct  = results["structure"]
    y, sr   = audio["y"], audio["sr"]
    name    = Path(audio["path"]).name

    fig = plt.figure(figsize=(16, 8))
    gs  = gridspec.GridSpec(2, 1, hspace=0.45)
    fig.suptitle(f"Harmony — {name}", fontsize=13, fontweight="bold")

    # Chromagram
    ax1  = fig.add_subplot(gs[0])
    hop  = 4096
    cqt  = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    img  = librosa.display.specshow(cqt, sr=sr, hop_length=hop, x_axis="time",
                                    y_axis="chroma", ax=ax1, cmap="YlOrRd")
    fig.colorbar(img, ax=ax1, pad=0.01)
    ax1.set_title(f"Chromagram (CQT)  — estimated key: "
                  f"{harmony['key']} {harmony['mode']}")
    _mark_bounds(ax1, struct["boundaries_sec"], color="white", alpha=0.5)

    # Chroma profile bars
    ax2 = fig.add_subplot(gs[1])
    notes       = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    chroma_mean = np.array(harmony["chroma_mean"])
    chroma_norm = chroma_mean / (chroma_mean.max() + 1e-10)
    colors      = plt.cm.YlOrRd(chroma_norm)
    ax2.bar(notes, chroma_norm, color=colors, edgecolor="white", linewidth=0.5)
    ax2.set_title("Mean Chroma Profile")
    ax2.set_ylabel("Relative Energy")
    ax2.set_ylim(0, 1.1)
    # Highlight detected key note
    root = harmony["key"]
    if root in notes:
        idx = notes.index(root)
        ax2.bar([notes[idx]], [chroma_norm[idx]], color="#e74c3c",
                edgecolor="white", linewidth=0.5, label=f"root: {root}")
        ax2.legend(fontsize=9)

    path = out_dir / "harmony.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _mark_bounds(ax, boundaries_sec: list[float], color: str = "#ff6b35", alpha: float = 0.7):
    for t in boundaries_sec:
        ax.axvline(x=t, color=color, alpha=alpha, linewidth=0.9)

# Forge UI — Developer Notes

## Inspecting the widget tree

Qt has no built-in browser-style "Inspect Element", but there are two options:

### GammaRay (full inspector)

GammaRay by KDAB is the closest equivalent to browser DevTools — live widget tree,
property editor, signal/slot monitor, geometry overlay, etc.

```bash
apt install gammaray          # or build from source / download from kdab.com/gammaray
gammaray --pid $(pgrep -f "forge.ui.main")
```

Or launch with injection:

```bash
gammaray -- python -m forge.ui.main
```

### DIY hover-tooltip inspector (no install)

Paste this into `main.py` during development (after `app = QApplication(...)`):

```python
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QToolTip

class _WidgetInspector:
    def __init__(self, app):
        app.installEventFilter(self)
    def eventFilter(self, obj, event):
        from PySide6.QtWidgets import QWidget
        if event.type() == QEvent.Type.MouseMove and isinstance(obj, QWidget):
            info = f"{obj.__class__.__name__}  objectName={obj.objectName()!r}"
            QToolTip.showText(event.globalPosition().toPoint(), info)
        return False

_WidgetInspector(app)
```

Hover over any widget and a tooltip shows its **class name** and **objectName**.

---

## Widget object names

All named widgets have `objectName` set so the inspector above (and GammaRay)
surface them clearly. Names are also grep-able:

```
grep -rn 'setObjectName' forge/ui/
```

### window.py — MainWindow

| objectName | widget |
|---|---|
| `forge-main-window` | `MainWindow` |
| `central-widget` | central `QWidget` |
| `main-splitter` | horizontal `QSplitter` |
| `arrangement-view` | `ArrangementView` (left panel) |
| `tracker-panel` | `QWidget` holding the scroll area |
| `tracker-scroll` | `QScrollArea` for channel rows |
| `tracker-container` | inner container of the scroll area |
| `mixer-dock` | `QDockWidget` (hidden by default) |
| `mixer` | `MixerWidget` inside the dock |
| `workshop-area` | `QWidget` bottom-left area |
| `ab-compare` | `ABCompareWidget` |
| `export-progress` | `QProgressBar` (visible during export/render) |
| `status-label` | `QLabel` in the status bar |

### transport.py — TransportWidget

| objectName | widget |
|---|---|
| `transport` | `TransportWidget` |
| `play-btn` | play/pause `QPushButton` |
| `stop-btn` | stop `QPushButton` |
| `position-label` | bar:beat `QLabel` |
| `seek-slider` | position `QSlider` |

### pattern_editor.py — TrackerEditor / TrackerRow

| objectName | widget |
|---|---|
| `tracker-editor-N` | `TrackerEditor` for channel N |
| `channel-ctrl-N` | left control panel `QWidget` for channel N |
| `channel-name` | instrument name `QLabel` |
| `volume-slider` | vertical `QSlider` |
| `mute-btn` | M `QPushButton` |
| `solo-btn` | S `QPushButton` |
| `tracker-row` | `TrackerRow` step grid |
| `tracker-row-scroll` | `QScrollArea` wrapping the row |
| `remove-btn` | × `QPushButton` |
| `instrument-label` | instrument name label inside `TrackerRow` |

### mixer.py — MixerWidget / _Strip

| objectName | widget |
|---|---|
| `mixer-widget` | `MixerWidget` |
| `mixer-strip-NAME` | `_Strip` for channel NAME |
| `strip-name-label` | channel name `QLabel` inside strip |
| `fader` | vertical volume `QSlider` |
| `mute-btn` | M `QPushButton` |
| `pan-slider` | pan `QSlider` |
| `reverb-slider` | reverb send `QSlider` |

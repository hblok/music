"""forge.document — mutable project document model (no Qt, no DSP).

The document model is the single source of truth for what the user is editing.
The UI mutates it only through the typed edit API on ``ProjectDoc``; every
mutation is recorded as a ``Transaction`` so undo/redo and cache-invalidation
keys are always derivable from history.

Public API::

    from forge.document.model import ProjectDoc
    from forge.document.channels import PatternChannel, TextureChannel, AutomationChannel
    from forge.document.history import History
    from forge.document.transaction import Transaction, channel_content_hash
"""

"""Allow running MetaWriter as ``python -m metawriter``."""

from .cli import main

raise SystemExit(main())

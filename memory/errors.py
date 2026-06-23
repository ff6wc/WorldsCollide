# RomSpaceError subclasses MemoryError because these failures were historically
# raised as MemoryError; existing callers/tools catching MemoryError still work
class RomSpaceError(MemoryError):
    """Raised when data does not fit in the requested/reserved ROM space.

    Common causes and resolutions are documented in agents.md under
    "Memory Overflow / Bank Exhaustion".
    """

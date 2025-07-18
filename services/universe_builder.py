# Global instance
_universe_builder: Optional[UniverseBuilder] = None


async def get_universe_builder() -> UniverseBuilder:
    """Get global universe builder instance"""
    global _universe_builder
    if _universe_builder is None:
        _universe_builder = UniverseBuilder()
    return _universe_builder 
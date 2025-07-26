#!/usr/bin/env python3
"""Test script to verify dynamic provider loading."""

from terminai.llm.base import LLMManager
from terminai.config.manager import ConfigManager

def test_providers():
    """Test provider loading."""
    print("🧪 Testing dynamic provider loading...")
    
    config = ConfigManager()
    manager = LLMManager()
    manager.load_providers_from_config(config._config)
    
    print("✅ Available providers:", manager.list_providers())
    print("✅ Configured providers:", manager.get_configured_providers(config._config))
    
    # Test individual providers
    for name in manager.list_providers():
        provider_config = config.get_llm_config(name)
        provider = manager.get_provider(name, provider_config)
        if provider:
            print(f"✅ {name}: configured={provider.is_configured()}")
        else:
            print(f"❌ {name}: failed to load")

if __name__ == "__main__":
    test_providers()

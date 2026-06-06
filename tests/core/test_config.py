from src.core.config import settings

def test_whisper_configs_exist():
    # Verify these configs exist and are strings (so the test is not brittle to environmental values)
    assert hasattr(settings, "WHISPER_MODEL_SIZE")
    assert hasattr(settings, "WHISPER_DEVICE")
    assert hasattr(settings, "WHISPER_COMPUTE_TYPE")
    assert isinstance(settings.WHISPER_MODEL_SIZE, str)
    assert isinstance(settings.WHISPER_DEVICE, str)
    assert isinstance(settings.WHISPER_COMPUTE_TYPE, str)

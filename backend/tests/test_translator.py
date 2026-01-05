"""Tests for translation engine."""
import pytest
from unittest.mock import Mock, patch

from translator.engine import (
    detect_language,
    TranslationState,
    should_retry,
    TranslationEngine
)


def test_language_detection_english():
    """Test English language detection."""
    state: TranslationState = {
        "original_text": "Hello, how are you?",
        "detected_language": None,
        "translation": None,
        "quality_score": None,
        "retry_count": 0,
        "max_retries": 2,
        "final_result": None
    }
    
    result = detect_language(state)
    assert result["detected_language"] == "en"


def test_language_detection_korean():
    """Test Korean language detection."""
    state: TranslationState = {
        "original_text": "안녕하세요, 어떻게 지내세요?",
        "detected_language": None,
        "translation": None,
        "quality_score": None,
        "retry_count": 0,
        "max_retries": 2,
        "final_result": None
    }
    
    result = detect_language(state)
    assert result["detected_language"] == "ko"


def test_quality_validation_retry_needed():
    """Test quality validation triggers retry when score is low."""
    state: TranslationState = {
        "original_text": "Test",
        "detected_language": "en",
        "translation": "테스트",
        "quality_score": 0.6,
        "retry_count": 0,
        "max_retries": 2,
        "final_result": None
    }
    
    decision = should_retry(state)
    assert decision == "retranslate"


def test_quality_validation_no_retry():
    """Test quality validation finalizes when score is high."""
    state: TranslationState = {
        "original_text": "Test",
        "detected_language": "en",
        "translation": "테스트",
        "quality_score": 0.85,
        "retry_count": 0,
        "max_retries": 2,
        "final_result": None
    }
    
    decision = should_retry(state)
    assert decision == "finalize"


def test_retry_logic_max_retries():
    """Test retry logic respects maximum retry count."""
    state: TranslationState = {
        "original_text": "Test",
        "detected_language": "en",
        "translation": "테스트",
        "quality_score": 0.6,
        "retry_count": 2,
        "max_retries": 2,
        "final_result": None
    }
    
    decision = should_retry(state)
    assert decision == "finalize"


@pytest.mark.asyncio
async def test_translation_engine_initialization():
    """Test translation engine initializes correctly."""
    engine = TranslationEngine()
    assert engine.workflow is not None

"""LangGraph-based translation engine with quality validation and retry logic."""
import logging
from typing import TypedDict, Literal, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from config import settings

logger = logging.getLogger(__name__)


class TranslationState(TypedDict):
    """State for the translation workflow."""
    original_text: str
    detected_language: Optional[str]
    translation: Optional[str]
    quality_score: Optional[float]
    retry_count: int
    max_retries: int
    final_result: Optional[dict]


def detect_language(state: TranslationState) -> TranslationState:
    """Detect whether text is English or Korean."""
    text = state["original_text"]
    
    # Simple heuristic: check if text contains Hangul characters
    has_hangul = any('\uac00' <= char <= '\ud7a3' for char in text)
    
    if has_hangul:
        detected = "ko"
    else:
        detected = "en"
    
    logger.info(f"Detected language: {detected}")
    state["detected_language"] = detected
    return state


def translate(state: TranslationState) -> TranslationState:
    """Translate text using OpenAI GPT-4."""
    text = state["original_text"]
    source_lang = state["detected_language"]
    
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        openai_api_key=settings.openai_api_key
    )
    
    if source_lang == "en":
        prompt = f"Translate the following English text to Korean. Only provide the translation without any explanations:\n\n{text}"
    else:
        prompt = f"Translate the following Korean text to English. Only provide the translation without any explanations:\n\n{text}"
    
    try:
        response = llm.invoke(prompt)
        translation = response.content.strip()
        logger.info(f"Translation completed: {len(translation)} characters")
        state["translation"] = translation
    except Exception as e:
        logger.error(f"Translation error: {e}")
        state["translation"] = ""
    
    return state


def validate_quality(state: TranslationState) -> TranslationState:
    """Validate translation quality using LLM."""
    original = state["original_text"]
    translation = state["translation"]
    source_lang = state["detected_language"]
    
    if not translation:
        state["quality_score"] = 0.0
        return state
    
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        openai_api_key=settings.openai_api_key
    )
    
    if source_lang == "en":
        prompt = f"""Rate the quality of this Korean translation on a scale of 0.0 to 1.0.
Consider accuracy, fluency, and naturalness.
Respond with ONLY a number between 0.0 and 1.0.

Original English: {original}
Korean Translation: {translation}

Quality Score:"""
    else:
        prompt = f"""Rate the quality of this English translation on a scale of 0.0 to 1.0.
Consider accuracy, fluency, and naturalness.
Respond with ONLY a number between 0.0 and 1.0.

Original Korean: {original}
English Translation: {translation}

Quality Score:"""
    
    try:
        response = llm.invoke(prompt)
        score_text = response.content.strip()
        # Extract numeric value
        score = float(score_text)
        score = max(0.0, min(1.0, score))  # Clamp to [0.0, 1.0]
        logger.info(f"Quality score: {score}")
        state["quality_score"] = score
    except Exception as e:
        logger.error(f"Quality validation error: {e}")
        state["quality_score"] = 0.5  # Default moderate score on error
    
    return state


def should_retry(state: TranslationState) -> Literal["retranslate", "finalize"]:
    """Determine if translation should be retried based on quality."""
    quality = state["quality_score"]
    retry_count = state["retry_count"]
    max_retries = state["max_retries"]
    
    if quality and quality < 0.7 and retry_count < max_retries:
        logger.info(f"Quality below threshold ({quality}), retrying (attempt {retry_count + 1}/{max_retries})")
        return "retranslate"
    else:
        logger.info(f"Finalizing translation (quality: {quality}, retries: {retry_count})")
        return "finalize"


def retranslate(state: TranslationState) -> TranslationState:
    """Retry translation with adjusted prompt."""
    state["retry_count"] += 1
    text = state["original_text"]
    source_lang = state["detected_language"]
    previous_translation = state["translation"]
    
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.3,  # Slightly higher temperature for variation
        openai_api_key=settings.openai_api_key
    )
    
    if source_lang == "en":
        prompt = f"""Translate the following English text to Korean with high accuracy and natural fluency.
Previous translation was not satisfactory. Provide an improved translation.
Only provide the translation without any explanations.

English text: {text}

Previous translation: {previous_translation}

Improved Korean translation:"""
    else:
        prompt = f"""Translate the following Korean text to English with high accuracy and natural fluency.
Previous translation was not satisfactory. Provide an improved translation.
Only provide the translation without any explanations.

Korean text: {text}

Previous translation: {previous_translation}

Improved English translation:"""
    
    try:
        response = llm.invoke(prompt)
        translation = response.content.strip()
        logger.info(f"Retranslation completed: {len(translation)} characters")
        state["translation"] = translation
    except Exception as e:
        logger.error(f"Retranslation error: {e}")
    
    return state


def finalize(state: TranslationState) -> TranslationState:
    """Finalize the translation result."""
    state["final_result"] = {
        "original": state["original_text"],
        "detected_language": state["detected_language"],
        "translation": state["translation"],
        "quality_score": state["quality_score"]
    }
    logger.info("Translation workflow finalized")
    return state


def create_translation_workflow() -> StateGraph:
    """Create the LangGraph translation workflow."""
    workflow = StateGraph(TranslationState)
    
    # Add nodes
    workflow.add_node("detect_language", detect_language)
    workflow.add_node("translate", translate)
    workflow.add_node("validate_quality", validate_quality)
    workflow.add_node("retranslate", retranslate)
    workflow.add_node("finalize", finalize)
    
    # Define edges
    workflow.set_entry_point("detect_language")
    workflow.add_edge("detect_language", "translate")
    workflow.add_edge("translate", "validate_quality")
    workflow.add_conditional_edges(
        "validate_quality",
        should_retry,
        {
            "retranslate": "retranslate",
            "finalize": "finalize"
        }
    )
    workflow.add_edge("retranslate", "validate_quality")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


class TranslationEngine:
    """Main translation engine using LangGraph."""
    
    def __init__(self) -> None:
        """Initialize the translation engine."""
        self.workflow = create_translation_workflow()
        logger.info("Translation engine initialized")
    
    def translate(self, text: str, max_retries: int = 2) -> dict:
        """
        Translate text with automatic quality validation and retry.
        
        Args:
            text: Text to translate
            max_retries: Maximum number of retries if quality is low
            
        Returns:
            Dictionary with translation result
        """
        initial_state: TranslationState = {
            "original_text": text,
            "detected_language": None,
            "translation": None,
            "quality_score": None,
            "retry_count": 0,
            "max_retries": max_retries,
            "final_result": None
        }
        
        try:
            final_state = self.workflow.invoke(initial_state)
            return final_state["final_result"]
        except Exception as e:
            logger.error(f"Translation engine error: {e}")
            return {
                "original": text,
                "detected_language": "unknown",
                "translation": "",
                "quality_score": 0.0,
                "error": str(e)
            }


# Global engine instance
engine = TranslationEngine()

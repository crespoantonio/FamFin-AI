import time
import logging
import httpx
from typing import Optional
from src.core.config import settings
from src.services.whisper_service import WhisperService
from src.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

class AIOrchestrator:
    async def orchestrate(self, user_id: str, text: Optional[str], audio_url: Optional[str], chat_id: int):
        start_time = time.time()
        status = "success"
        response_text = ""
        extracted_data = None
        
        try:
            # 1. Process Audio if provided
            if audio_url:
                try:
                    whisper_service = WhisperService()
                    text, _ = await whisper_service.transcribe(audio_url=audio_url)
                    if not text:
                        raise ValueError("Transcription returned empty text.")
                except Exception as e:
                    logger.error(f"Transcription failed: {e}")
                    status = "error"
                    response_text = "I couldn't understand the audio. Could you please type it or try again?"
                    
            # 2. Extract Data if we have text and no previous error
            if text and status == "success":
                try:
                    extraction_service = ExtractionService()
                    result = await extraction_service.extract(text=text)
                    extracted_data = result.model_dump()
                    
                    # Construct success message
                    response_text = f"Saved {result.amount} {result.currency} for '{result.concept}' under category '{result.category}'."
                except Exception as e:
                    logger.error(f"Extraction failed: {e}")
                    status = "error"
                    response_text = "I couldn't extract the details from your message. Please make sure to include the amount and what it was for."
            elif not text and status == "success":
                status = "error"
                response_text = "No message or audio was provided."
                
        except Exception as e:
            logger.error(f"Unexpected error in orchestrator: {e}")
            status = "error"
            response_text = "An unexpected error occurred while processing your request."
            
        # 3. Callback to n8n
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "status": status,
            "text": response_text,
            "extracted_data": extracted_data
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.N8N_CALLBACK_URL,
                    json=payload,
                    headers={"X-FamFin-Token": settings.MESSAGING_WEBHOOK_SECRET}
                )
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send callback to n8n: {e}")
            
        # 4. Log 3s Audit
        duration = time.time() - start_time
        logger.info(f"[3s Audit] Total pipeline orchestration took {duration:.2f} seconds (user_id: {user_id}, text: '{text}')")

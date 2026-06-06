import time
import logging
import threading
import asyncio
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator
import ollama
from src.core.config import settings

logger = logging.getLogger(__name__)

class ExtractionError(Exception):
    """Custom exception raised when extraction fails."""
    pass

class ExtractionResult(BaseModel):
    amount: float = Field(..., gt=0, description="The exact amount of the transaction")
    category: str = Field(..., description="Mapped to one of: 'Food/Drink', 'Transport', 'Rent/Bills', 'Shopping', 'Leisure', 'Other'")
    concept: str = Field(..., description="The transaction description or concept")
    currency: str = Field(default="USD", description="ISO 3-letter currency code, e.g. 'USD', 'EUR', 'GBP'")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"Food/Drink", "Transport", "Rent/Bills", "Shopping", "Leisure", "Other"}
        cleaned = v.strip()
        
        # Check title case
        if cleaned.title() == "Food/Drink":
            return "Food/Drink"
            
        for cat in allowed:
            if cleaned.lower() == cat.lower():
                return cat
        return "Other"

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        mapping = {
            "dollar": "USD",
            "dollars": "USD",
            "usd": "USD",
            "$": "USD",
            "euro": "EUR",
            "euros": "EUR",
            "eur": "EUR",
            "€": "EUR",
            "pound": "GBP",
            "pounds": "GBP",
            "gbp": "GBP",
            "£": "GBP"
        }
        cleaned = v.strip().lower()
        if cleaned in mapping:
            return mapping[cleaned]
            
        if len(cleaned) == 3 and cleaned.isalpha():
            return cleaned.upper()
        return "USD"

class ExtractionService:
    _instance: Optional['ExtractionService'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ExtractionService':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ExtractionService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
            self.model = settings.OLLAMA_MODEL
            self._initialized = True
            
    async def extract(self, text: str) -> ExtractionResult:
        if not text or not text.strip():
            raise ValueError("Input text is empty or contains only whitespace")

        system_prompt = '''You are an expert financial data extraction parser.
Your job is to extract transaction details from unstructured natural language text and return them in structured JSON format.

RULES:
1. Extract the numeric 'amount' as a float.
2. Determine the 'category'. It MUST be one of the following exact strings: "Food/Drink", "Transport", "Rent/Bills", "Shopping", "Leisure", "Other". If the category is ambiguous or doesn't fit, use "Other".
3. Extract the 'concept' (a brief description of what was purchased or the merchant name).
4. Determine the 'currency' and return its standard ISO 3-letter code (e.g., "euros" -> "EUR", "dollars" -> "USD", "pounds" -> "GBP"). If no currency is mentioned, use "USD".

Return ONLY the JSON matching the provided schema.'''

        start_time = time.time()
        
        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': f"Extract transaction details from this text: '{text}'"}
                    ],
                    format=ExtractionResult.model_json_schema(),
                ),
                timeout=10.0
            )
            
            content = response.message.content
            if not content:
                raise ExtractionError("Received empty response from Ollama")
                
            result = ExtractionResult.model_validate_json(content)
            return result
            
        except asyncio.TimeoutError as e:
            logger.error(f"Ollama request timed out: {e}")
            raise ExtractionError("Ollama request timed out after 10.0 seconds")
        except (ollama.ResponseError, ollama.RequestError, ConnectionError, OSError) as e:
            logger.error(f"Ollama connection/API error: {e}")
            raise ExtractionError(f"Failed to communicate with Ollama: {e}")
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Failed to parse extraction result: {e}")
        finally:
            duration = time.time() - start_time
            logger.info(f"[3s Audit] Ollama extraction took {duration:.2f} seconds (model: {self.model})")

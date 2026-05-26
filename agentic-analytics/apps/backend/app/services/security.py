import re
from typing import Any

class PIIMasker:
    """
    Utility for masking Personally Identifiable Information (PII) in strings and dicts.
    """
    
    # Regex for common sensitive data
    CPF_PATTERN = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    
    # Keys in dictionaries that should have their values masked
    SENSITIVE_KEYS = {"cliente_id", "cpf", "email", "telefone", "documento", "password", "senha"}

    @classmethod
    def mask_text(cls, text: str) -> str:
        """Masks sensitive patterns in a plain text string."""
        if not isinstance(text, str):
            return text
            
        text = cls.CPF_PATTERN.sub("XXX.XXX.XXX-XX", text)
        text = cls.EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
        
        # Also mask cliente_id=1234 or similar in raw text
        text = re.sub(r"(cliente_id\s*=\s*['\"]?)\w+(['\"]?)", r"\g<1>XXXX\g<2>", text, flags=re.IGNORECASE)
        
        return text

    @classmethod
    def mask_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively masks sensitive values in a dictionary."""
        masked_data = {}
        for key, value in data.items():
            if isinstance(key, str) and key.lower() in cls.SENSITIVE_KEYS:
                masked_data[key] = "XXXX"
            elif isinstance(value, dict):
                masked_data[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    cls.mask_dict(item) if isinstance(item, dict) else cls.mask_text(str(item)) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, str):
                masked_data[key] = cls.mask_text(value)
            else:
                masked_data[key] = value
        return masked_data

    @classmethod
    def mask_any(cls, data: Any) -> Any:
        """Masks any given data type (dict, list, str)."""
        if isinstance(data, dict):
            return cls.mask_dict(data)
        elif isinstance(data, list):
            return [cls.mask_any(item) for item in data]
        elif isinstance(data, str):
            return cls.mask_text(data)
        return data

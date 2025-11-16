"""
LLM-based OCR service for receipt and product image recognition.
Uses Google Gemini API for image analysis and structured data extraction.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-genai package not installed. Install with: pip install google-genai")


class LLMOCRService:
    """Service for processing receipt/product images using LLM."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OCR service.

        Args:
            api_key: Gemini API key. If not provided, reads from config.secret
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")

        self.api_key = api_key or self._load_api_key()
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please:\n"
                "1. Create secrets/config.secret or config.secret\n"
                "2. Add your API key from https://aistudio.google.com/app/apikey\n"
                "3. Or pass api_key parameter to LLMOCRService()"
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-lite"  # Use gemini-2.5-flash-lite as requested

        # Load prompt template
        self.prompt = self._load_prompt_template()

    def _load_api_key(self) -> Optional[str]:
        """Load API key from config.secret file."""
        # Try multiple locations
        base_path = Path(__file__).parent.parent.parent
        config_paths = [
            base_path / "secrets" / "config.secret",  # secrets/config.secret
            base_path / "config.secret",              # config.secret
        ]

        for config_path in config_paths:
            if not config_path.exists():
                continue

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('GEMINI_API_KEY='):
                            key = line.split('=', 1)[1].strip()
                            # Remove quotes if present
                            key = key.strip('"\'')
                            if key and key != 'your_gemini_api_key_here':
                                return key
            except Exception as e:
                print(f"Error reading {config_path}: {e}")

        return None

    def _load_prompt_template(self) -> str:
        """Load the OCR prompt template."""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "receipt_ocr_prompt.txt"

        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Fallback minimal prompt
        return """
Analyze the receipt/product image and extract items as JSON.

Output format:
{
  "items": [
    {
      "name": "产品名称",
      "category": "类别",
      "quantity": 1.0,
      "unit": "个",
      "location_path": "冰箱 > 冷藏",
      "acquired_date": "2025-01-15",
      "expiry_date": "2025-01-25",
      "notes": "备注"
    }
  ]
}

Output JSON only, no explanations.
"""

    def process_receipt(
        self,
        image_path: str,
        custom_instructions: Optional[str] = None
    ) -> Dict:
        """
        Process a receipt or product image and extract inventory items.

        Args:
            image_path: Path to the image file
            custom_instructions: Optional additional instructions for the LLM

        Returns:
            Dictionary with extracted items or error information
        """
        try:
            # Upload file to Gemini
            uploaded_file = self.client.files.upload(file=image_path)

            # Construct prompt
            prompt_text = self.prompt
            if custom_instructions:
                prompt_text = f"{prompt_text}\n\nAdditional Instructions:\n{custom_instructions}"

            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=[uploaded_file, prompt_text]
            )

            # Parse response
            result = self._parse_response(response.text)

            # Clean up uploaded file (optional, files auto-expire after 48 hours)
            try:
                self.client.files.delete(name=uploaded_file.name)
            except:
                pass  # Ignore cleanup errors

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse LLM response and extract JSON.

        Args:
            response_text: Raw text response from LLM

        Returns:
            Parsed data dictionary
        """
        try:
            # Clean response text
            text = response_text.strip()

            # Remove markdown code blocks if present
            if text.startswith('```'):
                # Find the JSON content between ```json and ```
                lines = text.split('\n')
                json_lines = []
                in_code_block = False

                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not any(line.strip().startswith(x) for x in ['```'])):
                        json_lines.append(line)

                text = '\n'.join(json_lines).strip()

            # Parse JSON
            data = json.loads(text)

            # Validate structure
            if isinstance(data, dict):
                # Check if it's a single item or multiple items
                if "items" in data:
                    items = data["items"]
                elif "name" in data:
                    # Single item, wrap in array
                    items = [data]
                else:
                    return {
                        "success": False,
                        "error": "Invalid response structure",
                        "raw_response": response_text
                    }

                # Validate each item has required fields
                for item in items:
                    if not all(k in item for k in ["name", "category", "location_path"]):
                        return {
                            "success": False,
                            "error": "Missing required fields in item",
                            "raw_response": response_text
                        }

                return {
                    "success": True,
                    "items": items,
                    "count": len(items)
                }

            return {
                "success": False,
                "error": "Response is not a JSON object",
                "raw_response": response_text
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": response_text[:500]  # First 500 chars for debugging
            }

    def batch_process_receipts(
        self,
        image_paths: List[str],
        custom_instructions: Optional[str] = None
    ) -> List[Dict]:
        """
        Process multiple receipt images.

        Args:
            image_paths: List of paths to image files
            custom_instructions: Optional additional instructions

        Returns:
            List of results for each image
        """
        results = []
        for image_path in image_paths:
            result = self.process_receipt(image_path, custom_instructions)
            results.append({
                "image_path": image_path,
                "result": result
            })
        return results


def test_ocr_service():
    """Test function for the OCR service."""
    try:
        service = LLMOCRService()
        print("[OK] OCR Service initialized successfully")
        print(f"Model: {service.model}")
        print(f"API key loaded: {'Yes' if service.api_key else 'No'}")

        # Test with a sample image (if provided)
        import sys
        if len(sys.argv) > 1:
            image_path = sys.argv[1]
            print(f"\nProcessing image: {image_path}")
            result = service.process_receipt(image_path)
            print(f"\nResult:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\nTo test with an image, run:")
            print("   python -m app.services.llm_ocr <image_path>")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ocr_service()

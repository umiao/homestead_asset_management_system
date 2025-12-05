# Receipt OCR Setup Guide

## Overview

PantryPilot now includes AI-powered receipt and product image recognition using Google Gemini API. Simply upload a photo of your receipt or product, and the system will automatically extract items, categories, storage locations, and expiry dates.

## Setup Instructions

### 1. Install Required Package

```bash
pip install google-genai
```

### 2. Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 3. Configure API Key

#### Option A: Using config.secret file (Recommended)

1. Copy the example config file:
   ```bash
   cp config.secret.example config.secret
   ```

2. Open `config.secret` and add your API key:
   ```
   GEMINI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   ```

3. The file is already in `.gitignore` and won't be committed to git

#### Option B: Using Environment Variable

```bash
# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"

# Windows (CMD)
set GEMINI_API_KEY=your_api_key_here
```

### 4. Test the Setup

Run the test script:

```bash
python -m app.services.llm_ocr
```

You should see:
```
✅ OCR Service initialized successfully
📝 Using model: gemini-2.0-flash-exp
🔑 API key loaded: Yes
```

To test with an actual image:
```bash
python -m app.services.llm_ocr path/to/your/receipt.jpg
```

## Usage

### Via Web UI

1. Navigate to the **Import** page
2. Find the "Smart Receipt Scanner (AI-Powered)" section at the top
3. Click "Upload Receipt or Product Photo"
4. Select an image file (JPG, PNG, WEBP)
5. Check "Automatically add items to inventory" if you want auto-import
6. Click "Scan & Extract Items"
7. View recognized items in the results table

### Via API

**Upload and Process Receipt:**
```bash
curl -X POST "http://localhost:8000/api/receipt/upload?auto_import=true" \
  -F "file=@/path/to/receipt.jpg"
```

**Check OCR Service Status:**
```bash
curl http://localhost:8000/api/receipt/status
```

**View Upload History:**
```bash
curl http://localhost:8000/api/receipt/history
```

## Supported Image Formats

- JPEG/JPG
- PNG
- WEBP
- HEIC/HEIF (iOS photos)

## What Gets Extracted

The AI analyzes the image and extracts:

- **Name (名称)**: Product name in Chinese when possible
- **Category (类别)**: Inferred category (食物, 饮料, 日用品, etc.)
- **Quantity (数量)**: Amount extracted from receipt
- **Unit (单位)**: Appropriate unit (个, 瓶, kg, etc.)
- **Location Path (存储位置)**: Recommended storage location
  - Example: `冰箱 > 冷藏` (Refrigerator > Chilled)
- **Acquired Date (购买日期)**: From receipt or current date
- **Expiry Date (过期日期)**: From packaging or estimated based on category
- **Notes (备注)**: Store name, brand, special attributes

## Customizing the Prompt

The OCR behavior is controlled by a prompt template in:
```
prompts/receipt_ocr_prompt.txt
```

You can edit this file to:
- Change output language preferences
- Adjust category mappings
- Modify shelf-life estimations
- Add custom instructions

After editing, restart the server for changes to take effect.

## Troubleshooting

### "OCR service not available"

**Solution**: Install the package:
```bash
pip install google-genai
```

### "Gemini API key not found"

**Solutions**:
1. Check `config.secret` exists and contains valid key
2. Verify key format (should be a long string like `AIza...`)
3. Ensure you copied the key correctly without extra spaces
4. Check that `config.secret` is in the project root directory

### "Failed to parse JSON"

**Possible causes**:
- Poor image quality (try taking a clearer photo)
- Receipt is too blurry or dark
- Text is not readable

**Solutions**:
- Use well-lit, high-resolution photos
- Keep receipt flat and in focus
- Try different angles or lighting

### "HTTP error 429"

**Cause**: API rate limit exceeded

**Solution**: Wait a moment and try again. Free tier has usage limits.

## API Rate Limits (Free Tier)

- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per month

For production use, consider:
- Upgrading to paid tier
- Implementing request queuing
- Caching results

## Example Output

**Input**: Receipt from Costco with milk, eggs, bread

**Output JSON**:
```json
{
  "success": true,
  "ocr_result": {
    "items_found": 3,
    "items": [
      {
        "name": "有机牛奶",
        "category": "乳制品",
        "quantity": 2.0,
        "unit": "加仑",
        "location_path": "冰箱 > 冷藏",
        "acquired_date": "2025-01-15",
        "expiry_date": "2025-01-25",
        "notes": "Costco购入，有机低脂"
      },
      {
        "name": "鸡蛋",
        "category": "乳制品",
        "quantity": 18.0,
        "unit": "个",
        "location_path": "冰箱 > 冷藏",
        "acquired_date": "2025-01-15",
        "expiry_date": "2025-02-05",
        "notes": "Costco购入"
      },
      {
        "name": "全麦面包",
        "category": "烘焙食品",
        "quantity": 1.0,
        "unit": "个",
        "location_path": "厨房 > 橱柜",
        "acquired_date": "2025-01-15",
        "expiry_date": "2025-01-20",
        "notes": "Costco购入"
      }
    ]
  },
  "import_results": {
    "auto_import": true,
    "total": 3,
    "successful": 3,
    "failed": 0
  }
}
```

## Security Notes

- ⚠️ **Never commit** `config.secret` to git
- ✅ `config.secret` is already in `.gitignore`
- ✅ Uploaded receipts are stored locally in `data/receipts/`
- ✅ Files are named with timestamps and random IDs
- ⚠️ Be aware that images are temporarily uploaded to Google's servers for processing
- ℹ️ Google automatically deletes uploaded files after 48 hours

## File Storage

Receipt images are stored in:
```
data/receipts/receipt_YYYYMMDD_HHMMSS_<uuid>.jpg
```

This directory is also in `.gitignore` and won't be committed.

## Advanced Usage

### Batch Processing Multiple Receipts

```python
from app.services.llm_ocr import LLMOCRService

service = LLMOCRService()

image_paths = [
    "receipt1.jpg",
    "receipt2.jpg",
    "receipt3.jpg"
]

results = service.batch_process_receipts(image_paths)

for result in results:
    print(f"Processed: {result['image_path']}")
    if result['result']['success']:
        print(f"  Items found: {result['result']['count']}")
```

### Custom Instructions

```python
service = LLMOCRService()

custom_instructions = """
优先识别中文品牌名称
所有食品默认存放位置：冰箱 > 冷藏
"""

result = service.process_receipt(
    "receipt.jpg",
    custom_instructions=custom_instructions
)
```

## Support

For issues, feature requests, or questions:
1. Check the troubleshooting section above
2. Review `prompts/receipt_ocr_prompt.txt` for customization options
3. Test with `python -m app.services.llm_ocr <image_path>`
4. Check API logs for detailed error messages

## Model Information

- **Model**: Google Gemini 2.0 Flash (Experimental)
- **Capabilities**: Vision, OCR, structured output
- **Languages**: Multilingual (优先中文输出)
- **Context**: Up to 1M tokens
- **Speed**: ~2-5 seconds per receipt

---

**Ready to scan receipts?** Start the server and visit the Import page!

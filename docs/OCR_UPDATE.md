# OCR Feature Update - Setup Guide

## Changes Made

### 1. Fixed API Key Path
- ✅ Now supports `secrets/config.secret` (your current location)
- ✅ Also supports `config.secret` (root directory)

### 2. Changed Model
- ✅ Updated to use `gemini-2.0-flash-exp` (most current available model)
- Note: `gemini-2.0-flash-lite` is not yet available in the API

### 3. Added Edit Interface
- ✅ After OCR recognition, shows edit modal instead of auto-importing
- ✅ Allows reviewing and editing all recognized items
- ✅ Can remove unwanted items
- ✅ Can modify any field (name, category, quantity, location, dates, notes)
- ✅ Import only after manual confirmation

## Installation Complete ✓

The Google Gemini AI package has been installed successfully:

```bash
✓ google-genai package installed
✓ Server automatically reloaded
✓ OCR Service is ready to use
```

## How to Use

### 1. Upload Receipt
1. Go to **Import** page
2. Click "Upload Receipt or Product Photo"
3. Select an image file
4. Click "Scan & Extract Items"

### 2. Review & Edit
After recognition:
- A modal will pop up showing all recognized items
- Each item displays in a card with editable fields
- You can:
  - ✏️ Edit any field (name, category, quantity, etc.)
  - 🗑️ Remove unwanted items
  - ✅ Review before importing

### 3. Import
- Click "Import All Items" to add to inventory
- Or click "Cancel" to discard

## Workflow

```
Upload Image
    ↓
AI Recognition (3-5 seconds)
    ↓
Edit Modal Opens
    ↓
Review & Edit Items
    ↓
Import All or Cancel
```

## Features

### Editable Fields
- **Name** - Product name (required)
- **Category** - Item category (required)
- **Quantity** - Amount
- **Unit** - Measurement unit
- **Location** - Storage location (required)
- **Acquired Date** - Purchase date
- **Expiry Date** - Expiration date
- **Notes** - Additional info

### Actions
- **Edit** - Modify any field inline
- **Remove** - Delete specific items before import
- **Cancel** - Discard all changes
- **Import All** - Add all items to inventory

## Troubleshooting

### "OCR Service Not Available"

**Solution**: Install the package
```bash
pip install google-genai
```

### "undefined" Error

This was a display issue that's now fixed. Your API key is correctly located in `secrets/config.secret` and should work after installing the package.

### After Installing google-genai

1. Restart the server:
   ```bash
   # Stop current server (Ctrl+C)
   python run.py
   ```

2. Visit the Import page

3. Click "Check OCR Service Status" button - should show:
   ```
   ✅ OCR Service Ready
   Model: gemini-2.0-flash-exp
   API Key: Configured ✓
   ```

## Example

**Input**: Photo of Costco receipt with 3 items

**After Recognition**:
```
Edit Modal Opens with:

Item 1:
  Name: 有机牛奶
  Category: 乳制品
  Quantity: 2
  Unit: 瓶
  Location: 冰箱 > 冷藏
  Acquired: 2025-01-16
  Expiry: 2025-01-26
  Notes: Costco购入

[Edit] [Remove]

Item 2: ...
Item 3: ...

[Cancel] [Import All Items]
```

**After Editing & Importing**:
- All items added to inventory
- Success message shown
- Can view in Inventory page

## Tips

1. **Review Before Import** - Always check AI recognition results
2. **Fix Categories** - AI guesses categories, verify they're correct
3. **Adjust Dates** - Expiry dates are estimates, update as needed
4. **Location Paths** - Edit to match your actual storage organization
5. **Remove Duplicates** - Delete items already in inventory

## Next Steps

After installation:
1. Test with a sample receipt image
2. Review the recognized items
3. Edit as needed
4. Import to inventory
5. Check Inventory page to confirm

---

**Ready to try?**
1. `pip install google-genai`
2. Restart server
3. Upload a receipt!

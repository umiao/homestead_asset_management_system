"""
Fix TSV File Encoding to UTF-8

This script ensures your TSV file is properly encoded as UTF-8.
Run this if you see question marks instead of Chinese characters.
"""
import sys
from pathlib import Path

def detect_and_fix_encoding(file_path):
    """Detect encoding and convert to UTF-8 if needed."""
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'cp1252', 'latin1']

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False

    # Try to read with different encodings
    content = None
    detected_encoding = None

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                detected_encoding = encoding
                print(f"[OK] Successfully read file with encoding: {encoding}")
                break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        print("[ERROR] Could not read file with any known encoding")
        return False

    # Check if already UTF-8
    if detected_encoding == 'utf-8':
        print("[OK] File is already UTF-8 encoded")
        # Verify by trying to read it
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                test = f.read()
            print("[OK] UTF-8 encoding verified")
            return True
        except:
            pass

    # Save as UTF-8
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    print(f"\nCreating backup: {backup_path}")

    try:
        # Create backup
        import shutil
        shutil.copy2(file_path, backup_path)

        # Write as UTF-8
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)

        print(f"[OK] Converted from {detected_encoding} to UTF-8")
        print(f"[OK] Backup saved as: {backup_path}")
        print(f"[OK] Original file updated: {file_path}")

        # Verify the conversion
        with open(file_path, 'r', encoding='utf-8') as f:
            verify = f.read()
            if verify == content:
                print("[OK] Conversion verified successfully")
                return True
            else:
                print("[WARN] Warning: File content changed during conversion")
                return False

    except Exception as e:
        print(f"[ERROR] Error during conversion: {e}")
        return False


def show_preview(file_path, lines=5):
    """Show first few lines of the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            print(f"\nPreview of {file_path}:")
            print("-" * 60)
            for i, line in enumerate(f, 1):
                if i > lines:
                    break
                print(f"{i}: {line.rstrip()}")
            print("-" * 60)
    except Exception as e:
        print(f"Could not preview file: {e}")


if __name__ == "__main__":
    # Default file path
    default_path = "src/sample_asset_data.tsv"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_path

    print("=" * 60)
    print("PantryPilot - TSV Encoding Fixer")
    print("=" * 60)
    print(f"\nProcessing: {file_path}\n")

    success = detect_and_fix_encoding(file_path)

    if success:
        show_preview(file_path)
        print("\n[OK] File is ready for import!")
        print("\nNext steps:")
        print("1. python run.py")
        print("2. Visit http://localhost:8000/import")
        print("3. Click 'Import Sample Data Now'")
    else:
        print("\n[ERROR] Failed to fix encoding")
        print("Please check the file manually or contact support")


import os

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Remove BOM if present
    if text.startswith('\ufeff'):
        text = text[1:]
    
    # Now try the recovery
    try:
        recovered_bytes = text.encode('latin-1')
        recovered_text = recovered_bytes.decode('utf-8')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(recovered_text)
        print("SUCCESS: Byte-level recovery successful after removing BOM.")
    except Exception as e:
        print(f"FAILED recovery: {e}")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")

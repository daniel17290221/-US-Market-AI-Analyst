
import os

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

try:
    # Read the file as UTF-8 (this gives us the corrupted 'ë¯¸êµ­' string)
    with open(path, 'r', encoding='utf-8') as f:
        corrupted_text = f.read()
    
    # Logic: corrupted_text contains characters that are actually the bytes of the original UTF-8
    # We map them back to bytes using latin-1 (which is a 1-to-1 mapping for the first 256 chars)
    # and then decode those bytes as UTF-8.
    
    try:
        # Some characters might not be in latin-1 if the corruption was even weirder,
        # but usually this 'latin-1' -> 'utf-8' trick fixes "Double UTF-8" or Mojibake.
        recovered_bytes = corrupted_text.encode('latin-1')
        recovered_text = recovered_bytes.decode('utf-8')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(recovered_text)
        print("SUCCESS: Byte-level UTF-8 recovery successful.")
    except Exception as e:
        print(f"FAILED byte-level recovery: {e}")
        print("Falling back to aggressive regex replacement.")
        # If the above fails, it means some chars were already destroyed or wasn't simple mojibake.
        # I will use a known clean block if possible.
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")

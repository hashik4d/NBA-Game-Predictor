
try:
    import nbainjuries
    print("Library imported successfully!")
    
    # Check for available methods
    print(dir(nbainjuries))
    
    # Try typical fetch
    # Note: I need to guess the exact API or read docs, but usually they have a simple 'get_injuries'
    # Based on PyPI, it might be 'get_injuries' or similar.
    # Let's try to inspect it first.
except Exception as e:
    print(f"Import failed: {e}")

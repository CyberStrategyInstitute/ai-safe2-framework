# ... inside scan() ...
    
    # Run scan
    # FIX: Import from local module structure
    from .scanner import StaticScanner 
    
    scanner = StaticScanner(config_path=config)
    result = scanner.scan_project(path)

    # Determine Failure
    def should_fail(res, tier):
        # Strict failure logic
        if tier == "Tier3" and res.score < 90: return True
        if tier == "Tier2" and res.score < 70: return True
        if tier == "Tier1" and res.score < 50: return True
        return False

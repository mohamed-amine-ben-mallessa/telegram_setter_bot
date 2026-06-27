def route_lead(score: int, config: dict) -> tuple[str, str]:
    """
    Route a lead based on their score.
    Returns (status, next_action).
    """
    scoring = config.get("scoring", {})
    routing = config.get("routing", {})

    if scoring:
        if score >= scoring.get("book_call_threshold", 80):
            return "book_call", "handoff_to_trader"
        if score >= scoring.get("qualified_threshold", 70):
            return "qualified", "propose_trial"
        if score <= scoring.get("disqualify_threshold", 30):
            return "not_qualified", "close_lost"

    # Default routing by state machine
    # Default to follow_up for medium scores
    return "engaged", "continue_qualification"
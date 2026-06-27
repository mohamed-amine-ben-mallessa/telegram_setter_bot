import re

def score_lead(text: str, cfg: dict) -> tuple[int, list[str]]:
    """
    Score a lead based on keywords in their message (trading signals context).
    Returns (score_delta, tags).
    """
    t = text.lower()
    score = 0
    tags = []

    weights = cfg.get("weights", {})
    rules = cfg.get("scoring_rules", {})

    # ─── Experience ───
    experience_rules = rules.get("experience_bonus", {})
    for word, pts in experience_rules.items():
        if word in t:
            score += pts
            tags.append("has_experience")
            break

    # ─── Budget (tous formats) ───
    # Détecte : "200€", "200 €", "200e", "200 euros", "200 balles", "200$", etc.
    budget_patterns = [
        r'(\d+)\s*euros?\b',        # 200€, 200 euros
        r'(\d+)\s*balles?\b',       # 150 balles
        r'(\d+)\s*\$',              # 200 $
        r'(\d+)\$',                 # 200$ (sans espace)
        r'(\d+)\s*bucks?\b',        # 200 bucks
        r'(\d+)\s*par\s*mois',      # 200 par mois
    ]
    
    # Détection spéciale pour € sans espace : pattern number + €
    # On cherche "200" suivi de "€" (avec ou sans espace)
    euro_match = re.search(r'(\d+)\s*[€\u20ac]', t)
    if euro_match:
        budget_patterns.insert(0, r'(\d+)\s*[€\u20ac]')  # Priorité haute

    budget_found = False
    for pattern in budget_patterns:
        matches = re.findall(pattern, t)
        for amount_str in matches:
            try:
                amount = int(amount_str)
            except ValueError:
                continue
            budget_found = True
            if amount >= 500:
                score += weights.get("budget", 25)
                tags.append("budget_vip")
            elif amount >= 150:
                score += weights.get("budget", 25)
                tags.append("high_budget")
            elif amount >= 50:
                score += 15
                tags.append("mid_budget")
            elif amount >= 20:
                score += 10
                tags.append("low_budget")
            break
        if budget_found:
            break

    # Si le mot "budget" est mentionné sans montant
    if not budget_found and any(w in t for w in ["budget", "prix", "tarif", "combien", "coût", "abonnement", "c'est quoi le prix"]):
        score += 8
        tags.append("asked_budget")

    # ─── Urgency ───
    urgency_hot = rules.get("urgency_hot", [])
    urgency_warm = rules.get("urgency_warm", [])
    urgency_cold = rules.get("urgency_cold", [])

    # Vérifier chaque mot du texte individually pour éviter les faux positifs
    words = set(t.split())

    if any(w in words for w in urgency_hot) or any(w in t for w in urgency_hot):
        score += weights.get("urgency", 20)
        tags.append("urgent")
    elif any(w in t for w in urgency_warm):
        score += 10
        tags.append("soon")
    
    if any(w in t for w in urgency_cold):
        score -= 10
        tags.append("not_urgent")

    # ─── Market detection ───
    market_rules = rules.get("markets", {})
    known_markets = set()
    for market, keywords in market_rules.items():
        if any(w in t for w in keywords):
            known_markets.add(market)
    if known_markets:
        score += weights.get("knowledge", 10)
        tags.extend([f"market_{m}" for m in known_markets])

    # ─── High interest / intent ───
    high_interest = rules.get("high_interest", [])
    if any(w in t for w in high_interest):
        score += weights.get("interest", 20)
        tags.append("high_interest")

    # ─── Referral ───
    referral = rules.get("referral", [])
    if any(w in t for w in referral):
        score += weights.get("referral", 10)
        tags.append("referral")

    # ─── Negative / disinterest ───
    negative = rules.get("negative", [])
    if any(w in t for w in negative):
        score -= 50
        tags.append("negative")

    # Scam alert (additional penalty)
    if any(w in t for w in ["arnaque", "scam", "faux", "piège"]):
        score -= 30
        tags.append("scam_alert")

    return score, tags
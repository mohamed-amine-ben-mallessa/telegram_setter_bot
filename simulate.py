#!/usr/bin/env python3
"""
Simulation du bot Trading Setter avec le nouveau tunnel.
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import load_yaml
from app.services.scoring import score_lead

# Charger les configs
scoring_cfg = load_yaml("scoring.yaml")
tunnel_raw = load_yaml("tunnel.yaml")

# scoring_rules est au top-level du YAML (PAS dans tunnel:)
scoring_rules = tunnel_raw.get("scoring_rules", {})

# Le scoring utilise weights de scoring.yaml + rules détaillées du tunnel.yaml
scoring_full = {
    "weights": scoring_cfg.get("scoring", {}).get("weights", {}),
    "scoring_rules": scoring_rules,
    "thresholds": tunnel_raw.get("thresholds", {}),
}

configs = {
    "scoring": scoring_cfg.get("scoring", {}),
    "scoring_rules": scoring_full,
    "tunnel": {
        "legends": tunnel_raw.get("legends", {}),
        "urls": tunnel_raw.get("urls", {}),
        "scripts": tunnel_raw.get("scripts", {}),
        "thresholds": tunnel_raw.get("thresholds", {}),
    },
}

# Messages de test
TEST_MESSAGES = [
    ("Lead chaud — crypto + budget 200€ + urgent", 
     "Salut, je cherche des signaux crypto, j'ai 200€ de budget par mois, je veux commencer cette semaine"),

    ("Lead froid — pas intéressé",
     "Non merci pas intéressé"),

    ("Lead tiède — débutant qui se renseigne",
     "Bonjour je suis débutant en trading, je voudrais des infos, c'est combien ?"),

    ("Lead brûlant — recommandé + 500€ + urgent",
     "Salut c'est un ami qui m'a parlé de vous. J'ai 500€ de budget pour des signaux forex, je veux commencer maintenant"),

    ("Lead négatif — arnaque",
     "C'est une arnaque votre truc"),

    ("Lead tiède — plus tard",
     "Salut je me renseigne pour plus tard, c'est quoi vos tarifs ?"),

    ("Test budget en euros — 150 balles",
     "Yo je cherche des signaux pour le bitcoin j'ai 150 balles à mettre par mois"),

    ("Test budget $ — 300$",
     "I'm interested in trading signals, I have 300$ per month budget"),

    ("Test avec $ et urgent — 400$ maintenant",
     "I need good trading signals, I have 400$ budget, I want to start now"),

    ("Test referral + budget — ami m'a parlé + 200€",
     "Salut c'est mon pote qui m'a donné ton contact. J'ai 200 euros de budget pour des signaux actions, on commence quand ?"),

    ("Test long — complet",
     "Bonjour, je m'appelle Pierre, je trade depuis 2 ans sur crypto et forex. J'ai un budget de 300€ par mois et je veux un package complet. Je peux décider seul. C'est urgent car le marché est favorable maintenant. Est-ce que vous avez un essai ?"),

    ("Test spam",
     "Bonjour, Cliquez ici pour des gains garantis !!! Profitez de notre offre exclusive maintenant !!!"),
]

def classify_stage(score: int, cfg: dict) -> dict:
    """Détermine l'étape du tunnel selon le score."""
    thresholds = cfg.get("thresholds", {})
    cold = thresholds.get("cold_to_warm", 30)
    warm = thresholds.get("warm_to_hot", 70)
    hot = thresholds.get("hot_to_booked", 85)

    if score >= hot:
        return {"stage": "hot", "emoji": "🔥🔥", "label": "Brûlant", "forward": True}
    elif score >= warm:
        return {"stage": "warm", "emoji": "🔥", "label": "Chaud", "forward": True}
    elif score >= cold:
        return {"stage": "engaged", "emoji": "💬", "label": "Engagé", "forward": False}
    else:
        return {"stage": "cold", "emoji": "❄️", "label": "Froid", "forward": False}

def format_tunnel_info(tags: list, tunnel: dict) -> dict:
    """Extraire les infos du tunnel depuis les tags."""
    info = {
        "experience": None,
        "budget": None,
        "market": None,
        "urgency": None,
        "source": None,
    }

    legends = tunnel.get("legends", {})

    for tag in tags:
        if tag == "has_experience":
            info["experience"] = "🌱 Débutant+"
        elif tag == "budget_vip":
            info["budget"] = legends.get("budget", {}).get("vip", "👑 VIP")
        elif tag == "high_budget":
            info["budget"] = legends.get("budget", {}).get("high", "💎 High")
        elif tag == "mid_budget":
            info["budget"] = legends.get("budget", {}).get("medium", "💰 Medium")
        elif tag == "low_budget":
            info["budget"] = legends.get("budget", {}).get("low", "💸 Low")
        elif tag.startswith("market_"):
            market = tag.replace("market_", "")
            market_labels = legends.get("market", {})
            info["market"] = market_labels.get(market, f"📊 {market}")
        elif tag == "urgent":
            info["urgency"] = "🔥🔥 Maintenant"
        elif tag == "soon":
            info["urgency"] = "🔥 Bientôt"
        elif tag == "not_urgent":
            info["urgency"] = "❄️ Plus tard"
        elif tag == "referral":
            info["source"] = "👥 Recommandé"

    return info

def get_script(stage: str, scripts: dict) -> str:
    """Récupère le script approprié selon l'étape."""
    script_map = {
        "hot": scripts.get("propose_booking", ["Je te mets en contact avec notre trader."]),
        "warm": scripts.get("propose_trial", ["On propose un essai 7 jours à 1€."]),
        "engaged": scripts.get("qualify_budget", ["Tu as un budget mensuel pour les signaux ?"]),
        "cold": scripts.get("close_lost", ["Pas de souci, à bientôt !"]),
    }
    return script_map.get(stage, ["Salut !"])[0]

def get_urls(info: dict, urls: dict) -> dict:
    """Génère les URLs formatées pour ce lead."""
    formatted = {}
    for key, url in urls.items():
        formatted[f"url_{key}"] = url
    return formatted

def simulate():
    tunnel = configs["tunnel"]
    legends = tunnel.get("legends", {})
    urls = tunnel.get("urls", {})
    scripts = tunnel.get("scripts", {})

    print("=" * 75)
    print("🧪 SIMULATION BOT TRADING SETTER — TUNNEL DE VENTE")
    print(f"{'=' * 75}")
    print(f"📊 Seuil cold→warm: {tunnel.get('thresholds', {}).get('cold_to_warm', 30)}")
    print(f"📊 Seuil warm→hot: {tunnel.get('thresholds', {}).get('warm_to_hot', 70)}")
    print(f"📊 Seuil hot→booked: {tunnel.get('thresholds', {}).get('hot_to_booked', 85)}")
    print(f"🔗 URLs configurées: {len(urls)} placeholders")
    print("=" * 75)

    for i, (title, msg) in enumerate(TEST_MESSAGES, 1):
        score_delta, tags = score_lead(msg, configs["scoring_rules"])
        stage_info = classify_stage(score_delta, configs["scoring_rules"])
        lead_info = format_tunnel_info(tags, tunnel)
        script = get_script(stage_info["stage"], scripts)
        formatted_urls = get_urls(lead_info, urls)

        # Remplacer les placeholders dans le script
        for key, url in formatted_urls.items():
            script = script.replace(f"{{{key}}}", url)

        print(f"\n{'─' * 75}")
        print(f"📩 TEST #{i} : {title}")
        print(f"{'─' * 75}")

        # Score
        sign = "+" if score_delta >= 0 else ""
        print(f"   📊 Score : {sign}{score_delta}")

        # Tags
        tag_str = ", ".join(tags) if tags else "aucun"
        print(f"   🏷️ Tags  : {tag_str}")

        # Stage tunnel
        stage_emoji = stage_info["emoji"]
        stage_label = stage_info["label"]
        print(f"   🚦 Stage : {stage_emoji} {stage_label}")

        # Info lead
        if any(lead_info.values()):
            print(f"   📋 Profil:")
            if lead_info["budget"]:
                print(f"      💰 Budget  : {lead_info['budget']}")
            if lead_info["market"]:
                print(f"      🪙 Market : {lead_info['market']}")
            if lead_info["experience"]:
                print(f"      📈 Level  : {lead_info['experience']}")
            if lead_info["urgency"]:
                print(f"      ⏰ Urgence: {lead_info['urgency']}")
            if lead_info["source"]:
                print(f"      👥 Source : {lead_info['source']}")

        # Forward ?
        if stage_info["forward"]:
            print(f"   🔥 FORWARD → Canal test (score {sign}{score_delta} ≥ seuil)")
        else:
            print(f"   ⏳ Pas de forward (score {sign}{score_delta} < seuil)")

        # Prix suggéré
        if lead_info["budget"]:
            if "VIP" in lead_info["budget"]:
                print(f"   💎 Prix suggéré : VIP (199€/mois)")
            elif "High" in lead_info["budget"]:
                print(f"   💎 Prix suggéré : Full Markets (99€/mois)")
            elif "Medium" in lead_info["budget"]:
                print(f"   💰 Prix suggéré : Crypto Only (49€/mois)")

        # Script de réponse
        print(f"\n   💬 Bot répond : \"{script}\"")

        # URLs utilisées (si présentes dans le script)
        used_urls = [k for k in formatted_urls if k.replace("url_", "") in script.lower()]
        if used_urls:
            print(f"   🔗 URLs utilisées :")
            for k in used_urls:
                print(f"      • {k}: {formatted_urls[k]}")

    print(f"\n{'=' * 75}")
    print("✅ Simulation terminée")
    print("=" * 75)

if __name__ == "__main__":
    simulate()
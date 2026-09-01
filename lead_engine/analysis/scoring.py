"""
Deterministic lead scoring, following the exact point system:

    +10 = Genuine business identified
    +10 = Reliable business contact information available
    +25 = No website
    +20 = Significant website opportunity
    +10 = Poor mobile experience
    +10 = Significant SEO opportunity
    +5  = Weak digital presence
    +5  = No obvious WhatsApp/contact conversion option
    +5  = Strong fit with requested KTZ service

Priority bands:
    85–100 = HOT
    70–84  = HIGH
    55–69  = MEDIUM
    Below 55 = LOW

This is deterministic, not an LLM judgment call — same inputs always
produce the same score, and no points are awarded without real evidence.
"""

RECOMMENDED_SERVICES = [
    "New Website", "Website Redesign", "SEO", "Digital Marketing",
    "Social Media Marketing", "Branding", "Graphic Design", "Mobile App",
    "Custom Software", "Automation", "Multiple Services", "No Clear Opportunity",
]


def score_lead(record: dict, website_analysis: dict) -> dict:
    """
    Score a lead (already merged/classified record + website analysis dict).
    Returns dict with lead_score, lead_priority, recommended_service,
    opportunity_reason, data_confidence.
    """
    score = 0
    reasons = []
    services_needed = []

    # +10 genuine business identified — true for anything that survived
    # verify.py's operational-status filter and dedup.
    score += 10

    # +10 reliable contact info available
    has_phone = bool(record.get("phone"))
    if has_phone:
        score += 10
        reasons.append("has a phone number on file")

    has_website = bool(record.get("website"))
    website_quality = website_analysis.get("website_quality")
    mobile_friendly = website_analysis.get("mobile_friendly")
    seo_opportunity = website_analysis.get("seo_opportunity", "")
    contact_options = website_analysis.get("contact_options", "")
    whatsapp = website_analysis.get("whatsapp")
    has_social = any(
        website_analysis.get(p, "Not Found") != "Not Found"
        for p in ("facebook", "instagram", "linkedin")
    )

    if not has_website:
        # +25 no website
        score += 25
        reasons.append("no website found")
        services_needed.append("New Website")
    else:
        # +20 significant website opportunity — only when we actually have
        # evidence of a real problem, not just because a website exists.
        significant_opportunity = website_quality == "Poor"
        if significant_opportunity:
            score += 20
            reasons.append("website has significant quality issues")
            services_needed.append("Website Redesign")

        # +10 poor mobile experience — only on an actual, checked signal
        if mobile_friendly is False:
            score += 10
            reasons.append("website is not mobile-friendly")
            if "Website Redesign" not in services_needed:
                services_needed.append("Website Redesign")

        # +10 significant SEO opportunity
        if isinstance(seo_opportunity, str) and seo_opportunity.startswith("High"):
            score += 10
            reasons.append("significant SEO gaps (missing title/meta description)")
            services_needed.append("SEO")

    # +5 weak digital presence — no social media links found anywhere
    if not has_social:
        score += 5
        reasons.append("no social media presence found")
        services_needed.append("Social Media Marketing")

    # +5 no obvious WhatsApp/contact conversion option
    no_conversion_option = (not whatsapp) and (contact_options in ("None found", "Unable to determine"))
    if no_conversion_option:
        score += 5
        reasons.append("no clear contact/conversion option found")

    # +5 strong fit with requested KTZ service — true by construction, since
    # this business was found via a category search KTZ is targeting.
    score += 5

    score = min(score, 100)

    if score >= 85:
        priority = "HOT"
    elif score >= 70:
        priority = "HIGH"
    elif score >= 55:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    if len(services_needed) >= 2:
        recommended_service = "Multiple Services"
    elif len(services_needed) == 1:
        recommended_service = services_needed[0]
    else:
        recommended_service = "No Clear Opportunity"

    opportunity_reason = (
        "; ".join(reasons).capitalize() + "."
        if reasons else "No significant opportunity signals found in available data."
    )

    # Confidence reflects how much real evidence we actually had, not the score itself
    if not has_website:
        data_confidence = "Medium — no website to analyze, based on directory data only"
    elif website_quality == "Unable to determine":
        data_confidence = "Low — website could not be reached or analyzed"
    else:
        data_confidence = "High — website content directly analyzed"

    return {
        "lead_score": score,
        "lead_priority": priority,
        "recommended_service": recommended_service,
        "opportunity_reason": opportunity_reason,
        "data_confidence": data_confidence,
    }

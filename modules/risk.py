def get_risk_level(prob, threshold):
    """HIGH = model says fraud. MEDIUM = a bit suspicious. LOW = normal."""
    if prob >= threshold:
        return 'HIGH'
    if prob >= 0.30:
        return 'MEDIUM'
    return 'LOW'
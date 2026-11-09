"""Equipment association separates visible objects, policy and human findings.

No inferred absence, safety rating or identity. Detection outputs alone cannot
satisfy protective-rating requirements; all deployment gates remain closed.
"""

from .ppe import iou

# Appearance label -> requirement, allowed vertical region of person box.
REGIONS = {
    "hard_hat": ("hard_hat", 0.0, 0.38),
    "high_visibility_vest": ("high_visibility_vest", 0.18, 0.78),
    "ordinary_eyewear": ("safety_goggles", 0.0, 0.32),
    "ordinary_footwear": ("protective_footwear", 0.65, 1.0),
    "gloves": ("protective_gloves", 0.15, 0.95),
    "face_shield": ("face_shield", 0.0, 0.4),
    "earmuffs": ("hearing_protection", 0.0, 0.38),
    "medical_mask": ("respiratory_protection", 0.0, 0.4),
}
CATEGORIES = {item[0] for item in REGIONS.values()}


def assess_people(boxes, required, *, threshold=0.5):
    if not set(required) <= CATEGORIES:
        raise ValueError("Unsupported requirement")
    people = [b for b in boxes if b.label == "person" and b.score >= threshold]
    assigned = [{} for _ in people]
    ambiguous = [set() for _ in people]
    for item in boxes:
        if item.label not in REGIONS or item.score < threshold:
            continue
        category, lo, hi = REGIONS[item.label]
        cx = (item.xyxy[0] + item.xyxy[2]) / 2
        cy = (item.xyxy[1] + item.xyxy[3]) / 2
        candidates = []
        for i, p in enumerate(people):
            x, y, q, z = p.xyxy
            if x <= cx <= q and y + lo * (z - y) <= cy <= y + hi * (z - y):
                candidates.append((abs(cx - (x + q) / 2) / (q - x), i))
        candidates.sort()
        if len(candidates) > 1 and candidates[1][0] - candidates[0][0] < 0.15:
            for _, i in candidates:
                ambiguous[i].add(category)
        elif candidates:
            i = candidates[0][1]
            if item.score > assigned[i].get(category, {}).get("score", -1):
                assigned[i][category] = {
                    "appearance_label": item.label,
                    "score": item.score,
                    "box": item.xyxy,
                }
    result = []
    for i, p in enumerate(people):
        statuses = {}
        for category in sorted(CATEGORIES):
            observed = assigned[i].get(category)
            statuses[category] = {
                "state": "unknown" if category in required else "not_required",
                "observed_object": observed,
                "association_ambiguous": category in ambiguous[i],
                "reason": "Deployment validation gate closed; appearance is not protective rating."
                if observed
                else "No assessable observation; absence is unconfirmed.",
            }
        result.append(
            {
                "person_index": i,
                "person_box": p.xyxy,
                "requirements": statuses,
                "requires_human_review": bool(required),
                "source": "object_appearance_not_human_confirmation",
            }
        )
    return result


def evaluate_associations(predictions, labels):
    """Exact links require independent person IDs and assessability annotations.

    Never infer association ground truth from spatial proximity or object AP.
    """
    if labels is None:
        return {
            "accuracy": None,
            "evaluated_links": 0,
            "reason": "Independent wearer relationships unavailable",
        }
    if not labels:
        return {"accuracy": None, "evaluated_links": 0, "reason": "No labeled links"}
    correct = sum(
        predictions.get(item["equipment_id"]) == item["person_id"] for item in labels
    )
    return {"accuracy": correct / len(labels), "evaluated_links": len(labels)}

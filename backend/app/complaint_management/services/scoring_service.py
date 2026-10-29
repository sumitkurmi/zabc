# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Technician leaderboard scoring formulas (plain average vs Bayesian weighted score).

from typing import Optional
from backend.app.config import settings


def compute_technician_score(
    avg_rating: Optional[float],
    rating_count: int,
    resolved_count: int
) -> float:
    """Computes leaderboard score for a technician based on configured formula.

    Formula options controlled by SCORE_FORMULA setting:
    - 'average' (DEFAULT): Plain arithmetic average rating.
    - 'weighted': Bayesian average balancing sample size with prior score.

    Args:
        avg_rating: Average rating float (1.0 to 5.0) or None if unrated.
        rating_count: Total number of ratings received.
        resolved_count: Total complaints resolved by technician.

    Returns:
        Calculated score float rounded to 2 decimal places.
    """
    formula = getattr(settings, "SCORE_FORMULA", "average").lower()

    if formula == "weighted":
        prior_mean = float(getattr(settings, "SCORE_PRIOR_MEAN", 3.5))
        prior_count = float(getattr(settings, "SCORE_PRIOR_COUNT", 5))

        sum_of_ratings = (avg_rating or 0.0) * rating_count
        weighted_score = (prior_mean * prior_count + sum_of_ratings) / (prior_count + rating_count)
        return round(weighted_score, 2)

    # Default 'average' formula
    if not avg_rating or rating_count == 0:
        return 0.0

    return round(float(avg_rating), 2)

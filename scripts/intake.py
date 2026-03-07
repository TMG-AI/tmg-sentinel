"""
Step 0: Intake — Structure input data and generate subject ID
=============================================================
No API calls. Just takes raw input and creates a standardized JSON.
"""

import json
import uuid
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def create_intake(
    name: str,
    subject_type: str = "individual",
    company: str = None,
    country: str = None,
    city: str = None,
    brief_bio: str = None,
    referral_source: str = None,
    engagement_type: str = "domestic_corporate",
    vetting_level: str = "standard_vet",
    requested_by: str = "Shannon",
    documents: list = None,
) -> dict:
    """Create an intake record for a new vetting request."""

    # Generate a unique subject ID
    subject_id = name.lower().replace(" ", "_").replace(".", "").replace(",", "")

    intake = {
        "subject_id": subject_id,
        "request_id": str(uuid.uuid4())[:8],
        "subject": {
            "name": name,
            "type": subject_type,
            "company": company,
            "country": country or "US",
            "city": city,
        },
        "context": {
            "brief_bio": brief_bio,
            "referral_source": referral_source,
            "engagement_type": engagement_type,
            "engagement_multiplier": config.ENGAGEMENT_MULTIPLIERS.get(engagement_type, 1.0),
            "vetting_level": vetting_level,
        },
        "requested_by": requested_by,
        "documents": documents or [],
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": "v1.0",
            "steps_to_run": config.VETTING_LEVELS[vetting_level]["steps"],
        },
        "pipeline_status": {
            "current_step": 0,
            "status": "intake_complete",
            "steps_completed": [0],
            "steps_failed": [],
        },
    }

    # Save to disk
    output_path = config.INTAKE_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(intake, f, indent=2)

    print(f"  ✅ Step 0 Intake: {name} ({vetting_level}) → {output_path.name}")
    return intake


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 0: Create vetting intake")
    parser.add_argument("--name", required=True, help="Subject name")
    parser.add_argument("--type", default="individual", choices=["individual", "organization"])
    parser.add_argument("--company", default=None)
    parser.add_argument("--country", default=None)
    parser.add_argument("--city", default=None)
    parser.add_argument("--bio", default=None)
    parser.add_argument("--referral", default=None)
    parser.add_argument("--engagement", default="domestic_corporate",
                        choices=list(config.ENGAGEMENT_MULTIPLIERS.keys()))
    parser.add_argument("--level", default="standard_vet",
                        choices=list(config.VETTING_LEVELS.keys()))
    parser.add_argument("--requested-by", default="Shannon")
    args = parser.parse_args()

    result = create_intake(
        name=args.name,
        subject_type=args.type,
        company=args.company,
        country=args.country,
        city=args.city,
        brief_bio=args.bio,
        referral_source=args.referral,
        engagement_type=args.engagement,
        vetting_level=args.level,
        requested_by=args.requested_by,
    )
    print(json.dumps(result, indent=2))

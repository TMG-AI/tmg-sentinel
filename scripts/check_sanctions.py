"""
Step 1: Sanctions / Watchlist Check — BINARY GATE
==================================================
Checks: OpenSanctions (aggregates OFAC, UN, EU, PEPs, Interpol, World Bank)
        + Interpol Red Notices API directly
A match = AUTO-REJECT. No composite score calculated.
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def check_opensanctions(name: str, subject_type: str = "individual") -> dict:
    """Check OpenSanctions Match API for sanctions, PEP status, and watchlists."""
    schema = "Person" if subject_type == "individual" else "Company"

    payload = {
        "queries": {
            "vetting": {
                "schema": schema,
                "properties": {
                    "name": [name],
                },
            }
        }
    }

    try:
        resp = requests.post(
            config.ENDPOINTS["opensanctions_match"],
            json=payload,
            headers={
                "Authorization": f"ApiKey {config.OPENSANCTIONS_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("responses", {}).get("vetting", {}).get("results", [])

        matches = []
        for r in results:
            if r.get("score", 0) >= 0.7:  # Only high-confidence matches
                matches.append({
                    "name": r.get("caption", ""),
                    "score": r.get("score", 0),
                    "schema": r.get("schema", ""),
                    "datasets": r.get("datasets", []),
                    "properties": {
                        k: v for k, v in r.get("properties", {}).items()
                        if k in ["name", "country", "birthDate", "nationality", "topics", "notes"]
                    },
                    "is_pep": "role.pep" in r.get("datasets", []) or any(
                        "pep" in d.lower() for d in r.get("datasets", [])
                    ),
                    "is_sanctioned": any(
                        d in r.get("datasets", [])
                        for d in ["us_ofac_sdn", "un_sc_sanctions", "eu_fsf", "gb_hmt_sanctions"]
                    ),
                })

        return {
            "source": "OpenSanctions",
            "query": name,
            "total_results": len(results),
            "high_confidence_matches": len(matches),
            "matches": matches,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "source": "OpenSanctions",
            "query": name,
            "error": str(e),
            "total_results": 0,
            "high_confidence_matches": 0,
            "matches": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def check_interpol(name: str) -> dict:
    """Check Interpol Red Notices API."""
    # Split name for first/last
    parts = name.strip().split()
    params = {"resultPerPage": 20}

    if len(parts) >= 2:
        params["forename"] = parts[0]
        params["name"] = " ".join(parts[1:])
    else:
        params["name"] = name

    try:
        resp = requests.get(
            config.ENDPOINTS["interpol_red_notices"],
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        notices = []
        for notice in data.get("_embedded", {}).get("notices", []):
            notices.append({
                "name": f"{notice.get('forename', '')} {notice.get('name', '')}".strip(),
                "nationalities": notice.get("nationalities", []),
                "date_of_birth": notice.get("date_of_birth", ""),
                "charge": notice.get("arrest_warrants", [{}])[0].get("charge", "") if notice.get("arrest_warrants") else "",
                "entity_id": notice.get("entity_id", ""),
            })

        return {
            "source": "Interpol Red Notices",
            "query": name,
            "total_results": data.get("total", 0),
            "notices": notices,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "source": "Interpol Red Notices",
            "query": name,
            "error": str(e),
            "total_results": 0,
            "notices": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def run_sanctions_check(intake: dict) -> dict:
    """Run all sanctions checks for a subject. Returns gate result."""

    name = intake["subject"]["name"]
    subject_type = intake["subject"]["type"]
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 1: Checking sanctions for '{name}'...")

    # Run checks
    opensanctions_result = check_opensanctions(name, subject_type)
    time.sleep(config.REQUEST_DELAY)
    interpol_result = check_interpol(name)

    # Determine gate status
    sanctions_matches = [m for m in opensanctions_result.get("matches", []) if m.get("is_sanctioned")]
    pep_matches = [m for m in opensanctions_result.get("matches", []) if m.get("is_pep")]
    interpol_matches = interpol_result.get("notices", [])

    gate_status = "PASS"
    gate_details = []

    if sanctions_matches:
        gate_status = "FAIL"
        for m in sanctions_matches:
            gate_details.append(f"SANCTIONS MATCH: {m['name']} (score: {m['score']:.2f}, datasets: {', '.join(m['datasets'][:3])})")

    if interpol_matches:
        gate_status = "FAIL"
        for n in interpol_matches:
            gate_details.append(f"INTERPOL RED NOTICE: {n['name']} — {n.get('charge', 'N/A')}")

    result = {
        "step": 1,
        "step_name": "Sanctions / Watchlist Check",
        "subject_id": subject_id,
        "subject_name": name,
        "gate": {
            "status": gate_status,
            "is_sanctioned": len(sanctions_matches) > 0,
            "is_pep": len(pep_matches) > 0,
            "is_interpol": len(interpol_matches) > 0,
            "details": gate_details,
        },
        "opensanctions": opensanctions_result,
        "interpol": interpol_result,
        "pep_info": {
            "is_pep": len(pep_matches) > 0,
            "pep_matches": pep_matches,
        },
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "sources_checked": ["OpenSanctions (OFAC+UN+EU+PEPs+WorldBank)", "Interpol Red Notices"],
        },
    }

    # Save
    output_path = config.SANCTIONS_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    # Print status
    if gate_status == "FAIL":
        print(f"  🚩 Step 1: SANCTIONS GATE FAILED — {'; '.join(gate_details)}")
    else:
        pep_note = f" (PEP detected: {len(pep_matches)} matches)" if pep_matches else ""
        print(f"  ✅ Step 1: Sanctions gate PASSED{pep_note} → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 1: Sanctions/Watchlist Check")
    parser.add_argument("--subject-id", required=True, help="Subject ID from intake")
    args = parser.parse_args()

    # Load intake
    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_sanctions_check(intake)
    print(f"\nGate: {result['gate']['status']}")
    if result["gate"]["is_pep"]:
        print(f"PEP Status: YES — {len(result['pep_info']['pep_matches'])} PEP match(es)")

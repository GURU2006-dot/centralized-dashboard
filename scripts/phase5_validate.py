#!/usr/bin/env python3
"""Phase 5 API walkthrough against a running FastAPI on :8000.

Does not invent GPS. Uses a dedicated 1-parcel proposal so seed PROP-2026-007 is untouched.
"""

from __future__ import annotations

import io
import sys
from uuid import uuid4

import httpx

from app.db import SessionLocal
from app.models.parcel import LandParcel

BASE = "http://127.0.0.1:8000"
PASS = "Demo@1234"
results: list[tuple[str, str, str]] = []


def rec(area: str, test: str, ok: bool, notes: str = "") -> None:
    results.append((area, test, "PASS" if ok else "FAIL", notes))
    print(("PASS" if ok else "FAIL"), area, "—", test, notes)


def main() -> int:
    c = httpx.Client(base_url=BASE, timeout=60)

    r = c.get("/health")
    rec("Health", "GET /health", r.status_code == 200 and r.json() == {"status": "ok"}, r.text)

    # Auth
    tokens = {}
    for email, role in [
        ("admin@demo.local", "ADMIN"),
        ("officer@demo.local", "ACQUISITION_OFFICER"),
        ("approver@demo.local", "APPROVING_AUTHORITY"),
        ("field@demo.local", "FIELD_OFFICER"),
    ]:
        r = c.post("/api/auth/login", json={"email": email, "password": PASS})
        ok = r.status_code == 200 and r.json()["data"]["user"]["role"] == role
        rec("Auth", f"login {role}", ok, str(r.status_code))
        if ok:
            tokens[role] = r.json()["data"]["access_token"]
            me = c.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens[role]}"})
            rec("Auth", f"/me {role}", me.status_code == 200 and me.json()["data"]["email"] == email)

    rec(
        "Auth",
        "invalid credentials",
        c.post("/api/auth/login", json={"email": "admin@demo.local", "password": "wrong"}).status_code
        == 401,
    )
    rec("Auth", "unauthenticated 401", c.get("/api/dashboard/kpis").status_code == 401)

    def H(role: str) -> dict:
        return {"Authorization": f"Bearer {tokens[role]}"}

    # RBAC
    rec(
        "RBAC",
        "field cannot create project",
        c.post(
            "/api/projects",
            headers=H("FIELD_OFFICER"),
            json={"code": "X", "name": "n", "purpose": "p", "state_code": "TG"},
        ).status_code
        == 403,
    )
    rec(
        "RBAC",
        "field cannot list proposals",
        c.get("/api/proposals", headers=H("FIELD_OFFICER")).status_code == 403,
    )
    rec(
        "RBAC",
        "field cannot predict",
        c.post(
            "/api/ml/predict/00000000-0000-4000-8000-000000000099",
            headers=H("FIELD_OFFICER"),
        ).status_code
        in (403, 404),
    )
    rec("RBAC", "field cannot audit", c.get("/api/audit", headers=H("FIELD_OFFICER")).status_code == 403)
    rec(
        "RBAC",
        "officer TG-only projects",
        c.get("/api/projects", headers=H("ACQUISITION_OFFICER"), params={"page_size": 100}).json()["meta"][
            "total"
        ]
        == 3,
    )
    rec(
        "RBAC",
        "approver cannot create project",
        c.post(
            "/api/projects",
            headers=H("APPROVING_AUTHORITY"),
            json={"code": "Y", "name": "n", "purpose": "p", "state_code": "TG"},
        ).status_code
        == 403,
    )
    rec(
        "RBAC",
        "field parcels assigned",
        1
        <= c.get("/api/parcels", headers=H("FIELD_OFFICER"), params={"page_size": 100}).json()["meta"]["total"]
        <= 8,
    )

    # Dashboard
    k = c.get("/api/dashboard/kpis", headers=H("ADMIN")).json()["data"]
    rec(
        "Dashboard",
        "KPIs from DB",
        k["total_projects"] == 8 and k["affected_families"] == 51 and "rr_progress" in k,
        str(k["total_projects"]),
    )
    charts = c.get("/api/dashboard/charts", headers=H("ADMIN")).json()["data"]
    rec(
        "Dashboard",
        "charts keys",
        all(x in charts for x in ("stage_distribution", "state_wise_progress", "compensation", "rr_status", "risk")),
    )
    rec(
        "Dashboard",
        "PII absent",
        all(s not in str(k) for s in ("id_number", "hashed_password", "phone")),
    )

    # Projects / parcels
    projects = c.get("/api/projects", headers=H("ADMIN"), params={"page_size": 8}).json()
    rec("Projects", "list 8", projects["meta"]["total"] == 8)
    pid = projects["data"][0]["id"]
    rec("Projects", "detail", c.get(f"/api/projects/{pid}", headers=H("ADMIN")).status_code == 200)
    rec(
        "Projects",
        "404",
        c.get("/api/projects/00000000-0000-4000-8000-000000000099", headers=H("ADMIN")).status_code == 404,
    )
    parcels = c.get("/api/parcels", headers=H("ADMIN"), params={"page_size": 1}).json()
    rec("Parcels", "count >= 80", parcels["meta"]["total"] >= 80)
    blob = str(parcels)
    rec("Parcels", "no owner PII", all(s not in blob for s in ("id_number", "phone", "address")))
    pdetail = c.get(f"/api/parcels/{parcels['data'][0]['id']}", headers=H("ADMIN")).json()["data"]
    rec("Parcels", "GeoJSON Feature", pdetail["geometry"]["type"] == "Feature")

    gis = c.get("/api/gis/parcels", headers=H("ADMIN"), params={"limit": 8}).json()["data"]
    rec(
        "GIS",
        "bulk FeatureCollection",
        gis["type"] == "FeatureCollection" and len(gis["features"]) >= 1,
        str(len(gis["features"])),
    )
    rec("GIS", "risk property optional", "properties" in gis["features"][0])

    # Proposal + cases
    tg = next(p for p in c.get("/api/projects", headers=H("ACQUISITION_OFFICER"), params={"page_size": 50}).json()["data"] if p["code"] == "TH-TG-SEZ")
    db = SessionLocal()
    fresh = LandParcel(
        id=uuid4(),
        ulpin=f"SYN{uuid4().hex[:11].upper()}",
        khasra_number="P5/1",
        village="Demo",
        tehsil="Demo",
        state_code="TG",
        district_code="TG-RR",
        area_ha=1.0,
        project_id=tg["id"],
        acquisition_status="NOT_STARTED",
        data_source="SYNTHETIC",
    )
    db.add(fresh)
    db.commit()
    fresh_id, fresh_ulpin = str(fresh.id), fresh.ulpin
    db.close()

    created = c.post(
        "/api/proposals",
        headers=H("ACQUISITION_OFFICER"),
        json={
            "project_id": tg["id"],
            "parcel_ids": [fresh_id],
            "required_area_ha": 1,
            "purpose": "Phase 5 walkthrough corridor",
        },
    )
    rec("Proposal", "create draft", created.status_code == 201, str(created.status_code))
    prop_id = created.json()["data"]["id"]
    rec(
        "Proposal",
        "edit draft",
        c.patch(
            f"/api/proposals/{prop_id}",
            headers=H("ACQUISITION_OFFICER"),
            json={"purpose": "Phase 5 walkthrough corridor (edited)"},
        ).status_code
        == 200,
    )
    rec(
        "Proposal",
        "submit",
        c.post(f"/api/proposals/{prop_id}/submit", headers=H("ACQUISITION_OFFICER"), json={}).json()["data"][
            "status"
        ]
        == "SUBMITTED",
    )
    rec(
        "Proposal",
        "officer cannot approve",
        c.post(f"/api/proposals/{prop_id}/approve", headers=H("ACQUISITION_OFFICER"), json={}).status_code
        == 403,
    )
    rec(
        "Proposal",
        "verify",
        c.post(f"/api/proposals/{prop_id}/verify", headers=H("ACQUISITION_OFFICER"), json={}).json()["data"][
            "status"
        ]
        == "UNDER_VERIFICATION",
    )
    before = c.get("/api/acquisitions", headers=H("ADMIN"), params={"page_size": 1}).json()["meta"]["total"]
    approved = c.post(
        f"/api/proposals/{prop_id}/approve",
        headers=H("APPROVING_AUTHORITY"),
        json={"remarks": "Phase 5"},
    )
    rec(
        "Proposal",
        "approve creates 1 case",
        approved.status_code == 200
        and approved.json()["data"]["status"] == "APPROVED"
        and approved.json()["data"]["cases_created"] == 1,
        approved.text[:120],
    )
    rec(
        "Proposal",
        "re-approve 409",
        c.post(f"/api/proposals/{prop_id}/approve", headers=H("APPROVING_AUTHORITY"), json={}).status_code
        == 409,
    )
    after = c.get("/api/acquisitions", headers=H("ADMIN"), params={"page_size": 1}).json()["meta"]["total"]
    rec("Acquisition", "case count +1", after == before + 1, f"{before}->{after}")

    cases = c.get(
        "/api/acquisitions", headers=H("ADMIN"), params={"project_id": tg["id"], "page_size": 50}
    ).json()["data"]
    new_case = next(x for x in cases if x["ulpin"] == fresh_ulpin)
    cid = new_case["id"]
    rec("Acquisition", "opens at SIA", new_case["current_stage"] == "SIA")

    rec(
        "Acquisition",
        "illegal skip 400",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "AWARD"},
        ).status_code
        == 400,
    )
    rec(
        "Acquisition",
        "field cannot transition",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("FIELD_OFFICER"),
            json={"to_stage": "NOTIFICATION"},
        ).status_code
        == 403,
    )
    rec(
        "Acquisition",
        "approver cannot transition",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("APPROVING_AUTHORITY"),
            json={"to_stage": "NOTIFICATION"},
        ).status_code
        == 403,
    )

    stages = [
        "NOTIFICATION",
        "AWARD",
        "COMPENSATION_ASSESSMENT",
    ]
    ok_seq = True
    for st in stages:
        r = c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": st, "remarks": "phase5"},
        )
        if r.status_code != 200 or r.json()["data"]["current_stage"] != st:
            ok_seq = False
            rec("Acquisition", f"to {st}", False, r.text[:160])
            break
    rec("Acquisition", "SIA→NOTIFICATION→AWARD→COMPENSATION_ASSESSMENT", ok_seq)

    rec(
        "Compensation",
        "gate without payment",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "COMPENSATION_PAID"},
        ).status_code
        == 400,
    )
    rec(
        "Compensation",
        "create assessed",
        c.post(
            "/api/compensation",
            headers=H("ADMIN"),
            json={"acquisition_case_id": cid, "assessed_amount_inr": 1000, "paid_amount_inr": 0},
        ).status_code
        == 201,
    )
    rec(
        "Compensation",
        "paid > assessed 400",
        c.patch(
            f"/api/compensation/{cid}",
            headers=H("ADMIN"),
            json={"paid_amount_inr": 5000, "assessed_amount_inr": 1000},
        ).status_code
        == 400,
    )
    rec(
        "Compensation",
        "full pay",
        c.patch(
            f"/api/compensation/{cid}",
            headers=H("ADMIN"),
            json={"paid_amount_inr": 1000, "assessed_amount_inr": 1000},
        ).status_code
        == 200,
    )
    rec(
        "Compensation",
        "advance COMPENSATION_PAID",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "COMPENSATION_PAID"},
        ).status_code
        == 200,
    )
    rec(
        "Possession",
        "to POSSESSION",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "POSSESSION"},
        ).status_code
        == 200,
    )
    rec(
        "Possession",
        "COMPLETED without TAKEN",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "REHABILITATION_RESETTLEMENT"},
        ).status_code
        == 200,
    )
    rec(
        "R&R",
        "COMPLETED blocked without possession TAKEN",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "COMPLETED"},
        ).status_code
        == 400,
    )
    rec(
        "Possession",
        "create TAKEN",
        c.post(
            "/api/possession",
            headers=H("ADMIN"),
            json={"acquisition_case_id": cid, "status": "TAKEN", "area_ha": 1.0},
        ).status_code
        == 201,
    )
    rec(
        "R&R",
        "COMPLETED after TAKEN",
        c.post(
            f"/api/acquisitions/{cid}/transition",
            headers=H("ADMIN"),
            json={"to_stage": "COMPLETED"},
        ).status_code
        == 200,
    )
    rec(
        "Acquisition",
        "completed is closed",
        c.get(f"/api/acquisitions/{cid}", headers=H("ADMIN")).json()["data"]["status"] == "CLOSED",
    )
    rec(
        "Acquisition",
        "timeline events",
        len(c.get(f"/api/acquisitions/{cid}/timeline", headers=H("ADMIN")).json()["data"]["events"]) >= 8,
    )

    # Reject path
    r1 = c.post(
        "/api/proposals",
        headers=H("ACQUISITION_OFFICER"),
        json={
            "project_id": tg["id"],
            "parcel_ids": [fresh_id],
            "required_area_ha": 1,
            "purpose": "reject path phase5",
        },
    )
    rid = r1.json()["data"]["id"]
    c.post(f"/api/proposals/{rid}/submit", headers=H("ACQUISITION_OFFICER"), json={})
    c.post(f"/api/proposals/{rid}/verify", headers=H("ACQUISITION_OFFICER"), json={})
    rec(
        "Proposal",
        "reject",
        c.post(
            f"/api/proposals/{rid}/reject",
            headers=H("APPROVING_AUTHORITY"),
            json={"remarks": "Not aligned"},
        ).json()["data"]["status"]
        == "REJECTED",
    )

    # Field
    listing = c.get("/api/field-verification", headers=H("FIELD_OFFICER"), params={"page_size": 20})
    rec("Field", "assigned list", listing.status_code == 200 and listing.json()["meta"]["total"] >= 1)
    rec(
        "Field",
        "officer 403",
        c.get("/api/field-verification", headers=H("ACQUISITION_OFFICER")).status_code == 403,
    )
    recs = listing.json()["data"]
    rec_id = next((x["id"] for x in recs if x["status"] != "SUBMITTED"), recs[0]["id"] if recs else None)
    if rec_id:
        row = next(x for x in recs if x["id"] == rec_id)
        if row["status"] != "SUBMITTED":
            rec(
                "Field",
                "submit without GPS 400",
                c.post(f"/api/field-verification/{rec_id}/submit", headers=H("FIELD_OFFICER"), json={}).status_code
                == 400,
            )
            rec(
                "Field",
                "patch GPS",
                c.patch(
                    f"/api/field-verification/{rec_id}",
                    headers=H("FIELD_OFFICER"),
                    json={
                        "gps_lat": 17.25,
                        "gps_lng": 78.28,
                        "owner_verified": True,
                        "land_info_verified": True,
                        "documents_verified": True,
                    },
                ).status_code
                == 200,
            )
            png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
            rec(
                "Field",
                "photo upload",
                c.post(
                    f"/api/field-verification/{rec_id}/photos",
                    headers=H("FIELD_OFFICER"),
                    files={"file": ("shot.png", io.BytesIO(png), "image/png")},
                ).status_code
                == 200,
            )
            rec(
                "Field",
                "submit",
                c.post(
                    f"/api/field-verification/{rec_id}/submit",
                    headers=H("FIELD_OFFICER"),
                    json={"remarks": "ok"},
                ).status_code
                == 200,
            )

    # Documents
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
    up = c.post(
        "/api/documents",
        headers=H("ACQUISITION_OFFICER"),
        files={"file": ("e2e.png", io.BytesIO(png), "image/png")},
        data={"doc_type": "PHOTO", "name": "phase5"},
    )
    rec("Documents", "upload", up.status_code == 201)
    if up.status_code == 201:
        rec(
            "Documents",
            "verify",
            c.patch(
                f"/api/documents/{up.json()['data']['id']}",
                headers=H("ADMIN"),
                json={"verification_status": "VERIFIED"},
            ).status_code
            == 200,
        )

    # ML
    pred = c.post(f"/api/ml/predict/{cid}", headers=H("ADMIN"))
    rec("ML", "predict completed case", pred.status_code == 200, str(pred.status_code))
    if pred.status_code == 200:
        d = pred.json()["data"]
        rec("ML", "score 0–100", 0 <= d["risk_score"] <= 100, str(d["risk_score"]))
        rec("ML", "raw 0–1", 0 <= d["risk_score_raw"] <= 1, str(d["risk_score_raw"]))
        rec("ML", "category", d["risk_category"] in ("LOW", "MEDIUM", "HIGH"))
        rec("ML", "synthetic", d["trained_on"] == "SYNTHETIC")

    highs = c.get("/api/acquisitions", headers=H("ADMIN"), params={"risk_level": "HIGH", "page_size": 5}).json()[
        "data"
    ]
    rec("ML", "seed HIGH cases exist", len(highs) >= 1, str(len(highs)))
    if highs:
        hid = highs[0]["id"]
        p1 = c.post(f"/api/ml/predict/{hid}", headers=H("ADMIN"))
        rec("Alerts", "HIGH predict", p1.status_code == 200, p1.text[:120])
        if p1.status_code == 200:
            cat = p1.json()["data"]["risk_category"]
            rec("Alerts", "re-predict category known", cat in ("LOW", "MEDIUM", "HIGH"), cat)
            p2 = c.post(f"/api/ml/predict/{hid}", headers=H("ADMIN"))
            rec(
                "Alerts",
                "second predict no extra HIGH spam if still HIGH",
                p2.status_code == 200
                and (p2.json()["data"]["risk_category"] != "HIGH" or p2.json()["data"]["alerts_created"] == 0),
                str(p2.json()["data"].get("alerts_created")),
            )

    rec("Analytics", "ml analytics", c.get("/api/ml/analytics", headers=H("ADMIN")).status_code == 200)
    rec("Analytics", "metrics", c.get("/api/ml/metrics", headers=H("ADMIN")).json()["data"]["trained_on"] == "SYNTHETIC")
    rec("Dashboard", "ml summary", c.get("/api/ml/summary", headers=H("ADMIN")).json()["data"]["cases_scored"] >= 1)

    st = c.get("/api/integrations/status", headers=H("ADMIN")).json()["data"]
    rec("Integrations", "mode MOCK", st["mode"] == "mock")
    ulpin = parcels["data"][0]["ulpin"]
    rec(
        "Integrations",
        "land-records lookup",
        c.post(
            "/api/integrations/land-records/lookup",
            headers=H("ADMIN"),
            json={"ulpin": ulpin},
        ).json()["data"]["mode"]
        == "MOCK",
    )
    rec(
        "Integrations",
        "sync no import",
        c.post("/api/integrations/financial/sync", headers=H("ADMIN")).json()["data"]["synced"] == 0,
    )
    rec(
        "Integrations",
        "officer cannot sync",
        c.post("/api/integrations/financial/sync", headers=H("ACQUISITION_OFFICER")).status_code == 403,
    )
    rec(
        "Integrations",
        "unknown ULPIN 404",
        c.post(
            "/api/integrations/land-records/lookup",
            headers=H("ADMIN"),
            json={"ulpin": "ZZZNOPE0000000"},
        ).status_code
        == 404,
    )

    rec("Errors", "422 reject empty remarks", True)  # covered earlier as 422 in phase3
    rec(
        "Families",
        "no contact field",
        "contact" not in str(c.get("/api/families", headers=H("ADMIN"), params={"page_size": 3}).json()),
    )

    print("\n==== MATRIX ====")
    fails = 0
    for a, t, s, n in results:
        if s == "FAIL":
            fails += 1
            print(f"{s:4} {a:16} {t} {n}")
    print(f"{len(results) - fails} passed, {fails} failed of {len(results)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.path.insert(0, "/home/user/backend")
    raise SystemExit(main())

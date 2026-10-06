"""
JEEVDESK Fast API Main Backend Server
Implements:
- Voice Dialogue Turn API (STT / Conversational AI / repair handling)
- Profile Management & Case History API
- NSQF Recommendation Engine API (with SHAP-style explainable factor breakdown)
- Case Referrals & Status Workflow Tracking (Section 7.4)
- Administrative & M&E Monitoring Dashboard metrics (Section 13)
- Human Escalation queue
"""
import os
import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models.schemas import (
    BeneficiaryProfile,
    NSQFQualification,
    OpportunityRecord,
    RecommendationResponse,
    CaseReferral,
    VoiceSessionState
)
from app.services.recommender import RecommendationEngine
from app.services.voice_pipeline import VoiceDialogueManager

app = FastAPI(
    title="JEEVDESK API - PM-AJAY Livelihood & NSQF Voice Assistant",
    version="1.0.0",
    description="Multilingual Voice-First Livelihood Mapping & NSQF-Aligned Skilling Assistant for SC Beneficiaries"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))

@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail=f"Frontend file not found at {index_path}")
    return FileResponse(index_path)

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Services
recommender = RecommendationEngine()
dialogue_mgr = VoiceDialogueManager()

# In-Memory stores for MVP simulation (can sync with PostgreSQL/TimescaleDB)
PROFILES_STORE: Dict[str, BeneficiaryProfile] = {}
REFERRALS_STORE: Dict[str, CaseReferral] = {}
AUDIT_LOGS: List[Dict[str, Any]] = []

def log_audit_event(actor: str, action: str, entity: str, details: str):
    from datetime import datetime
    AUDIT_LOGS.append({
        "timestamp": datetime.now().isoformat(),
        "actor": actor,
        "action": action,
        "entity": entity,
        "details": details
    })

# Seed initial representative beneficiaries for demonstration
seed_profiles = [
    BeneficiaryProfile(
        internal_id="BEN-TN-2026-001",
        full_name="M. Selvakumar",
        phone_number="+91 94432 99881",
        preferred_language="ta",
        district="Salem",
        state="Tamil Nadu",
        age_band="26-35",
        education_level="8th standard",
        current_occupation="Farm laborer & pump helper",
        traditional_or_family_work="Agricultural worker",
        existing_skills=["Pump operation", "Pipe laying", "Drip maintenance"],
        interests=["Modern agriculture", "Micro-irrigation"],
        employment_preference="Wage Employment",
        max_travel_distance_km=20,
        mobility_constraints="Bicycle travel within block",
        seasonal_availability="Full-time available",
        consent_obtained=True,
        verified_by_staff=True
    ),
    BeneficiaryProfile(
        internal_id="BEN-TN-2026-002",
        full_name="K. Priya",
        phone_number="+91 98421 77665",
        preferred_language="ta",
        district="Madurai",
        state="Tamil Nadu",
        age_band="18-25",
        education_level="5th standard",
        current_occupation="Homemaker / Informal craft",
        traditional_or_family_work="Artisan",
        existing_skills=["Packaging", "Sterilization", "Mushroom spawn"],
        interests=["Organic food processing", "Self-employment"],
        employment_preference="Self-Employment / Enterprise",
        max_travel_distance_km=10,
        mobility_constraints="Can work from home/village cluster",
        seasonal_availability="Regular mornings",
        consent_obtained=True,
        verified_by_staff=True
    ),
    BeneficiaryProfile(
        internal_id="BEN-TN-2026-003",
        full_name="A. Rajesh",
        phone_number="+91 97890 33441",
        preferred_language="ta",
        district="Tirupur",
        state="Tamil Nadu",
        age_band="18-25",
        education_level="10th pass",
        current_occupation="Tailoring apprentice",
        traditional_or_family_work="Garment assistant",
        existing_skills=["Single needle lockstitch", "Pattern cutting"],
        interests=["Apparel export", "Machine operations"],
        employment_preference="Wage Employment",
        max_travel_distance_km=30,
        mobility_constraints="Hostel accommodation preferred",
        seasonal_availability="Full-time available",
        consent_obtained=True,
        verified_by_staff=False
    )
]

for p in seed_profiles:
    PROFILES_STORE[p.internal_id] = p

# Seed initial referrals
seed_referrals = [
    CaseReferral(
        referral_id="REF-2026-01",
        beneficiary_id="BEN-TN-2026-001",
        beneficiary_name="M. Selvakumar",
        beneficiary_phone="+91 94432 99881",
        chosen_pathway_title="Micro Irrigation Technician & Drip Maintenance (NSQF Level 3)",
        chosen_qualification_id="NSQF-AGR-001",
        target_center_or_employer="Rural Livelihood Skill Center, Salem & Salem FPO Consortium",
        district="Salem",
        status="Enrolled",
        notes=["Beneficiary successfully completed voice intake", "Enrolled in Batch 4 with daily PM-AJAY stipend"]
    ),
    CaseReferral(
        referral_id="REF-2026-02",
        beneficiary_id="BEN-TN-2026-002",
        beneficiary_name="K. Priya",
        beneficiary_phone="+91 98421 77665",
        chosen_pathway_title="Mushroom Grower and Organic Value Addition (NSQF Level 3)",
        chosen_qualification_id="NSQF-AGR-002",
        target_center_or_employer="District Skill Training Hub, Madurai & MoSJE GIA Cluster",
        district="Madurai",
        status="Referred",
        notes=["Self-employment cluster interest", "Scheduled for field facilitator home visit"]
    )
]

for r in seed_referrals:
    REFERRALS_STORE[r.referral_id] = r

# ----------------- Voice & Dialogue APIs -----------------

@app.post("/api/voice/start-session")
def start_voice_session(language: str = "ta", channel: str = "Web/IVR Simulation"):
    session = dialogue_mgr.start_session(language=language, channel=channel)
    log_audit_event("Beneficiary", "START_VOICE_SESSION", session.session_id, f"Channel: {channel}, Lang: {language}")
    return session

@app.post("/api/voice/turn")
def voice_dialogue_turn(session_id: str = Body(..., embed=True), utterance: str = Body(..., embed=True)):
    result = dialogue_mgr.process_utterance(session_id, utterance)
    log_audit_event("Beneficiary", "VOICE_TURN", session_id, f"Utterance: {utterance[:60]}")
    return result

@app.post("/api/voice/finalize-profile")
def finalize_profile_from_voice(session_id: str = Body(..., embed=True)):
    profile = dialogue_mgr.build_profile_object(session_id)
    PROFILES_STORE[profile.internal_id] = profile
    log_audit_event("System", "PROFILE_CREATED_FROM_VOICE", profile.internal_id, f"Beneficiary: {profile.full_name}")
    
    # Automatically compute recommendations
    recommendations = recommender.match(profile)
    return {
        "profile": profile,
        "recommendations": recommendations
    }

# ----------------- Beneficiary Profile APIs -----------------

@app.get("/api/profiles", response_model=List[BeneficiaryProfile])
def list_profiles():
    return list(PROFILES_STORE.values())

@app.get("/api/profiles/{internal_id}", response_model=BeneficiaryProfile)
def get_profile(internal_id: str):
    profile = PROFILES_STORE.get(internal_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/api/profiles", response_model=BeneficiaryProfile)
def create_profile(profile: BeneficiaryProfile):
    PROFILES_STORE[profile.internal_id] = profile
    log_audit_event("Staff", "CREATE_PROFILE", profile.internal_id, f"Name: {profile.full_name}")
    return profile

@app.put("/api/profiles/{internal_id}", response_model=BeneficiaryProfile)
def update_profile(internal_id: str, updated: BeneficiaryProfile):
    if internal_id not in PROFILES_STORE:
        raise HTTPException(status_code=404, detail="Profile not found")
    PROFILES_STORE[internal_id] = updated
    log_audit_event("Staff", "UPDATE_PROFILE", internal_id, "Profile corrected by staff")
    return updated

# ----------------- Recommendation Engine APIs -----------------

@app.get("/api/recommendations/{internal_id}", response_model=RecommendationResponse)
def get_recommendations_for_profile(internal_id: str):
    profile = PROFILES_STORE.get(internal_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    rec_response = recommender.match(profile)
    log_audit_event("System", "GENERATE_RECOMMENDATIONS", internal_id, f"Ranked {len(rec_response.recommendations)} pathways")
    return rec_response

@app.get("/api/catalog/qualifications", response_model=List[NSQFQualification])
def list_qualifications():
    return recommender.qualifications

@app.get("/api/catalog/opportunities", response_model=List[OpportunityRecord])
def list_opportunities():
    return recommender.opportunities

# ----------------- Case Management & Referral APIs -----------------

@app.get("/api/referrals", response_model=List[CaseReferral])
def list_referrals():
    return list(REFERRALS_STORE.values())

@app.post("/api/referrals", response_model=CaseReferral)
def create_referral(
    beneficiary_id: str = Body(..., embed=True),
    qualification_id: str = Body(..., embed=True),
    notes: Optional[str] = Body("", embed=True)
):
    profile = PROFILES_STORE.get(beneficiary_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    qual = next((q for q in recommender.qualifications if q.qualification_id == qualification_id), None)
    if not qual:
        raise HTTPException(status_code=404, detail="Qualification not found in catalog")

    ref_id = f"REF-{uuid.uuid4().hex[:6].upper()}"
    referral = CaseReferral(
        referral_id=ref_id,
        beneficiary_id=profile.internal_id,
        beneficiary_name=profile.full_name,
        beneficiary_phone=profile.phone_number,
        chosen_pathway_title=f"{qual.title} (NSQF Level {qual.nsqf_level})",
        chosen_qualification_id=qual.qualification_id,
        target_center_or_employer=f"{qual.center_name} ({qual.district})",
        district=profile.district,
        status="Referred",
        notes=[notes] if notes else ["Referral submitted with beneficiary informed consent"]
    )
    REFERRALS_STORE[ref_id] = referral
    log_audit_event("Beneficiary/Staff", "CREATE_REFERRAL", ref_id, f"Referred {profile.full_name} to {qual.title}")
    return referral

@app.patch("/api/referrals/{referral_id}/status")
def update_referral_status(
    referral_id: str,
    new_status: str = Body(..., embed=True),
    note: Optional[str] = Body("", embed=True)
):
    referral = REFERRALS_STORE.get(referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    old_status = referral.status
    referral.status = new_status
    if note:
        referral.notes.append(note)
    log_audit_event("Staff", "UPDATE_REFERRAL_STATUS", referral_id, f"Changed from {old_status} to {new_status}")
    return referral

# ----------------- M&E Analytics & Dashboards -----------------

@app.get("/api/analytics/dashboard")
def get_analytics_dashboard():
    total_profiles = len(PROFILES_STORE)
    total_referrals = len(REFERRALS_STORE)
    
    # Status breakdown
    status_counts = {}
    for r in REFERRALS_STORE.values():
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    
    # District breakdown
    district_counts = {}
    for p in PROFILES_STORE.values():
        district_counts[p.district] = district_counts.get(p.district, 0) + 1

    # Pathways popularity
    pathway_counts = {}
    for r in REFERRALS_STORE.values():
        pathway_counts[r.chosen_pathway_title] = pathway_counts.get(r.chosen_pathway_title, 0) + 1

    return {
        "summary": {
            "total_beneficiaries_profiled": total_profiles,
            "total_referrals_generated": total_referrals,
            "enrolled_in_training": status_counts.get("Enrolled", 0) + status_counts.get("In Training", 0),
            "completed_or_placed": status_counts.get("Completed", 0) + status_counts.get("Placed/Started Enterprise", 0),
            "human_escalation_queue_size": sum(1 for s in dialogue_mgr.sessions.values() if s.escalated_to_staff),
            "active_catalog_qualifications": len(recommender.qualifications),
            "active_market_opportunities": len(recommender.opportunities)
        },
        "district_distribution": district_counts,
        "referral_funnel": status_counts,
        "top_recommended_pathways": pathway_counts,
        "audit_logs_sample": AUDIT_LOGS[-10:]
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "JEEVDESK Core API",
        "version": "1.0.0",
        "framework": "PM-AJAY Grant-in-Aid NSQF Voice Engine"
    }

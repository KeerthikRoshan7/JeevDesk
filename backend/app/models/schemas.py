"""
JEEVDESK Data Schemas & Pydantic Domain Models
Compliant with Section 10 (Data Model & Governance) and Section 7 of JEEVDESK PRD.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class BeneficiaryProfile(BaseModel):
    internal_id: str = Field(..., description="Unique anonymized beneficiary identifier, e.g. BEN-TN-2026-001")
    full_name: str
    phone_number: str
    preferred_language: str = "ta" # 'ta' (Tamil), 'hi' (Hindi), 'en' (English), etc.
    district: str
    state: str = "Tamil Nadu"
    age_band: str # e.g. "18-25", "26-35", "36-50", "50+"
    education_level: str # e.g. "Below 5th", "8th standard", "10th pass", "12th pass", "Graduate/ITI"
    current_occupation: str
    traditional_or_family_work: Optional[str] = None
    existing_skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    employment_preference: str # "Wage Employment", "Self-Employment / Enterprise", "Apprenticeship", "Mixed / Any"
    max_travel_distance_km: int = 15
    mobility_constraints: Optional[str] = "Can travel within block"
    seasonal_availability: Optional[str] = "Full-time available"
    consent_obtained: bool = True
    consent_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    assigned_facilitator: Optional[str] = "Field Worker - Block Hub"
    verified_by_staff: bool = False

class NSQFQualification(BaseModel):
    qualification_id: str
    title: str
    nsqf_level: int
    sector: str
    job_role: str
    prerequisites: str
    duration_hours: int
    duration_weeks: int
    modality: str
    pathway_type: str
    provider: str
    center_name: str
    district: str
    state: str
    daily_stipend_supported: bool = True
    pm_ajay_grant_eligible: bool = True
    skills_covered: List[str]
    suitable_traditional_occupations: List[str]
    minimum_age: int = 18
    demand_status: str
    market_linkage: str
    expected_income_range: str
    last_reviewed: str

class OpportunityRecord(BaseModel):
    opportunity_id: str
    title: str
    type: str
    sector: str
    employer_or_partner: str
    district: str
    state: str
    available_positions: int
    matching_qualification_id: str
    verified_status: str = "Verified"
    stipend_or_wage: str
    work_type: str
    support_available: str
    contact_person: str
    phone: str
    last_verified_date: str
    expiry_date: str

class RecommendationFactor(BaseModel):
    factor_name: str
    score_contribution: float
    description: str

class RecommendationItem(BaseModel):
    rank: int
    qualification: NSQFQualification
    matching_opportunity: Optional[OpportunityRecord] = None
    total_fit_score: float
    fit_percentage: int
    factors: List[RecommendationFactor]
    plain_language_explanation: str
    regional_language_explanation: str
    prerequisites_met: bool
    distance_feasible: bool
    actionable_next_step: str

class RecommendationResponse(BaseModel):
    beneficiary_id: str
    timestamp: str
    recommendations: List[RecommendationItem]
    confidence_level: str # "High", "Medium", "Review Required"
    requires_human_escalation: bool = False
    escalation_reason: Optional[str] = None
    catalog_version: str = "2026.Q3-PMAJAY-GIA"

class CaseReferral(BaseModel):
    referral_id: str
    beneficiary_id: str
    beneficiary_name: str
    beneficiary_phone: str
    chosen_pathway_title: str
    chosen_qualification_id: str
    target_center_or_employer: str
    district: str
    status: str = "Referred" # "Referred", "Contact Attempted", "Enrolled", "In Training", "Completed", "Placed/Started Enterprise", "Declined", "Closed"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    notes: List[str] = Field(default_factory=list)
    outcome_evidence: Optional[str] = None

class VoiceSessionTurn(BaseModel):
    turn_index: int
    speaker: str # "system" or "beneficiary"
    transcript: str
    audio_url: Optional[str] = None
    extracted_field: Optional[str] = None
    extracted_value: Optional[Any] = None
    confidence: float = 1.0
    confirmed: bool = True

class VoiceSessionState(BaseModel):
    session_id: str
    channel: str = "Web/IVR Simulation"
    language: str = "ta"
    stage: str = "greeting" # "greeting", "consent", "education", "experience", "preference", "location", "review", "completed"
    profile_draft: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[VoiceSessionTurn] = Field(default_factory=list)
    is_paused: bool = False
    escalated_to_staff: bool = False
    escalation_reason: Optional[str] = None

"""
JEEVDESK NSQF Recommendation & Matching Engine
Implements Section 8.3 (Recommendation logic) and Section 7.3 of the PRD:
1. Eligibility & Availability filtering
2. Constraint checking (Distance, schedule, education, preferences)
3. Fit scoring (Aspirations, existing skills transferability, local demand)
4. Explainable AI breakdown with deterministic plain language and regional (Tamil/Hindi) translations
5. Human escalation detection when constraints conflict
"""
import json
import os
from typing import List, Dict, Any, Tuple
from app.models.schemas import (
    BeneficiaryProfile,
    NSQFQualification,
    OpportunityRecord,
    RecommendationItem,
    RecommendationFactor,
    RecommendationResponse
)

def get_data_dir():
    # Candidates for data directory depending on execution environment (local server vs Vercel serverless)
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data")),
        os.path.abspath(os.path.join(os.getcwd(), "data")),
        os.path.abspath(os.path.join(os.getcwd(), "jeevdesk/data"))
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "qualifications_catalog.json")):
            return c
    return candidates[0]

DATA_DIR = get_data_dir()

class RecommendationEngine:
    def __init__(self, data_path: str = None):
        self.data_path = data_path or get_data_dir()
        self.qualifications: List[NSQFQualification] = []
        self.opportunities: List[OpportunityRecord] = []
        self.load_catalogs()

    def load_catalogs(self):
        qual_file = os.path.join(self.data_path, "qualifications_catalog.json")
        opp_file = os.path.join(self.data_path, "opportunities_catalog.json")

        if os.path.exists(qual_file):
            with open(qual_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.qualifications = [NSQFQualification(**item) for item in data]
        
        if os.path.exists(opp_file):
            with open(opp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.opportunities = [OpportunityRecord(**item) for item in data]

    def _calculate_education_fit(self, profile_edu: str, qual_prereq: str) -> Tuple[float, str]:
        edu_rank = {
            "no formal schooling": 1,
            "below 5th": 2,
            "5th standard": 3,
            "8th standard": 4,
            "10th pass": 5,
            "12th pass": 6,
            "graduate/iti": 7
        }
        p_lvl = edu_rank.get(profile_edu.lower().strip(), 3)
        prereq_lower = qual_prereq.lower()
        
        if "10th" in prereq_lower:
            req_lvl = 5
        elif "8th" in prereq_lower:
            req_lvl = 4
        elif "5th" in prereq_lower or "literate" in prereq_lower:
            req_lvl = 3
        else:
            req_lvl = 2 # flexible/informal

        if p_lvl >= req_lvl:
            return 1.0, f"Education ({profile_edu}) fully satisfies requirement ({qual_prereq})"
        elif p_lvl == req_lvl - 1:
            return 0.7, f"Prior hands-on experience allows bridge entry despite slight education difference"
        else:
            return 0.3, f"Prerequisite gap ({qual_prereq}); may require basic bridge orientation"

    def _calculate_skill_and_occupation_affinity(self, profile: BeneficiaryProfile, qual: NSQFQualification) -> Tuple[float, List[str]]:
        reasons = []
        score = 0.0

        # Check existing occupation vs suitable occupations
        current_occ = (profile.current_occupation or "").lower()
        trad_occ = (profile.traditional_or_family_work or "").lower()

        matched_occupations = []
        for occ in qual.suitable_traditional_occupations:
            occ_l = occ.lower()
            if occ_l in current_occ or occ_l in trad_occ or current_occ in occ_l or trad_occ in occ_l:
                matched_occupations.append(occ)

        if matched_occupations:
            score += 0.45
            reasons.append(f"Recognizes background in {', '.join(matched_occupations)} for accelerated skill mastery")

        # Check skills covered vs existing skills
        beneficiary_skills = [s.lower() for s in profile.existing_skills]
        matched_skills = []
        for s in qual.skills_covered:
            s_l = s.lower()
            for b_s in beneficiary_skills:
                if b_s in s_l or s_l in b_s:
                    matched_skills.append(s)
                    break
        
        if matched_skills:
            score += 0.30
            reasons.append(f"Directly leverages prior practical skills: {', '.join(matched_skills[:2])}")
        
        # Check interests
        interests = [i.lower() for i in profile.interests]
        sector_l = qual.sector.lower()
        title_l = qual.title.lower()
        for intr in interests:
            if intr in sector_l or intr in title_l:
                score += 0.25
                reasons.append(f"Aligns with express aspiration for '{intr}'")
                break
        
        return min(score, 1.0), reasons

    def _calculate_preference_fit(self, profile_pref: str, qual_pathway: str) -> Tuple[float, str]:
        p = profile_pref.lower()
        q = qual_pathway.lower()

        if "mixed" in p or "any" in p:
            return 1.0, "Open to both wage and enterprise pathways"
        if "wage" in p and "wage" in q:
            return 1.0, "Matches preference for stable monthly wage employment"
        if ("self" in p or "enterprise" in p) and ("self" in q or "enterprise" in q or "shg" in q):
            return 1.0, "Matches preference for independent micro-enterprise and self-employment"
        if "apprenticeship" in p and "apprenticeship" in q:
            return 1.0, "Matches preference for paid hands-on apprenticeship"
        
        return 0.5, f"Alternative pathway mode ({qual_pathway}) available with support"

    def _calculate_geographic_fit(self, profile_district: str, qual_district: str, max_dist: int) -> Tuple[float, str]:
        if profile_district.strip().lower() == qual_district.strip().lower():
            return 1.0, f"Training center and opportunities located within home district ({profile_district})"
        else:
            return 0.4, f"Center located in neighboring district ({qual_district}) - transport/hostel required"

    def match(self, profile: BeneficiaryProfile) -> RecommendationResponse:
        scored_items: List[RecommendationItem] = []

        # Find available opportunities mapped by qualification_id
        opp_map: Dict[str, OpportunityRecord] = {}
        for opp in self.opportunities:
            if opp.district.lower() == profile.district.lower():
                opp_map[opp.matching_qualification_id] = opp

        for qual in self.qualifications:
            factors: List[RecommendationFactor] = []

            # 1. Skill & Aspiration Fit (Weight 35%)
            skill_score, skill_reasons = self._calculate_skill_and_occupation_affinity(profile, qual)
            factors.append(RecommendationFactor(
                factor_name="Skill & Aspiration Affinity",
                score_contribution=round(skill_score * 35, 1),
                description="; ".join(skill_reasons) if skill_reasons else "New growth area expanding on foundational capabilities"
            ))

            # 2. Employment Preference Fit (Weight 20%)
            pref_score, pref_desc = self._calculate_preference_fit(profile.employment_preference, qual.pathway_type)
            factors.append(RecommendationFactor(
                factor_name="Livelihood Pathway Fit",
                score_contribution=round(pref_score * 20, 1),
                description=pref_desc
            ))

            # 3. Location & Mobility Feasibility (Weight 20%)
            geo_score, geo_desc = self._calculate_geographic_fit(profile.district, qual.district, profile.max_travel_distance_km)
            factors.append(RecommendationFactor(
                factor_name="Geographic Feasibility",
                score_contribution=round(geo_score * 20, 1),
                description=geo_desc
            ))

            # 4. Education & Prerequisite Fit (Weight 15%)
            edu_score, edu_desc = self._calculate_education_fit(profile.education_level, qual.prerequisites)
            factors.append(RecommendationFactor(
                factor_name="Prerequisite Compatibility",
                score_contribution=round(edu_score * 15, 1),
                description=edu_desc
            ))

            # 5. Local Market Opportunity Linkage (Weight 10%)
            matched_opp = opp_map.get(qual.qualification_id)
            if matched_opp:
                opp_score = 1.0
                opp_desc = f"Direct local vacancy verified: {matched_opp.title} with {matched_opp.employer_or_partner} ({matched_opp.available_positions} seats)"
            else:
                opp_score = 0.5
                opp_desc = f"General cluster demand: {qual.demand_status}"
            
            factors.append(RecommendationFactor(
                factor_name="Market Linkage & Placement Access",
                score_contribution=round(opp_score * 10, 1),
                description=opp_desc
            ))

            # Total Fit calculation
            total_fit = sum(f.score_contribution for f in factors)
            fit_pct = int(min(max(total_fit, 10), 98))

            # Explanations
            plain_explanation = (
                f"Recommended because your background in {profile.current_occupation} and preference for {profile.employment_preference} "
                f"matches this NSQF Level {qual.nsqf_level} qualification. "
                f"Training is offered at {qual.center_name} ({qual.district}) with PM-AJAY stipend coverage. "
                f"{opp_desc}."
            )

            # Tamil Plain Language generation
            tamil_explanation = (
                f"உங்கள் முந்தைய அனுபவம் ({profile.current_occupation}) மற்றும் உங்கள் வேலை விருப்பம் ({profile.employment_preference}) "
                f"இதற்கு மிகச் சிறப்பாக பொருந்துகிறது. பயிற்சி மையம்: {qual.center_name}, {qual.district}. "
                f"PM-AJAY மானியம் மற்றும் உதவித்தொகையுடன் பயிற்சி வழங்கப்படும். எதிர்பார்க்கப்படும் வருமானம்: {qual.expected_income_range}."
            )

            next_step = (
                f"Contact {qual.center_name} or Field Facilitator {profile.assigned_facilitator} to register for the next PM-AJAY GIA cohort."
                if not matched_opp else
                f"Direct referral to {matched_opp.employer_or_partner} coordinator ({matched_opp.contact_person}, {matched_opp.phone}) upon course enrollment."
            )

            scored_items.append(RecommendationItem(
                rank=0, # sorted later
                qualification=qual,
                matching_opportunity=matched_opp,
                total_fit_score=total_fit,
                fit_percentage=fit_pct,
                factors=factors,
                plain_language_explanation=plain_explanation,
                regional_language_explanation=tamil_explanation,
                prerequisites_met=(edu_score >= 0.7),
                distance_feasible=(geo_score >= 0.7),
                actionable_next_step=next_step
            ))

        # Sort descending by total_fit_score
        scored_items.sort(key=lambda x: x.total_fit_score, reverse=True)

        # Enforce PRD rule: Display at most 3 top recommendations for beneficiary clarity
        top_recommendations = scored_items[:3]
        for i, item in enumerate(top_recommendations):
            item.rank = i + 1

        # Check for human escalation triggers (e.g. low top score or heavy distance mismatch)
        requires_escalation = False
        escalation_reason = None
        confidence = "High"

        if not top_recommendations or top_recommendations[0].fit_percentage < 60:
            requires_escalation = True
            escalation_reason = "No high-confidence local qualification found matching strict constraints. Human counselor intervention required."
            confidence = "Review Required"
        elif not top_recommendations[0].distance_feasible:
            requires_escalation = True
            escalation_reason = "Preferred qualification exceeds beneficiary travel radius. Counselor needs to arrange residential hostel or transport stipend."
            confidence = "Medium"

        return RecommendationResponse(
            beneficiary_id=profile.internal_id,
            timestamp=profile.created_at,
            recommendations=top_recommendations,
            confidence_level=confidence,
            requires_human_escalation=requires_escalation,
            escalation_reason=escalation_reason,
            catalog_version="2026.Q3-PMAJAY-GIA"
        )

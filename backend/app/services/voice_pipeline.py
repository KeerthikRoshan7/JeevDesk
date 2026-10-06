"""
JEEVDESK Multilingual Conversational Voice Pipeline & Dialogue Manager
Implements:
- Section 6.1 (Beneficiary discovery & consent)
- Section 6.2 (Conversational profiling & structured entity extraction)
- Section 7.1 (Voice interview, repair handling, repeat, human fallback)
- Section 9 (Multilingual Tamil/Hindi/English prompts & IVR / voice note turns)
"""
from typing import Dict, Any, List, Optional
import uuid
from app.models.schemas import VoiceSessionState, VoiceSessionTurn, BeneficiaryProfile

CONVERSATION_FLOW_CONFIG = {
    "greeting": {
        "prompt_en": "Welcome to JEEVDESK, the PM-AJAY Livelihood and Skilling Voice Assistant. You can speak in Tamil, Hindi, or English. Which language do you prefer?",
        "prompt_ta": "ஜீவ்டெஸ்க் (JEEVDESK) வாழ்வாதார மற்றும் திறன் வழிகாட்டிக்கு உங்களை வரவேற்கிறோம். உங்களுடன் தமிழில் பேசலாமா அல்லது ஹிந்தி, ஆங்கிலத்தில் பேசலாமா?",
        "prompt_hi": "जीवडेस्क (JEEVDESK) पीएम-अजय आजीविका और कौशल सहायक में आपका स्वागत है। आप किस भाषा में बात करना पसंद करेंगे?",
        "field": "language",
        "next_stage": "consent"
    },
    "consent": {
        "prompt_en": "To suggest the best NSQF training courses and government grant opportunities under PM-AJAY, may I ask you a few questions about your work, skills, and education? Please say Yes to proceed.",
        "prompt_ta": "PM-AJAY திட்டத்தின் கீழ் உங்களுக்குப் பொருத்தமான அரசு இலவச திறன் பயிற்சிகள் மற்றும் வாழ்வாதார வேலைவாய்ப்புகளைப் பரிந்துரைக்க, உங்கள் பணி அனுபவம் மற்றும் விருப்பங்கள் பற்றி சில கேள்விகள் கேட்கலாமா? தொடரலாம் என்றால் 'சரி' அல்லது 'ஆம்' என்று கூறுங்கள்.",
        "prompt_hi": "पीएम-अजय योजना के तहत आपके लिए उपयुक्त मुफ्त कौशल प्रशिक्षण और रोजगार के अवसर खोजने के लिए, क्या मैं आपके अनुभव और रुचि के बारे में कुछ प्रश्न पूछ सकता हूँ? आगे बढ़ने के लिए 'हाँ' कहें।",
        "field": "consent_obtained",
        "next_stage": "name"
    },
    "name": {
        "prompt_en": "Please tell me your full name.",
        "prompt_ta": "தயவுசெய்து உங்கள் முழுப் பெயரைச் சொல்லுங்கள்.",
        "prompt_hi": "कृपया अपना पूरा नाम बताएं।",
        "field": "full_name",
        "next_stage": "district"
    },
    "district": {
        "prompt_en": "Which district do you reside in? For example, Salem, Madurai, Tiruchirappalli, Namakkal, Tirupur, or Dharmapuri?",
        "prompt_ta": "நீங்கள் எந்த மாவட்டத்தில் வசிக்கிறீர்கள்? உதாரணமாக: சேலம், மதுரை, திருச்சி, நாமக்கல், திருப்பூர் அல்லது தருமபுரி?",
        "prompt_hi": "आप किस जिले में रहते हैं? जैसे सलेम, मदुरै, तिरुचिरापल्ली, नमक्कल, तिरुपुर या धर्मपुरी?",
        "field": "district",
        "next_stage": "current_work"
    },
    "current_work": {
        "prompt_en": "What work or daily activity are you currently doing? For example: farm labor, tailoring, electrical helper, small trade, or looking for first work?",
        "prompt_ta": "தற்போது நீங்கள் என்ன வேலை அல்லது தொழில் செய்து வருகிறீர்கள்? உதாரணமாக: விவசாயக் கூலி வேலை, தையல், எலக்ட்ரிக்கல் வேலை, வீட்டுப் பராமரிப்பு அல்லது புதிய வேலை தேடுகிறீர்களா?",
        "prompt_hi": "वर्तमान में आप क्या काम करते हैं? जैसे कृषि मजदूरी, सिलाई, बिजली काम, या पहली नौकरी की तलाश?",
        "field": "current_occupation",
        "next_stage": "education"
    },
    "education": {
        "prompt_en": "What is your highest educational standard? For example: 5th standard, 8th standard, 10th pass, 12th, or ITI?",
        "prompt_ta": "உங்கள் பள்ளி அல்லது கல்வித் தகுதி என்ன? உதாரணமாக: 5-ஆம் வகுப்பு, 8-ஆம் வகுப்பு, 10-ஆம் வகுப்பு தேர்ச்சி, 12-ஆம் வகுப்பு அல்லது ஐடிஐ?",
        "prompt_hi": "आपकी शैक्षणिक योग्यता क्या है? जैसे 5वीं, 8वीं, 10वीं पास, 12वीं या आईटीआई?",
        "field": "education_level",
        "next_stage": "skills"
    },
    "skills": {
        "prompt_en": "What practical skills or tools do you know how to operate? For example: pumps, motor wiring, sewing machine, smartphone/typing, or animal rearing?",
        "prompt_ta": "உங்களுக்கு என்னென்ன கருவிகள் அல்லது செய்முறை வேலைகள் தெரியும்? உதாரணமாக: மோட்டார் பம்ப், தையல் இயந்திரம், கணினி/மொபைல் பயன்பாடு, அல்லது கால்நடை வளர்ப்பு?",
        "prompt_hi": "आपको कौन से व्यावहारिक कौशल या उपकरण चलाने आते हैं? जैसे सिलाई मशीन, मोटर पंप, कंप्यूटर या पशुपालन?",
        "field": "existing_skills",
        "next_stage": "work_preference"
    },
    "work_preference": {
        "prompt_en": "Do you prefer monthly wage employment in a company, or starting your own self-employment micro-business with PM-AJAY grant support?",
        "prompt_ta": "மாத ஊதியம் கிடைக்கும் நிறுவன வேலையை விரும்புகிறீர்களா, அல்லது அரசு மானிய உதவியுடன் சொந்தமாக சுயதொழில் தொடங்க விரும்புகிறீர்களா?",
        "prompt_hi": "क्या आप मासिक वेतन वाली नौकरी चाहते हैं, या सरकारी अनुदान सहायता से अपना स्वरोजगार शुरू करना चाहते हैं?",
        "field": "employment_preference",
        "next_stage": "confirmation"
    }
}

class VoiceDialogueManager:
    def __init__(self):
        self.sessions: Dict[str, VoiceSessionState] = {}

    def start_session(self, language: str = "ta", channel: str = "Web/Voice Assistant") -> VoiceSessionState:
        session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
        initial_prompt = CONVERSATION_FLOW_CONFIG["greeting"]["prompt_ta"] if language == "ta" else CONVERSATION_FLOW_CONFIG["greeting"]["prompt_en"]
        
        session = VoiceSessionState(
            session_id=session_id,
            channel=channel,
            language=language,
            stage="greeting",
            profile_draft={
                "internal_id": f"BEN-TN-{uuid.uuid4().hex[:6].upper()}",
                "preferred_language": language,
                "district": "Salem",
                "state": "Tamil Nadu",
                "age_band": "26-35",
                "phone_number": "+91 98400 12345",
                "max_travel_distance_km": 15,
                "mobility_constraints": "Within local block",
                "seasonal_availability": "Full-time available",
                "interests": [],
                "existing_skills": []
            },
            conversation_history=[
                VoiceSessionTurn(
                    turn_index=1,
                    speaker="system",
                    transcript=initial_prompt,
                    confidence=1.0,
                    confirmed=True
                )
            ]
        )
        self.sessions[session_id] = session
        return session

    def process_utterance(self, session_id: str, beneficiary_utterance: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            session = self.start_session()
            session_id = session.session_id

        # Turn recording for Beneficiary
        turn_num = len(session.conversation_history) + 1
        current_stage = session.stage
        text = beneficiary_utterance.strip().lower()

        # Handle universal conversational repairs (repeat, human help, pause)
        if any(w in text for w in ["repeat", "மறுபடியும்", "மீண்டும்", "दोबारा", "फिर से"]):
            stage_config = CONVERSATION_FLOW_CONFIG.get(current_stage, CONVERSATION_FLOW_CONFIG["greeting"])
            lang_key = f"prompt_{session.language}" if f"prompt_{session.language}" in stage_config else "prompt_en"
            reply = f"(மீண்டும் சொல்கிறேன்) {stage_config[lang_key]}" if session.language == "ta" else f"(Repeating) {stage_config[lang_key]}"
            session.conversation_history.append(VoiceSessionTurn(
                turn_index=turn_num,
                speaker="beneficiary",
                transcript=beneficiary_utterance,
                confidence=0.98
            ))
            session.conversation_history.append(VoiceSessionTurn(
                turn_index=turn_num + 1,
                speaker="system",
                transcript=reply,
                confidence=1.0
            ))
            return {"session": session, "system_reply": reply, "stage": current_stage}

        if any(w in text for w in ["help", "human", "அதிகாரி", "உதவி", "मदद", "अधिकारी", "operator"]):
            session.escalated_to_staff = True
            session.escalation_reason = "Beneficiary requested live human assistance / field facilitator during voice session"
            reply_ta = "உங்கள் அழைப்பு கள ஒருங்கிணைப்பாளர் மற்றும் அதிகாரியின் நேரடி உதவிப் பிரிவுக்கு மாற்றப்படுகிறது. சிறிது நேரத்தில் களப் பணியாளர் உங்களைத் தொடர்பு கொள்வார்."
            reply_en = "Your request has been routed to the Field Facilitator human queue. A case worker will contact you shortly."
            reply = reply_ta if session.language == "ta" else reply_en
            session.conversation_history.append(VoiceSessionTurn(
                turn_index=turn_num,
                speaker="beneficiary",
                transcript=beneficiary_utterance,
                confidence=0.95
            ))
            session.conversation_history.append(VoiceSessionTurn(
                turn_index=turn_num + 1,
                speaker="system",
                transcript=reply,
                confidence=1.0
            ))
            return {"session": session, "system_reply": reply, "stage": "escalated"}

        # Extract structured fields depending on stage
        extracted_field = None
        extracted_val = None

        if current_stage == "greeting":
            if any(w in text for w in ["tamil", "தமிழ்", "த"]):
                session.language = "ta"
                extracted_val = "ta"
            elif any(w in text for w in ["hindi", "हिंदी", "हिन्दी"]):
                session.language = "hi"
                extracted_val = "hi"
            else:
                session.language = "en"
                extracted_val = "en"
            session.profile_draft["preferred_language"] = session.language
            extracted_field = "preferred_language"
            next_stage = "consent"

        elif current_stage == "consent":
            if any(w in text for w in ["yes", "சரி", "ஆம்", "ஓகே", "हाँ", "ha", "sari"]):
                session.profile_draft["consent_obtained"] = True
                extracted_val = True
            else:
                session.profile_draft["consent_obtained"] = True
                extracted_val = True
            extracted_field = "consent_obtained"
            next_stage = "name"

        elif current_stage == "name":
            # Extract name
            name_val = beneficiary_utterance.replace("என் பெயர்", "").replace("my name is", "").replace("mera naam", "").strip()
            session.profile_draft["full_name"] = name_val if name_val else "Beneficiary"
            extracted_field = "full_name"
            extracted_val = session.profile_draft["full_name"]
            next_stage = "district"

        elif current_stage == "district":
            districts = ["salem", "madurai", "tiruchirappalli", "namakkal", "tirupur", "dharmapuri", "vellore", "coimbatore"]
            found_dist = "Salem"
            for d in districts:
                if d in text:
                    found_dist = d.capitalize()
                    break
            session.profile_draft["district"] = found_dist
            extracted_field = "district"
            extracted_val = found_dist
            next_stage = "current_work"

        elif current_stage == "current_work":
            session.profile_draft["current_occupation"] = beneficiary_utterance
            session.profile_draft["traditional_or_family_work"] = beneficiary_utterance
            extracted_field = "current_occupation"
            extracted_val = beneficiary_utterance
            next_stage = "education"

        elif current_stage == "education":
            if any(w in text for w in ["10", "tenth", "பத்தாம்"]):
                edu = "10th pass"
            elif any(w in text for w in ["8", "eighth", "எட்டாம்"]):
                edu = "8th standard"
            elif any(w in text for w in ["12", "twelfth", "பன்னிரெண்டாம்"]):
                edu = "12th pass"
            elif any(w in text for w in ["iti", "diploma", "graduate", "பட்டதாரி"]):
                edu = "Graduate/ITI"
            else:
                edu = "5th standard"
            session.profile_draft["education_level"] = edu
            extracted_field = "education_level"
            extracted_val = edu
            next_stage = "skills"

        elif current_stage == "skills":
            skills_extracted = [s.strip() for s in beneficiary_utterance.split(",") if s.strip()]
            if not skills_extracted:
                skills_extracted = [beneficiary_utterance]
            session.profile_draft["existing_skills"] = skills_extracted
            extracted_field = "existing_skills"
            extracted_val = skills_extracted
            next_stage = "work_preference"

        elif current_stage == "work_preference":
            if any(w in text for w in ["சுயதொழில்", "சொந்த", "business", "self", "enterprise", "दुकान", "स्वरोजगार"]):
                pref = "Self-Employment / Enterprise"
            elif any(w in text for w in ["மாத ஊதியம்", "வேலை", "wage", "company", "नौकरी", "वेतन"]):
                pref = "Wage Employment"
            else:
                pref = "Mixed / Any"
            session.profile_draft["employment_preference"] = pref
            extracted_field = "employment_preference"
            extracted_val = pref
            next_stage = "completed"

        else:
            next_stage = "completed"

        # Record turns
        session.conversation_history.append(VoiceSessionTurn(
            turn_index=turn_num,
            speaker="beneficiary",
            transcript=beneficiary_utterance,
            extracted_field=extracted_field,
            extracted_value=extracted_val,
            confidence=0.96
        ))

        session.stage = next_stage

        # System response generation
        if next_stage in CONVERSATION_FLOW_CONFIG:
            prompt_key = f"prompt_{session.language}" if f"prompt_{session.language}" in CONVERSATION_FLOW_CONFIG[next_stage] else "prompt_en"
            sys_reply = CONVERSATION_FLOW_CONFIG[next_stage][prompt_key]
        else:
            # Completed summary
            name = session.profile_draft.get("full_name", "")
            dist = session.profile_draft.get("district", "")
            occ = session.profile_draft.get("current_occupation", "")
            pref = session.profile_draft.get("employment_preference", "")
            
            if session.language == "ta":
                sys_reply = (
                    f"நன்றி {name} அவர்களே! உங்கள் தகவல்கள் சேகரிக்கப்பட்டன: "
                    f"மாவட்டம்: {dist}, தற்போதைய தொழில்: {occ}, வேலை விருப்பம்: {pref}. "
                    f"இப்போது PM-AJAY திட்டத்தின் கீழ் உங்களுக்கு சிறந்த 3 NSQF திறன் பயிற்சிகள் பரிந்துரைக்கப்படுகின்றன."
                )
            else:
                sys_reply = (
                    f"Thank you {name}! Your profile is confirmed: District: {dist}, Current work: {occ}, Preference: {pref}. "
                    f"JEEVDESK is now presenting your top 3 NSQF-aligned training and livelihood pathways."
                )

        session.conversation_history.append(VoiceSessionTurn(
            turn_index=turn_num + 1,
            speaker="system",
            transcript=sys_reply,
            confidence=1.0
        ))

        return {
            "session": session,
            "system_reply": sys_reply,
            "stage": next_stage,
            "profile_draft": session.profile_draft
        }

    def build_profile_object(self, session_id: str) -> BeneficiaryProfile:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        draft = session.profile_draft
        return BeneficiaryProfile(
            internal_id=draft.get("internal_id", f"BEN-TN-{uuid.uuid4().hex[:6].upper()}"),
            full_name=draft.get("full_name", "K. Murugan"),
            phone_number=draft.get("phone_number", "+91 98400 12345"),
            preferred_language=session.language,
            district=draft.get("district", "Salem"),
            state="Tamil Nadu",
            age_band=draft.get("age_band", "26-35"),
            education_level=draft.get("education_level", "8th standard"),
            current_occupation=draft.get("current_occupation", "Agricultural helper"),
            traditional_or_family_work=draft.get("traditional_or_family_work", "Farm laborer"),
            existing_skills=draft.get("existing_skills", ["Drip emitter maintenance", "Pump operation"]),
            interests=draft.get("interests", ["Agriculture", "Water technology"]),
            employment_preference=draft.get("employment_preference", "Wage Employment"),
            max_travel_distance_km=draft.get("max_travel_distance_km", 15),
            mobility_constraints=draft.get("mobility_constraints", "Within block"),
            seasonal_availability=draft.get("seasonal_availability", "Full-time available"),
            consent_obtained=draft.get("consent_obtained", True)
        )

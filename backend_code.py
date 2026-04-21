import os
import google.generativeai as genai
import json
import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import time
import re

# ----------------------------
# Firebase + Environment Setup
# ----------------------------
load_dotenv(dotenv_path=".env")

api_key = os.getenv("API_KEY")
firebase_config = os.getenv("FIREBASE_CONFIG")

if not api_key:
    raise ValueError("API_KEY is missing. Check your .env file.")

genai.configure(api_key=api_key)

if not firebase_admin._apps:
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG is not set in .env")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ----------------------------
# Database Helpers
# ----------------------------
def addDataToDatabase(prompt, response):
    data = {"user": prompt, "bot": response, "time": datetime.datetime.now()}
    db.collection("chat").add(data)


def addFormDataToDatabase(name, symptoms, prediction, final_disease=None):
    data = {
        "name": name,
        "symptoms": symptoms,
        "prediction": prediction,
        "final_disease": final_disease if final_disease else "Not confirmed",
        "time": datetime.datetime.now()
    }
    db.collection("disease_form").add(data)


def retrieveDataFromDatabase():
    history = db.collection("chat").order_by("time").get()
    return [chat.to_dict() for chat in history]


def retrieveFormDataFromDatabase():
    history = db.collection("disease_form").order_by("time").get()
    return [entry.to_dict() for entry in history]


# ----------------------------
# Rule-based Disease Detection
# ----------------------------
def check_disease_rules(symptoms_list):
    disease_rules = {
        "Cholera": ["diarrhea", "watery stool", "vomiting", "dehydration", "sunken eyes", "dry mouth", "cramps"],
        "Typhoid": ["fever", "headache", "abdominal pain", "constipation", "diarrhea"],
        "Dysentery": ["bloody diarrhea", "abdominal cramps", "nausea", "vomiting"],
        "Hepatitis A/E": ["jaundice", "yellow eyes", "dark urine", "fatigue", "loss of appetite"]
    }

    matched = []
    for disease, indicators in disease_rules.items():
        for s in symptoms_list:
            if any(keyword in s.lower() for keyword in indicators):
                matched.append(disease)

    return list(set(matched))


# ----------------------------
# Disease Info
# ----------------------------
disease_info = {
    "Cholera": {
        "precautions": "Drink clean water, maintain hygiene, avoid contaminated food.",
        "medicines": "ORS, antibiotics (only if prescribed), rehydration therapy."
    },
    "Typhoid": {
        "precautions": "Avoid outside food, drink boiled water, maintain sanitation.",
        "medicines": "Antibiotics (doctor prescribed), paracetamol for fever."
    },
    "Dysentery": {
        "precautions": "Wash hands, avoid contaminated food/water.",
        "medicines": "ORS, antibiotics (if severe), anti-diarrheal meds."
    },
    "Hepatitis A/E": {
        "precautions": "Avoid oily food, maintain hygiene, drink safe water.",
        "medicines": "Rest, hydration, liver-friendly diet."
    }
}


# ----------------------------
# Utility Functions
# ----------------------------
def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else "{}"


def extract_symptoms_from_text(text):
    text = text.lower()

    phrases = ["i have", "i am having", "i feel", "since", "from"]
    for p in phrases:
        text = text.replace(p, "")

    text = text.replace(" and ", ",")
    text = text.replace(" with ", ",")

    parts = re.split(r'[,.]', text)

    cleaned = []
    for p in parts:
        p = p.strip()
        if len(p) > 2:
            cleaned.append(p)

    return cleaned


def extract_name_and_symptoms(text):
    text = text.strip()

    name_match = re.search(r"my name is (\w+)", text.lower())
    if name_match:
        name = name_match.group(1).capitalize()
    else:
        name = "User"

    cleaned_text = re.sub(r"my name is \w+", "", text.lower())
    symptoms_list = extract_symptoms_from_text(cleaned_text)

    return name, ", ".join(symptoms_list)


# ----------------------------
# AI + Processing Functions
# ----------------------------
def interpret_command_with_gpt(command):
    prompt = f"""
    You are an AI assistant. Always return ONLY valid JSON.
    Format:
    {{
    "kind": "<type>",
    "parameters": {{ ... }}
    }}

    Types:
    - disease_prediction
    - general_chat
    - mathematics
    - date_time

    input: {command}
    output:
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        raw = response.text.strip()
        cleaned = extract_json(raw)
        return cleaned

    except Exception:
        name, symptoms = extract_name_and_symptoms(command)

        return json.dumps({
            "kind": "disease_prediction",
            "parameters": {
                "name": name,
                "symptoms": symptoms,
                "prediction": "Fallback mode"
            }
        })


def process_interpreted_command(interpreted_command):
    try:
        command_data = json.loads(interpreted_command)
    except Exception:
        return "Error: AI returned invalid format."

    kind = command_data.get("kind")
    parameters = command_data.get("parameters", {})

    if kind == "generate_code":
        return parameters.get("code", "")

    elif kind == "general_chat":
        return parameters.get("response", "No response provided.")

    elif kind == "mathematics":
        return parameters.get("result", "Error evaluating expression.")

    elif kind == "date_time":
        response = parameters.get("response", "")
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M")
        response = response.replace("{{current_date}}", current_date)
        response = response.replace("{{current_time}}", current_time)
        return response

    elif kind == "disease_prediction":
        name = parameters.get("name", "User")
        symptoms = parameters.get("symptoms", "")

        symptoms_list = extract_symptoms_from_text(symptoms)
        matched_diseases = check_disease_rules(symptoms_list)

        if matched_diseases:
            final_disease = ", ".join(matched_diseases)

            details = ""
            for d in matched_diseases:
                info = disease_info.get(d, {})
                precautions = info.get("precautions", "N/A")
                medicines = info.get("medicines", "N/A")
                details += f"\n\n🔹 {d}:\nPrecautions: {precautions}\nMedicines: {medicines}"

            prediction = f"You may have: {final_disease}.{details}\n\n⚠️ Please consult a doctor."
        else:
            final_disease = None
            prediction = "Symptoms are unclear. Please consult a doctor."

        addFormDataToDatabase(name, symptoms, prediction, final_disease)

        return f"Hi {name}, based on your symptoms ({symptoms}), {prediction}"

    else:
        return "I couldn't quite understand that."


# ----------------------------
# UI Response
# ----------------------------
def writeAssistantResponse(response):
    with st.chat_message("assistant"):
        placeholder = st.empty()
        typed_message = ""

        for char in response:
            typed_message += char
            placeholder.markdown(typed_message)
            time.sleep(0.03)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })


def delete_all_records():
    docs = db.collection("disease_form").get()
    deleted_count = 0

    for doc in docs:
        db.collection("disease_form").document(doc.id).delete()
        deleted_count += 1

    return deleted_count


def backfill_final_disease():
    """Update old records to include final_disease column."""
    docs = db.collection("disease_form").get()
    updated_count = 0

    for doc in docs:
        data = doc.to_dict()

        if "final_disease" not in data:
            symptoms_list = extract_symptoms_from_text(data.get("symptoms", ""))
            matched = check_disease_rules(symptoms_list)

            final_disease = ", ".join(matched) if matched else "Not confirmed"

            db.collection("disease_form").document(doc.id).update({
                "final_disease": final_disease
            })

            updated_count += 1

    return updated_count

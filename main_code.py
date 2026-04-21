import streamlit as st
from backend_code import (
    interpret_command_with_gpt,
    process_interpreted_command,
    writeAssistantResponse,
    retrieveDataFromDatabase,
    addDataToDatabase,
    retrieveFormDataFromDatabase,
    backfill_final_disease,
    delete_all_records,
    check_disease_rules,              
    extract_symptoms_from_text,
    extract_name_and_symptoms
)

# ------------------------------
# Session Initialization
# ------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_chatbot" not in st.session_state:
    st.session_state.show_chatbot = False
if "context" not in st.session_state:
    st.session_state.context = ""

# ------------------------------
# App Title
# ------------------------------
st.markdown("""
<h1 style='text-align: center; color:#38bdf8;'>💧 Smart Health Assistant</h1>
<p style='text-align: center; color:#cbd5f5; font-size:16px;'>
AI + Rule-based Water-borne Disease Detection
</p>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* DARK MODE BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}

/* INPUT FIELDS */
.stTextInput>div>div>input,
.stTextArea textarea {
    background-color: #1e293b;
    color: white;
    border-radius: 10px;
    border: 1px solid #38bdf8;
}

/* BUTTON */
.stButton>button {
    background-color: #38bdf8;
    color: black;
    border-radius: 10px;
    font-weight: bold;
}

/* HEADINGS */
h1, h2, h3 {
    color: #38bdf8;
}

/* CHAT BUBBLE */
div[data-testid="stChatMessage"] {
    background-color: #1e293b !important;
    border-radius: 10px;
    padding: 10px;
}

</style>
""", unsafe_allow_html=True)
# ------------------------------
# Mode Selection
# ------------------------------
mode = st.radio("Choose Mode:", ["Disease Form", "Chatbot", "View Predictions"])

# ------------------------------
# FORM MODE
# ------------------------------
if mode == "Disease Form":
    st.subheader("Predict Disease from Symptoms")
    with st.form("disease_form"):
        name = st.text_input("Enter your name")
        symptoms = st.text_area("Enter your symptoms")
        submitted = st.form_submit_button("Predict Disease")

        if submitted:
            if name.strip() == "" or symptoms.strip() == "":
                st.warning("⚠️ Please enter both name and symptoms.")
            else:
                prompt = f"My name is {name} and I have {symptoms}"

                try:
                    interpreted_command = interpret_command_with_gpt(prompt)
                    response = process_interpreted_command(interpreted_command)

                except Exception as e:
                    symptoms_list = extract_symptoms_from_text(symptoms)
                    matched = check_disease_rules(symptoms_list)

                    if matched:
                        response = f"You may have: {', '.join(matched)}"
                    else:
                        response = "Could not detect disease. Please consult a doctor."

                    print("FALLBACK ERROR:", str(e))

                st.markdown(f"""
                    <div style='
                        padding:15px; 
                        border-radius:12px; 
                        background:linear-gradient(135deg, #1e293b, #0f172a);
                        color:white;
                        border:1px solid #38bdf8;
                        box-shadow: 0 0 10px rgba(56,189,248,0.3);
                    '>
                    {response}
                    </div>
                    """, unsafe_allow_html=True)

# ------------------------------
# CHAT MODE
# ------------------------------
elif mode == "Chatbot":
    st.subheader("Chat with the Health Assistant")

    if st.button("Start Chatting"):
        st.session_state.show_chatbot = True
        st.session_state.messages = []

        response = "Hi there, how can I assist you with your health concerns today?"
        st.session_state.context += f"Bot: {response}\n"

        st.session_state.messages.append({"role": "assistant", "content": response})

    if st.session_state.show_chatbot:
        # Display previous messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Handle new user input
        if prompt := st.chat_input("Type your symptoms or query..."):
            with st.chat_message("user"):
                st.markdown(prompt)

            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.context += f"User: {prompt}\n"
            st.session_state.context = st.session_state.context[-1000:]

            # AI processing
            full_prompt = f"Previous chat context: {st.session_state.context}\n\nCurrent message: {prompt}"

            try:
                interpreted_command = interpret_command_with_gpt(full_prompt)
                response = process_interpreted_command(interpreted_command)

            except Exception as e:
                # 🔥 FULL FALLBACK MODE
                symptoms_list = extract_symptoms_from_text(prompt)
                matched = check_disease_rules(symptoms_list)

                if matched:
                    response = f"You may have: {', '.join(matched)}"
                else:
                    response = "I'm not sure about the condition. Please consult a doctor."

                print("FALLBACK ERROR:", str(e))

            st.session_state.context += f"Bot: {response}\n"

            addDataToDatabase(prompt, response)
            writeAssistantResponse(response)

# ------------------------------
# ADMIN PANEL
# ------------------------------
elif mode == "View Predictions":
    st.subheader("Admin Panel - Disease Predictions 📝")

    admin_pass = st.text_input("Enter admin password", type="password")

    if admin_pass == "abc@987":
        data = retrieveFormDataFromDatabase()

        if not data:
            st.info("No predictions stored yet.")
        else:
            import pandas as pd
            df = pd.DataFrame(data)

            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"])

            cols_to_show = ["name", "symptoms", "final_disease", "prediction", "time"]
            available_cols = [c for c in cols_to_show if c in df.columns]
            st.dataframe(df[available_cols])

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download as CSV", csv, "predictions.csv", "text/csv")

            if st.button("Backfill old records with Final Disease"):
                count = backfill_final_disease()
                st.success(f"✅ Updated {count} old records.")

            if st.button("Delete ALL old records from database"):
                count = delete_all_records()
                st.success(f"🗑️ Deleted {count} records.")

    else:
        st.warning("⚠️ Admin access required")
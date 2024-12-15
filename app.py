from flask import Flask, request, jsonify
from docx import Document
import PyPDF2
import re
import os

app = Flask(__name__)

# Predefined list of technical and soft skills
skills_list = [
    "Python", "Java", "Kotlin", "Machine Learning", "Data Analysis",
    "Communication", "Leadership", "Problem Solving", "Teamwork",
    "Android Development", "Firebase", "Google ML Kit", "MongoDB","C","C++",
    "DSA","CA","C#","JavaScript","Swift","DBMS","OOP","Data Science","AIML",
    "Node JS","Express JS","React JS","React Native","Web development"
]

# Helper functions for extracting text from files
def extract_text_docx(file_path):
    doc = Document(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text()
    return text

# Preprocessing text to remove unnecessary whitespaces
def preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text.strip()

# Extract Name
def extract_name(text):
    name_keywords = ["name", "full name"]
    lines = text.split("\n")
    for line in lines:
        if any(keyword in line.lower() for keyword in name_keywords):
            return line.split(":")[-1].strip()
    for line in lines:
        if line.strip():
            return line.strip()
    return "Not Found"

# Extract Contact Number
def extract_contact(text):
    phone_regex = r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    match = re.search(phone_regex, text)
    return match.group() if match else "Not Found"

# Extract Email
def extract_email(text):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_regex, text)
    return match.group() if match else "Not Found"

# Extract Profile Summary (Assumes it is the first 3-5 lines of the text)
def extract_profile_summary(text):
    lines = text.split("\n")
    return " ".join(lines[:5]).strip() if lines else "Not Found"

# Extract Skills
def extract_skills_from_section(text):
    return [skill for skill in skills_list if skill.lower() in text.lower()]

# Calculate Match Score
def calculate_match_score(resume_skills, desired_skills):
    set_resume_skills = set(resume_skills)
    set_desired_skills = set(desired_skills)
    match_score = len(set_resume_skills.intersection(set_desired_skills)) / len(set_desired_skills)
    return match_score

@app.route('/evaluate', methods=['POST'])
def evaluate_resume():
    try:
        # Get desired skills and uploaded file from the request
        desired_skills = request.form.get("desired_skills").split(",")
        file = request.files["resume"]

        # Save the file temporarily
        file_path = f"./{file.filename}"
        file.save(file_path)

        # Determine file type and extract text
        file_type = file.filename.split(".")[-1].lower()
        if file_type == "docx":
            text = extract_text_docx(file_path)
        elif file_type == "pdf":
            text = extract_text_pdf(file_path)
        else:
            os.remove(file_path)
            return jsonify({"error": "Unsupported file type"}), 400

        # Preprocess the text
        processed_text = preprocess_text(text)

        # Extract details
        name = extract_name(processed_text)
        contact = extract_contact(processed_text)
        email = extract_email(processed_text)
        profile_summary = extract_profile_summary(processed_text)
        resume_skills = extract_skills_from_section(processed_text)
        match_score = calculate_match_score(resume_skills, desired_skills)
        result = "Suitable" if match_score >= 0.5 else "Not Suitable"

        # Clean up temporary file
        os.remove(file_path)

        # Return all extracted information
        return jsonify({
            # "name": name,
            "contact": contact,
            "email": email,
            "profile_summary": profile_summary,
            "resume_skills": resume_skills,
            "desired_skills": desired_skills,
            "match_score": round(match_score, 2),
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

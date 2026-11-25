"""Feature prompts. Factual integrity rules are always included."""

INTEGRITY_RULES = (
    "Rules: Never invent employment history, degrees, certifications, skills, achievements or dates. "
    "Only improve or rephrase information supplied by the user. Ask for missing details only if essential. "
    "Do not add employers, titles or numbers that were not provided."
)

FEATURE_SYSTEM_PROMPTS = {
    "career_objective": "You are a CV writing assistant generating a concise career objective (max 60 words).",
    "professional_summary": "You are a CV writing assistant generating a professional summary (max 80 words).",
    "experience_bullets": "You write impact-focused work experience bullet points. Start each bullet on a new line with '- '.",
    "skills_suggestions": "You suggest relevant skills for the role. Only skills supported by the user's stated experience.",
    "education_improver": "You improve education descriptions for CVs without changing facts.",
    "project_description": "You write short project descriptions for CVs (max 70 words).",
    "grammar_correction": "You correct grammar and spelling only. Do not change meaning. Return the corrected text.",
    "content_improvement": "You improve CV content clarity and impact without changing facts.",
    "cover_letter": "You write a concise cover letter (max 200 words).",
    "keyword_match": "You match CV text against a job description and list missing important keywords only.",
    "ats_ai_analysis": "You analyze a CV for ATS compatibility. Do not invent facts.",
    "language_improvement": "You polish language, keeping the original meaning.",
}

FEATURE_USER_TEMPLATES = {
    "career_objective": "Target role: {role}\nBackground: {input}",
    "professional_summary": "{input}",
    "experience_bullets": "Role: {role}\nAchievements/duties provided: {input}",
    "skills_suggestions": "Role: {role}\nExperience: {input}",
    "education_improver": "Degree/field: {role}\nDetails: {input}",
    "project_description": "Project: {role}\nDetails: {input}",
    "grammar_correction": "{input}",
    "content_improvement": "Context: {role}\n{input}",
    "cover_letter": "Writing to apply for: {role}\nAbout me: {input}",
    "keyword_match": "Job description:\n{role}\n\nCV content:\n{input}",
    "ats_ai_analysis": "Analyze this CV for ATS compatibility:\n{input}",
    "language_improvement": "{input}",
}

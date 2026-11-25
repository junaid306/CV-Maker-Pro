from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.resumes.models import Resume, ResumeSection
from apps.resumes.services import build_render_data

from .engine import analyze_cv


GOOD_CV = {
    "full_name": "Karim Ahmed",
    "phone": "+8801712345678",
    "email": "karim@example.com",
    "address": "Dhaka",
    "professional_summary": "Software engineer with five years of experience building mobile and web applications for startups and enterprises in fintech.",
    "skills": [{"name": "Flutter"}, {"name": "Django"}, {"name": "Python"}, {"name": "MySQL"}, {"name": "Docker"}],
    "experience": [{"company": "Tech Ltd", "position": "Engineer", "description": "Built apps."}],
    "education": [{"degree": "BSc CSE", "institution": "DU", "year": "2020"}],
}


class EngineTests(APITestCase):
    def test_good_cv_scores_reasonably(self):
        result = analyze_cv(GOOD_CV)
        self.assertGreaterEqual(result["total_score"], 70)
        self.assertIn("disclaimer", result)

    def test_empty_cv_scores_low(self):
        result = analyze_cv({})
        self.assertLessEqual(result["total_score"], 35)

    def test_job_description_missing_keywords(self):
        jd = "We need Kubernetes, Terraform and GraphQL experience."
        result = analyze_cv(GOOD_CV, job_description=jd)
        self.assertIn("kubernetes", result["missing_keywords"])

    def test_service_analyses_resume(self):
        user = User.objects.create_user(email="ats@x.com", password="ChangeMe123")
        resume = Resume.objects.create(user=user, data={k: GOOD_CV.get(k) for k in ("full_name", "phone", "email")})
        for key in ("skills", "experience", "education"):
            ResumeSection.objects.create(resume=resume, key=key, data={"entries": GOOD_CV.get(key, [])})
        data = build_render_data(resume)
        self.assertEqual(data["full_name"], "Karim Ahmed")
        result = analyze_cv(data)
        self.assertGreater(result["total_score"], 0)

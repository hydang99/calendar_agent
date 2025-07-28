import os
import json
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAI
import googlemaps
from dotenv import load_dotenv

load_dotenv()

class VietnamSchoolQAAgent:
    """
    Intelligent QA chatbot for Vietnamese schools and colleges with global coverage.
    Provides comprehensive information about educational institutions.
    """
    
    def __init__(self, 
                 vertex_project_id: str = None,
                 vertex_location: str = "us-central1",
                 google_maps_api_key: str = None):
        """
        Initialize the Vietnam School QA Agent.
        
        Args:
            vertex_project_id: Google Cloud project ID for Vertex AI
            vertex_location: Vertex AI location
            google_maps_api_key: Google Maps API key for location services
        """
        self.vertex_project_id = vertex_project_id or os.getenv('VERTEX_PROJECT_ID')
        self.vertex_location = vertex_location
        self.google_maps_api_key = google_maps_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Initialize Vertex AI
        if self.vertex_project_id:
            try:
                aiplatform.init(project=self.vertex_project_id, location=self.vertex_location)
                
                # Try different model names in order of preference
                model_names = [
                    "gemini-1.5-flash",
                    "gemini-1.5-pro", 
                    "gemini-2.0-flash",
                    "text-bison"
                ]
                
                self.llm = None
                for model_name in model_names:
                    try:
                        self.llm = VertexAI(
                            model_name=model_name,
                            project=self.vertex_project_id,
                            location=self.vertex_location,
                            temperature=0.3,
                            max_output_tokens=2048
                        )
                        print(f"✅ Successfully initialized Vertex AI with model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"⚠️ Model {model_name} not available: {model_error}")
                        continue
                
                if self.llm is None:
                    print("⚠️ No Vertex AI models available. Agent will work with basic search only.")
                    
            except Exception as e:
                print(f"Warning: Vertex AI initialization failed: {e}")
                self.llm = None
        
        # Initialize Google Maps client
        if self.google_maps_api_key:
            self.gmaps = googlemaps.Client(key=self.google_maps_api_key)
        
        # Load Vietnam education system knowledge
        self.vietnam_education_knowledge = self._load_vietnam_education_knowledge()
        
        # Initialize school database
        self.school_database = self._initialize_school_database()
        
        print("🎓 Vietnam School QA Agent initialized successfully!")
    
    def _load_vietnam_education_knowledge(self) -> Dict[str, Any]:
        """Load comprehensive knowledge about Vietnam's education system."""
        return {
            "education_levels": {
                "mầm_non": {
                    "english": "Pre-school/Kindergarten",
                    "ages": "3-5 years",
                    "description": "Early childhood education in Vietnam"
                },
                "tiểu_học": {
                    "english": "Primary School",
                    "ages": "6-10 years", 
                    "grades": "1-5",
                    "description": "Compulsory primary education"
                },
                "trung_học_cơ_sở": {
                    "english": "Lower Secondary School",
                    "ages": "11-14 years",
                    "grades": "6-9", 
                    "description": "Compulsory lower secondary education"
                },
                "trung_học_phổ_thông": {
                    "english": "Upper Secondary School",
                    "ages": "15-17 years",
                    "grades": "10-12",
                    "description": "Non-compulsory upper secondary education"
                },
                "đại_học": {
                    "english": "University",
                    "duration": "4-6 years",
                    "description": "Higher education leading to bachelor's degree"
                },
                "cao_đẳng": {
                    "english": "College",
                    "duration": "2-3 years", 
                    "description": "Vocational higher education"
                }
            },
            "top_universities": {
                "vietnam_national_university_hanoi": {
                    "vietnamese_name": "Đại học Quốc gia Hà Nội",
                    "location": "Hanoi",
                    "type": "Public",
                    "ranking": "Top 1-2 in Vietnam",
                    "specialties": ["Engineering", "Natural Sciences", "Social Sciences", "Economics"]
                },
                "vietnam_national_university_hcmc": {
                    "vietnamese_name": "Đại học Quốc gia TP.HCM", 
                    "location": "Ho Chi Minh City",
                    "type": "Public",
                    "ranking": "Top 1-2 in Vietnam",
                    "specialties": ["Engineering", "Medicine", "Economics", "Law"]
                },
                "hanoi_university_of_science_and_technology": {
                    "vietnamese_name": "Đại học Bách khoa Hà Nội",
                    "location": "Hanoi",
                    "type": "Public",
                    "ranking": "Top 3 in Vietnam",
                    "specialties": ["Engineering", "Technology", "Computer Science"]
                },
                "university_of_medicine_and_pharmacy_hcmc": {
                    "vietnamese_name": "Đại học Y Dược TP.HCM",
                    "location": "Ho Chi Minh City", 
                    "type": "Public",
                    "ranking": "Top medical school",
                    "specialties": ["Medicine", "Pharmacy", "Dentistry"]
                }
            },
            "admission_system": {
                "national_high_school_exam": {
                    "vietnamese_name": "Kỳ thi tốt nghiệp THPT Quốc gia",
                    "subjects": ["Literature", "Mathematics", "Foreign Language", "Specialized subjects"],
                    "purpose": "High school graduation and university admission"
                },
                "university_admission": {
                    "methods": ["National exam scores", "Direct admission", "International programs"],
                    "scoring": "Scale of 0-10",
                    "competitive": "Highly competitive for top universities"
                }
            },
            "regions": {
                "northern_vietnam": {
                    "major_cities": ["Hanoi", "Hai Phong", "Nam Dinh"],
                    "education_hubs": ["Hanoi - Capital with top universities"]
                },
                "central_vietnam": {
                    "major_cities": ["Da Nang", "Hue", "Quang Nam"],
                    "education_hubs": ["Hue - Historic university city", "Da Nang - Modern education center"]
                },
                "southern_vietnam": {
                    "major_cities": ["Ho Chi Minh City", "Can Tho", "Vung Tau"],
                    "education_hubs": ["Ho Chi Minh City - Largest education center"]
                }
            }
        }
    
    def _initialize_school_database(self) -> Dict[str, List[Dict]]:
        """Initialize comprehensive school database with Vietnamese and international schools."""
        return {
            "universities_vietnam": [
                {
                    "name": "Vietnam National University, Hanoi",
                    "vietnamese_name": "Đại học Quốc gia Hà Nội",
                    "location": "Hanoi",
                    "type": "Public",
                    "founded": 1906,
                    "ranking_vietnam": 1,
                    "programs": ["Engineering", "Natural Sciences", "Social Sciences", "Economics", "International Studies"],
                    "tuition_annual_vnd": "10000000-20000000",
                    "admission_score": "25-28/30",
                    "website": "https://vnu.edu.vn/",
                    "contact": {
                        "phone": "+84-24-3754-7506",
                        "email": "info@vnu.edu.vn",
                        "address": "144 Xuân Thủy, Cầu Giấy, Hà Nội"
                    }
                },
                {
                    "name": "Vietnam National University, Ho Chi Minh City",
                    "vietnamese_name": "Đại học Quốc gia TP.HCM",
                    "location": "Ho Chi Minh City",
                    "type": "Public", 
                    "founded": 1995,
                    "ranking_vietnam": 2,
                    "programs": ["Engineering", "Medicine", "Economics", "Law", "Information Technology"],
                    "tuition_annual_vnd": "12000000-25000000",
                    "admission_score": "24-27/30",
                    "website": "https://vnuhcm.edu.vn/",
                    "contact": {
                        "phone": "+84-28-3724-4270",
                        "email": "info@vnuhcm.edu.vn", 
                        "address": "Quarter 6, Linh Trung Ward, Thu Duc City, Ho Chi Minh City"
                    }
                },
                {
                    "name": "Hanoi University of Science and Technology",
                    "vietnamese_name": "Đại học Bách khoa Hà Nội",
                    "location": "Hanoi",
                    "type": "Public",
                    "founded": 1956,
                    "ranking_vietnam": 3,
                    "programs": ["Engineering", "Computer Science", "Electronics", "Mechanical Engineering"],
                    "tuition_annual_vnd": "8000000-15000000",
                    "admission_score": "23-26/30",
                    "website": "https://hust.edu.vn/",
                    "contact": {
                        "phone": "+84-24-3869-2008",
                        "email": "info@hust.edu.vn",
                        "address": "1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội"
                    }
                }
            ],
            "international_schools_vietnam": [
                {
                    "name": "British International School Hanoi",
                    "location": "Hanoi",
                    "type": "International",
                    "curriculum": "British",
                    "grades": "K-12",
                    "tuition_annual_usd": "25000-35000",
                    "languages": ["English", "Vietnamese"],
                    "accreditation": ["CIS", "WASC"]
                },
                {
                    "name": "Australian International School Vietnam",
                    "location": "Ho Chi Minh City",
                    "type": "International", 
                    "curriculum": "Australian",
                    "grades": "K-12",
                    "tuition_annual_usd": "20000-30000",
                    "languages": ["English", "Vietnamese"],
                    "accreditation": ["CIS", "NEASC"]
                }
            ]
        }
    
    def search_schools(self, query: str, location: str = None, school_type: str = None, 
                      program: str = None, max_results: int = 10) -> List[Dict]:
        """
        Search for schools based on various criteria.
        
        Args:
            query: Search query (school name, program, etc.)
            location: Specific location (city, region)
            school_type: Type of school (university, college, international)
            program: Specific program or field of study
            max_results: Maximum number of results to return
            
        Returns:
            List of matching schools with detailed information
        """
        print(f"🔍 Searching schools: query='{query}', location='{location}', type='{school_type}', program='{program}'")
        
        results = []
        
        # Search Vietnamese universities
        for school in self.school_database["universities_vietnam"]:
            if self._matches_criteria(school, query, location, school_type, program):
                results.append({
                    **school,
                    "category": "Vietnamese University",
                    "match_score": self._calculate_match_score(school, query, location, program)
                })
        
        # Search international schools
        for school in self.school_database["international_schools_vietnam"]:
            if self._matches_criteria(school, query, location, school_type, program):
                results.append({
                    **school,
                    "category": "International School",
                    "match_score": self._calculate_match_score(school, query, location, program)
                })
        
        # Sort by match score and return top results
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return results[:max_results]
    
    def _matches_criteria(self, school: Dict, query: str, location: str, 
                         school_type: str, program: str) -> bool:
        """Check if a school matches the search criteria."""
        # Convert all text to lowercase for case-insensitive matching
        school_text = json.dumps(school, ensure_ascii=False).lower()
        
        # Check query match
        if query and query.lower() not in school_text:
            return False
        
        # Check location match
        if location and location.lower() not in school.get("location", "").lower():
            return False
        
        # Check school type match
        if school_type:
            if school_type.lower() == "university" and school.get("type", "").lower() != "public":
                if "university" not in school.get("name", "").lower():
                    return False
            elif school_type.lower() == "international" and school.get("type", "").lower() != "international":
                return False
        
        # Check program match
        if program:
            programs = school.get("programs", []) + school.get("curriculum", [])
            program_text = " ".join(str(p) for p in programs).lower()
            if program.lower() not in program_text:
                return False
        
        return True
    
    def _calculate_match_score(self, school: Dict, query: str, location: str, program: str) -> float:
        """Calculate a match score for ranking search results."""
        score = 0.0
        
        # Name match (highest priority)
        if query and query.lower() in school.get("name", "").lower():
            score += 10.0
        
        # Vietnamese name match
        if query and query.lower() in school.get("vietnamese_name", "").lower():
            score += 8.0
        
        # Location exact match
        if location and location.lower() == school.get("location", "").lower():
            score += 5.0
        
        # Program match
        if program:
            programs = school.get("programs", [])
            for p in programs:
                if program.lower() in str(p).lower():
                    score += 3.0
        
        # Ranking bonus for Vietnamese universities
        if school.get("ranking_vietnam"):
            score += (10 - school["ranking_vietnam"]) * 0.5
        
        return score
    
    def ask_question(self, question: str, context: str = None) -> str:
        """
        Answer questions about schools and education in Vietnam.
        
        Args:
            question: User's question
            context: Additional context (e.g., specific school information)
            
        Returns:
            Comprehensive answer to the question
        """
        if not hasattr(self, 'llm') or self.llm is None:
            return self._basic_qa_response(question, context)
        
        print(f"🤖 Processing question: {question}")
        
        # Create comprehensive prompt with Vietnam education knowledge
        prompt = f"""
        You are an expert educational consultant specializing in Vietnamese education system and schools worldwide. 
        Provide comprehensive, accurate, and helpful answers about schools, universities, and education.

        KNOWLEDGE BASE - Vietnamese Education System:
        {json.dumps(self.vietnam_education_knowledge, indent=2, ensure_ascii=False)}

        SCHOOL DATABASE SAMPLE:
        {json.dumps(self.school_database["universities_vietnam"][:2], indent=2, ensure_ascii=False)}

        USER QUESTION: {question}

        ADDITIONAL CONTEXT (if provided): {context or "None"}

        INSTRUCTIONS:
        1. Provide accurate, detailed information about Vietnamese schools and education
        2. Include both Vietnamese and English names when relevant
        3. Mention specific admission requirements, tuition costs, and programs
        4. Compare schools when appropriate
        5. Give practical advice for students and parents
        6. Include contact information when available
        7. If about international schools, compare with Vietnamese alternatives
        8. Use Vietnamese terms with English translations
        9. Be culturally sensitive and understanding of Vietnamese education context
        10. If you don't have specific information, clearly state that and suggest reliable sources

        FORMAT:
        - Start with a direct answer
        - Provide detailed explanation
        - Include practical tips or recommendations
        - End with contact info or next steps if relevant

        ANSWER:
        """
        
        try:
            response = self.llm.invoke(prompt)
            print("✅ AI response generated successfully")
            return response
        except Exception as e:
            print(f"❌ AI processing failed: {e}")
            return self._basic_qa_response(question, context)
    
    def _basic_qa_response(self, question: str, context: str = None) -> str:
        """Provide basic response when AI is not available."""
        basic_responses = {
            "tuition": "Tuition fees in Vietnam vary significantly. Public universities typically charge 10-25 million VND per year, while international schools range from $20,000-35,000 USD annually.",
            "admission": "Vietnamese university admission is based on the National High School Examination (Kỳ thi tốt nghiệp THPT). Scores are on a 0-10 scale, with top universities requiring 24-28 points.",
            "ranking": "Top universities in Vietnam include Vietnam National University Hanoi, Vietnam National University HCMC, and Hanoi University of Science and Technology.",
            "location": "Major education hubs in Vietnam are Hanoi (northern region) and Ho Chi Minh City (southern region), with Da Nang and Hue as central region centers."
        }
        
        question_lower = question.lower()
        for key, response in basic_responses.items():
            if key in question_lower:
                return f"**{response}**\n\nFor more detailed information, please configure Vertex AI or search our school database."
        
        return "I'd be happy to help with information about Vietnamese schools and education. Please try asking about specific schools, admission requirements, tuition fees, or programs."
    
    def get_school_details(self, school_name: str) -> Dict:
        """Get detailed information about a specific school."""
        print(f"📋 Getting details for school: {school_name}")
        
        # Search in all school databases
        all_schools = (
            self.school_database["universities_vietnam"] + 
            self.school_database["international_schools_vietnam"]
        )
        
        for school in all_schools:
            if (school_name.lower() in school.get("name", "").lower() or 
                school_name.lower() in school.get("vietnamese_name", "").lower()):
                return school
        
        return {"error": f"School '{school_name}' not found in database"}
    
    def compare_schools(self, school_names: List[str]) -> Dict:
        """Compare multiple schools side by side."""
        print(f"⚖️ Comparing schools: {school_names}")
        
        comparison = {
            "schools": [],
            "comparison_matrix": {}
        }
        
        for name in school_names:
            school = self.get_school_details(name)
            if "error" not in school:
                comparison["schools"].append(school)
        
        if len(comparison["schools"]) >= 2:
            # Create comparison matrix
            comparison["comparison_matrix"] = self._create_comparison_matrix(comparison["schools"])
        
        return comparison
    
    def _create_comparison_matrix(self, schools: List[Dict]) -> Dict:
        """Create a comparison matrix for schools."""
        matrix = {}
        
        # Compare key attributes
        attributes = ["type", "location", "ranking_vietnam", "tuition_annual_vnd", "admission_score"]
        
        for attr in attributes:
            matrix[attr] = {}
            for school in schools:
                school_name = school.get("name", "Unknown")
                matrix[attr][school_name] = school.get(attr, "N/A")
        
        return matrix
    
    def get_recommendations(self, preferences: Dict) -> List[Dict]:
        """Get personalized school recommendations based on user preferences."""
        print(f"💡 Generating recommendations for preferences: {preferences}")
        
        # Extract preferences
        budget = preferences.get("budget", "medium")
        location_pref = preferences.get("location", "any")
        program_pref = preferences.get("program", "any")
        school_type_pref = preferences.get("type", "any")
        
        # Score all schools based on preferences
        recommendations = []
        all_schools = (
            self.school_database["universities_vietnam"] + 
            self.school_database["international_schools_vietnam"]
        )
        
        for school in all_schools:
            score = self._calculate_recommendation_score(school, preferences)
            if score > 0:
                recommendations.append({
                    **school,
                    "recommendation_score": score,
                    "recommendation_reasons": self._get_recommendation_reasons(school, preferences)
                })
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations[:5]  # Top 5 recommendations
    
    def _calculate_recommendation_score(self, school: Dict, preferences: Dict) -> float:
        """Calculate recommendation score based on user preferences."""
        score = 5.0  # Base score
        
        # Budget scoring
        budget = preferences.get("budget", "medium")
        if budget == "low":
            if school.get("type") == "Public":
                score += 3.0
        elif budget == "high":
            if school.get("type") == "International":
                score += 2.0
        
        # Location scoring
        location_pref = preferences.get("location", "any")
        if location_pref != "any":
            if location_pref.lower() in school.get("location", "").lower():
                score += 4.0
        
        # Program scoring
        program_pref = preferences.get("program", "any")
        if program_pref != "any":
            programs = school.get("programs", [])
            for p in programs:
                if program_pref.lower() in str(p).lower():
                    score += 3.0
        
        # Ranking bonus
        if school.get("ranking_vietnam"):
            score += (10 - school["ranking_vietnam"]) * 0.3
        
        return score
    
    def _get_recommendation_reasons(self, school: Dict, preferences: Dict) -> List[str]:
        """Get reasons why this school is recommended."""
        reasons = []
        
        if school.get("ranking_vietnam") and school["ranking_vietnam"] <= 3:
            reasons.append("Top-ranked university in Vietnam")
        
        if preferences.get("budget") == "low" and school.get("type") == "Public":
            reasons.append("Affordable tuition fees")
        
        if preferences.get("location") != "any":
            if preferences["location"].lower() in school.get("location", "").lower():
                reasons.append(f"Located in preferred city: {school.get('location')}")
        
        if school.get("programs"):
            reasons.append(f"Strong programs in: {', '.join(school['programs'][:3])}")
        
        return reasons 
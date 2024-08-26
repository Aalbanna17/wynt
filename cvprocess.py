from jobifyai import process_gpt_4o_turbo
from storedata import store_cv_data
from jsonup import json_load
from utils import profiletype
from getdata import get_job_data
from utils import get_database_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cvprocess(metadata, extracted_text):
    tenantId = metadata.get('tenant_id')
    jobid = metadata.get('job_id')
    resumeid = metadata.get('resume_id')
    candidate_id = metadata.get('candidate_id')
    
    profile_type = profiletype.Candidate if jobid is not None else profiletype.Talent
    
    cv_data , title_categories , score , scoren = await parse_cv_based_on_jobid(extracted_text, jobid)
    cv_data = await json_load(cv_data)
    scorejson = await json_load(score)

    session = await get_database_session()
    try:
        success = await store_cv_data(session, cv_data, scorejson, scoren, resumeid, tenantId, profile_type, title_categories, jobid, candidate_id)
        if not success:
            print("Failed to store CV data")
            logger.error("Failed to store CV data")
    finally:
        await session.close()

async def parse_cv_based_on_jobid(extracted_text, jobid):
    description, requirements, experience, education, tools, skills = None, None, None, None, None, None
    session = await get_database_session()

    try:
        if jobid is not None:
            job = await get_job_data(session, jobid)
            if job:
                title = job.title
                description = job.description
                requirements = job.requirements
                experience = job.experience
                education = job.education
                tools = job.tools
                skills = job.skills

    finally:
        await session.close()

    job_title = title if jobid is not None else ""
    cv_data , title_categories = await parse_cv(extracted_text, job_title,description, requirements, experience, education, tools, skills)
    score, scorej = await score_cv(extracted_text, job_title,description, requirements, experience, education, tools, skills)
    return cv_data , title_categories ,score ,scorej

async def parse_cv(text: str, job_title: str = "",description: str = "", requirements: str = "", experience: str = "", education: str = "", tools: str = "", skills: str = ""):
    if not job_title:
        agent_script = f"""
Organize CV data into these categories, staying within 4090 tokens:
{{
"Name":"",
"Age":"",
"Phone":" , ,...",
"Email":"Write the email in lowercase letters only.",
"address":[{{
"alladdress": "get full address like:("Sadat, Square, Qalyubia Governorate")",
"country" : "Back country ISO 3166 like : EG,KSA,USA,etc....",
"city" : ""
}}],
socialLinks:[{{
"platform":"Write the platform name in lowercase except first letter only. if back presonal website back only Website",
"link":"link",
}}]
"title":"on cv",
"summary": "Max 100 words",
"experience": "Find out how many years of experience he has.",
"education": [{{
"education" : "all education"
"school" : "University, school, institute or academy",
"speciality" : "description",
"department" : "department on school",
"degree" : "",
"duration": ""
}}],
"jobDetails": [{{
"company": "",
"position": "",
"duration": "",
"responsibilities": ["",""],
"projects": [{{
"project name":"name",
"Project details":"details",
"project name":"name",
"Project details":"details",
"":"",
"":""
}}]
}}],
"skills": [{{
"category": "category name", "skills": ["...", "..."],
"":"" , "":["",""]
Get all the skills written even if they are not related
}}],
"projects": [{{
"project_name":"name",
"Project_details":"details",
"project_name":"name",
"Project_details":"details",
write all projects
}}]
"achievements": ["",""],
"certifications": ["title":"","description":""],
"strengthPoints": ["4 key strengths he/she have it Related to "title on cv",""],
"recommendationsCv": ["4 actionable CV improvements",""]
}}
Instructions:
1. Tailor to job title: "title":"on cv".
2. Be concise, focus on quality over quantity.
3. If input exceeds limit, focus on most recent and relevant info.
3. any field is empty back it EMPTY
"""
    else:
         agent_script = f"""
Organize CV data into these categories, staying within 4090 tokens:
{{
"Name":"",
"Age":"",
"Phone":" , ,...",
"Email":"Write the email in lowercase letters only.",
"address":[{{
"alladdress": "get full address like:("Sadat, Square, Qalyubia Governorate")",
"country" : "Back country ISO 3166 like : EG,KSA,USA,etc....",
"city" : ""
}}],
socialLinks:[{{
"platform":"Write the platform name in lowercase except first letter only. if back presonal website back only Website",
"link":"link",
}}]
"title":"on cv",
"summary": "Max 100 words",
"experience": "Find out how many years of experience he has.",
"education": [{{
"education" : "all education"
"school" : "University, school, institute or academy",
"speciality" : "description",
"department" : "department on school",
"degree" : "",
"duration": ""
}}],
"jobDetails": [{{
"company": "",
"position": "",
"duration": "",
"responsibilities": ["",""],
"projects": [{{
"project name":"name",
"Project details":"details",
"project name":"name",
"Project details":"details",
"":"",
"":""
}}]
}}],
"skills": [{{
"category": "category name", "skills": ["...", "..."],
"":"" , "":["",""]
Get all the skills written even if they are not related
}}],
"projects": [{{
"project_name":"name",
"Project_details":"details",
"project_name":"name",
"Project_details":"details",
write all projects
}}]
"achievements": ["",""],
"certifications": ["title":"","description":""],
"strengthPoints": ["4 key strengths he/she have it Related to job title,job description,job requirements,job skills and job tools ""],
"recommendationsCv": ["4 actionable CV improvements to job description job requirements,job skills and job tools"]
}}
Instructions:
1. Tailor to job title: {job_title}.
2. job description : {description}
4. job requirements : {requirements}
5. job skills : {skills}
6. job tools : {tools}
7. Be concise, focus on quality over quantity.
8. If input exceeds limit, focus on most recent and relevant info.
9. any field is empty back it null don't write any things
"""
    
    data = process_gpt_4o_turbo(text, f"{agent_script} (respond in JSON)")
    title_categories = await get_title_categories(data)
    return data , title_categories

async def get_title_categories(data):
    parsed_data = await json_load(data)
    title = parsed_data.get("title", "EMPTY")
    logger.info(f"talent_title: {title}")
    agent_categories = """
"Software Engineer"
"BIM Coordinator"
"BIM Facilitator"
"BIM Manager"
"UX/UI Designer"
"BIM Designer"
"BIM Engineer"
"Project Manager"
"BIM Modeller"
"Data Analyst"
"Web Developer"
"DevOps Engineer"
Based on this categorys, choose one that is related to the job title sent to you.
if title Software Engineer Title Categories is Software Engineer like that on all
respond in string format like that:"BIM Engineer"
"""
    category = process_gpt_4o_turbo(title,agent_categories)
    logger.info(f"talent_title category: {category}")
    return category

async def score_cv(cv_text, job_title: str = "",description: str = "", requirements: str = "", experience: str = "", education: str = "", tools: str = "", skills: str = ""):
    if not job_title:
        agent_score = f"""
Human Resources Specialist Evaluation Framework for  Role
As a Human Resources Specialist, you are tasked with the critical evaluation of candidates' CVs for the position of . This evaluation must strictly scrutinize the alignment of the candidate's qualifications, experience, and skills with the explicit job description and requirements provided.
Job Description:
Job Requirements:
Evaluation Criteria:
1. Direct Experience and Proficiency:
- Closely assess whether the candidate's experience and proficiencies match the precise skills outlined in the job description and requirements. Only experiences directly related to these points are acceptable.
- Automatically assign low scores (below 50) to candidates whose experiences do not directly align with the specified skills and requirements.
2. Educational and Professional Background:
- Evaluate the specificity of the candidate's educational and professional background concerning the job requirements. Only degrees and professional experiences that are explicitly related to the job role are to be considered valid.
- Deduct significant points or fail candidates who do not possess the exact educational and professional background required.
3. Transferable Skills and Knowledge Gaps:
- Identify and critically evaluate any significant knowledge gaps relative to the explicit job requirements.
- Consider candidates' potential to quickly and effectively bridge these gaps only if they show clear evidence of similar accomplishments in the past.
4. Scoring System:
- Implement a stringent scoring system where the scores are primarily based on the candidate's direct alignment with the job requirements. The system should be transparent and quantifiable, focusing on direct evidence of skills and experiences as detailed in the job description.
- Reserve scores above 50 exclusively for candidates who demonstrate a clear, strong proficiency and direct experience in the essential areas outlined.
Reason for the Score:
Provide a detailed rationale for the assigned score, focusing solely on the candidate's qualifications in direct relation to the job description and requirements. Clearly state any discrepancies and the lack of alignment where relevant.
Recommendations:
Offer specific and actionable recommendations for the candidate to potentially enhance their suitability for the role, focusing only on development in areas directly related to the job description.
Conclusion:
Your analysis should sharply distinguish between candidates with general qualifications and those who possess the specific skills and experiences required by the job. Ensure that the scoring reflects a stringent and precise evaluation aligned with the job's explicit needs.
Please return the evaluation data in the following JSON format:
{{
    "score": "",
    "reason": "",
    "recommendationsScore": ["", "", ""],
    "conclusion": ""
}}
"""
    else:
        agent_score = f"""
Human Resources Specialist Evaluation Framework for {job_title} Role
As a Human Resources Specialist, you are tasked with the critical evaluation of candidates' CVs for the position of "BIM Manager". This evaluation must strictly scrutinize the alignment of the candidate's qualifications, experience, and skills with the explicit job description and requirements provided.
put score and recommendationsScore based on instructions:

1. Tailor to job title: {job_title}.
2. job description : {description}
3. job requirements : {requirements}
4. job skills : {skills}
5. job tools : {tools}

Evaluation Criteria:
1. Direct Experience and Proficiency:
- Closely assess whether the candidate's experience and proficiencies match the precise skills outlined in the job description 
and requirements. Only experiences directly related to these points are acceptable.
- Automatically assign low scores (below 50) to candidates whose experiences do not directly align with the specified skills 
and requirements.
2. Educational and Professional Background:
- Evaluate the specificity of the candidate's educational and professional background concerning the job requirements. 
Only degrees and professional experiences that are explicitly related to the job role are to be considered valid.
- Deduct significant points or fail candidates who do not possess the exact educational and professional background required.
3. Transferable Skills and Knowledge Gaps:
- Identify and critically evaluate any significant knowledge gaps relative to the explicit job requirements.
- Consider candidates' potential to quickly and effectively bridge these gaps only if they show clear evidence 
of similar accomplishments in the past.
4. Scoring System:
- Implement a stringent scoring system where the scores are primarily based on the candidate's direct alignment 
with the job requirements. The system should be transparent and quantifiable, focusing on direct evidence of skills 
and experiences as detailed in the job description.
- Reserve scores above 50 exclusively for candidates who demonstrate a clear, strong proficiency and direct 
experience in the essential areas outlined.
Reason for the Score:
Provide a detailed rationale for the assigned score, focusing solely on the candidate's qualifications in direct relation 
to the job description and requirements. Clearly state any discrepancies and the lack of alignment where relevant.
Recommendations:
Offer specific and actionable recommendations for the candidate to potentially enhance their suitability for the role, 
focusing only on development in areas directly related to the job description.
Conclusion:
Your analysis should sharply distinguish between candidates with general qualifications and those who possess 
the specific skills and experiences required by the job. Ensure that the scoring reflects a stringent and precise evaluation aligned with the job's explicit needs.
Please return the evaluation data in the following JSON format:
{{
    "score": "",
    "reason": "",
    "recommendationsScore": ["", "", ""],
    "conclusion": ""
}}
"""

    score = process_gpt_4o_turbo(cv_text, agent_score) 
    try:
            score_data = await json_load(score)
            numeric_score = int(score_data["score"])
    except (KeyError, ValueError):
            numeric_score = 0
            logger.warning(f"except numeric_score: {numeric_score}")
    else:
        numeric_score = 0

    return score, numeric_score

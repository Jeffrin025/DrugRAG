# import os
# import cv2
# import numpy as np
# from flask import Flask, request, jsonify
# from deepface import DeepFace
# from flask_cors import CORS
# import base64

# app = Flask(__name__)
# CORS(app)


# faces = "faces/"


# def upload_image():
#     data = request.get_json()
  
#     image_data = data.get('image')
    
#     if image_data:
#         print("Image data found")  
       
#         header, encoded = image_data.split(',', 1)
#         image_bytes = base64.b64decode(encoded)
        
       
#         np_array = np.frombuffer(image_bytes, np.uint8)
#         frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

       
#         try:
#             dfs = DeepFace.find(
#                 img_path=frame,
#                 db_path=faces,
#                 model_name='VGG-Face', 
#                 distance_metric='cosine',  
#                 detector_backend='opencv'  
#             )
            
#             if len(dfs) > 0:
#                 df = dfs[0]
#                 if not df.empty:
#                     name = df['identity'].values[0].split("/")[-1]
#                     print(name)
#                     return jsonify({'name': name[:-4]})  # Return only the name without the file extension
#             else:
#                 return jsonify({'name': 'No matching identity found.'}), 404
        
#         except Exception as e:
#             return jsonify({'error': str(e)}), 500

#     return jsonify({'message': 'No image provided'}), 400

# if __name__ == '__main__':
#     app.run(debug=True)





from flask import Flask, request, jsonify
import google.generativeai as genai
import PyPDF2
from flask_cors import CORS
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import json
import os
import time 
import concurrent.futures
app = Flask(__name__)
CORS(app)

genai.configure(api_key="AIzaSyBRK3rx8TEldrnG8eTkaluRNTpSARE8av0") 
model = genai.GenerativeModel('gemini-1.5-flash')


def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text.encode('utf-8', errors='ignore').decode('utf-8') + "\n"
            except Exception as e:
                print(f"PDF text extraction error: {str(e)}")
                continue

        if not text.strip():
            print("Fallback to OCR")
            images = convert_from_bytes(pdf_file)
            for image in images:
                text += pytesseract.image_to_string(image)

        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""


# Add timeout and better error handling
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Validate all required fields
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No student submission provided", "grade": 0}), 400

        file = request.files['file']
        if not file or file.filename == '' or not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Invalid student PDF file", "grade": 0}), 400

        # Get assignment metadata
        assignment_title = request.form.get('assignmentTitle', 'Assignment').strip()
        assignment_description = request.form.get('assignmentDescription', '').strip()
        
        # Get the original assignment PDF (if needed)
        assignment_pdf = request.files.get('assignmentPdf')

        print(f"Assignment Title: {assignment_title}")
        print(f"Assignment Description: {assignment_description[:100]}...")  # Preview first 100 chars

        # Extract text from student PDF
        pdf_bytes = file.read()
        text = extract_text_from_pdf(pdf_bytes)
        print(f'text : {text}')
        if not text.strip():
            return jsonify({"success": False, "error": "Empty student submission content", "grade": 0}), 400

        # Gemini Prompt
        prompt = f"""
        GRADE THIS ASSIGNMENT STRICTLY FOLLOWING THESE RULES:

        1. Assignment Title: {assignment_title}
        2. Assignment Description: {assignment_description}
        3. Student Submission: {text[:5000]}

        EVALUATION CRITERIA:
        - Relevance to assignment title and description (30%)
        - Quality of content (40%)
        - Originality (20%)
        - Technical accuracy (10%)

        OUTPUT REQUIREMENTS:
        - Return ONLY valid JSON
        - Grade must be between 0.0 and 10.0
        - Feedback should specifically reference the assignment requirements
        - Relevance score between 1-10

        OUTPUT FORMAT:
        {{
            "grade": 7.5,
            "feedback": "Good effort addressing {assignment_title} but needs more depth in discussing {assignment_description.split()[0]}...",
            "relevance_score": 8
        }}
        """

        # Function to call Gemini
        def call_gemini():
            return model.generate_content(prompt, request_options={"timeout": 20}).text.strip()

        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(call_gemini)
                response_text = future.result(timeout=30)

            # Clean up response text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(response_text)

            # Validate required fields
            if not all(k in result for k in ["grade", "feedback", "relevance_score"]):
                raise ValueError("Missing required fields in response")

            # Clamp and parse grade
            grade = float(result["grade"])
            grade = max(0.0, min(10.0, round(grade, 1)))
            feedback = str(result["feedback"]).strip()
            relevance_score = int(result["relevance_score"])

            if relevance_score < 3:
                grade = 0
                feedback = "Submission not relevant to assignment topic"

            return jsonify({
                "success": True,
                "grade": grade,
                "feedback": feedback,
                "relevance_score": relevance_score
            })

        except concurrent.futures.TimeoutError:
            return jsonify({
                "success": False,
                "error": "Grading timed out",
                "grade": 0,
                "feedback": "Automatic grading timeout"
            }), 504

        except Exception as e:
            print(f"Grading error: {str(e)}\nResponse was: {response_text}")
            return jsonify({
                "success": False,
                "error": f"Grading failed: {str(e)}",
                "grade": 0,
                "feedback": "Automatic grading failed"
            }), 500

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "grade": 0,
            "feedback": "Technical error during grading"
        }), 500
    
@app.route('/grade-written-test', methods=['POST'])
def grade_written_test():
    try:
        data = request.json
        attempt_id = data.get('attemptId')
        
        if not attempt_id:
            return jsonify({"success": False, "error": "Missing attemptId"}), 400

        # 1. Fetch test data from Node.js backend
        node_backend_url = f"http://localhost:5000/api/test-attempts/{attempt_id}/questions-for-grading"
        response = request.get(node_backend_url)
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Failed to fetch test data from backend"
            }), 500

        test_data = response.json()
        answers = test_data['answers']
        test_title = test_data['test_title']

        graded_answers = []
        total_marks = 0
        
        # 2. Grade each written answer
        for answer in answers:
            if answer['question_type'] != 'written':
                continue  # Skip non-written questions

            prompt = f"""
            GRADE THIS WRITTEN TEST ANSWER:
            
            TEST: {test_title}
            QUESTION: {answer['question_text']}
            STUDENT ANSWER: {answer['answer_text']}
            
            EVALUATION CRITERIA:
            1. Accuracy (40%): How correct is the answer?
            2. Completeness (30%): Does it cover all aspects of the question?
            3. Clarity (20%): Is the answer well-structured and easy to understand?
            4. Originality (10%): Does it show original thought?
            
            MAXIMUM MARKS: {answer['max_marks']}
            
            INSTRUCTIONS:
            - Grade strictly but fairly
            - Provide constructive feedback
            - Return ONLY valid JSON
            
            REQUIRED OUTPUT FORMAT:
            {{
                "marks_awarded": x.x,  // Between 0 and max_marks
                "feedback": "Your feedback here..."
            }}
            """
            
            try:
                # Call Gemini API
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Clean response
                response_text = response_text.replace('```json', '').replace('```', '').strip()
                result = json.loads(response_text)
                
                marks = min(float(result["marks_awarded"]), float(answer['max_marks']))
                feedback = result["feedback"]
                
                graded_answers.append({
                    "question_id": answer['question_id'],
                    "marks_awarded": round(marks, 1),
                    "feedback": feedback
                })
                
                total_marks += marks
            except Exception as e:
                print(f"Error grading question {answer['question_id']}: {str(e)}")
                # Fallback to partial marks if grading fails
                graded_answers.append({
                    "question_id": answer['question_id'],
                    "marks_awarded": float(answer['max_marks']) * 0.5,
                    "feedback": "Automatic grading encountered an error"
                })
                total_marks += float(answer['max_marks']) * 0.5

        # 3. Send grades back to Node.js backend
        update_url = f"http://localhost:5000/api/test-attempts/{attempt_id}/update-grades"
        update_response = request.post(
            update_url,
            json={"grades": graded_answers}
        )
        
        if update_response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Failed to update grades in backend"
            }), 500

        return jsonify({
            "success": True,
            "attemptId": attempt_id,
            "total_marks": round(total_marks, 1),
            "graded_questions": len(graded_answers)
        })

    except Exception as e:
        print(f"Grading error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
@app.route('/generate-questions', methods=['POST'])
def generate_questions():
    try:
        data = request.json
        topic = data.get('topic', 'General Knowledge')
        test_type = data.get('testType', 'mcq')
        num_questions = int(data.get('numQuestions', 5))
        difficulty = data.get('difficulty', 'medium')
        total_marks = int(data.get('totalMarks', num_questions))  # Default to 1 mark per question if not provided

        # Calculate base marks per question
        base_marks = total_marks // num_questions
        remainder = total_marks % num_questions

        prompt = f"""
        Generate {num_questions} {test_type.upper()} questions about {topic} ({difficulty} difficulty).
        
        The total marks for this test is {total_marks}, distributed as:
        - {num_questions - remainder} questions worth {base_marks} marks each
        - {remainder} questions worth {base_marks + 1} marks each
        
        For MCQ questions, provide:
        - The question text
        - 4 options (A, B, C, D)
        - The correct answer (A, B, C, or D)
        - Marks (as calculated above)
        
        For written questions, provide:
        - The question text
        - Marks (as calculated above)
        
        Return ONLY valid JSON in this format:
        {{
            "questions": [
                {{
                    "question_text": "...",
                    "question_type": "{test_type}",
                    "marks": x,  // Distribute marks as explained above
                    "options": {{"A": "...", "B": "...", ...}},  // Only for MCQ
                    "correct_answer": "A"  // Only for MCQ
                }},
                ...
            ]
        }}
        """

        def call_gemini():
            response = model.generate_content(prompt)
            return response.text.strip()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(call_gemini)
            response_text = future.result(timeout=30)

        # Clean response
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        result = json.loads(response_text)
        
        # Verify total marks match
        generated_marks = sum(q.get('marks', 0) for q in result.get("questions", []))
        if generated_marks != total_marks:
            # Adjust marks if they don't match
            questions = result.get("questions", [])
            for i in range(len(questions)):
                if i < remainder:
                    questions[i]['marks'] = base_marks + 1
                else:
                    questions[i]['marks'] = base_marks

        return jsonify({
            "success": True,
            "questions": result.get("questions", []),
            "totalMarks": total_marks
        })

    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "questions": []
        }), 500
    

if __name__ == '__main__':
    app.run(port=5001, debug=True)
import requests
import sys
import json
import time
from datetime import datetime

class ColdEmailAPITester:
    def __init__(self, base_url="https://jobreach-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_api_root(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, str(e))
            return False

    def test_hr_contacts(self):
        """Test HR contacts endpoint"""
        try:
            response = requests.get(f"{self.api_url}/hr-contacts", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    details += f", Found {len(data)} HR contacts"
                    # Check structure of first contact
                    first_contact = data[0]
                    required_fields = ['id', 'company_name', 'hr_name', 'hr_email', 'position', 'industry']
                    missing_fields = [field for field in required_fields if field not in first_contact]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                else:
                    success = False
                    details += ", No HR contacts returned"
            
            self.log_test("HR Contacts Endpoint", success, details)
            return success, response.json() if success else []
        except Exception as e:
            self.log_test("HR Contacts Endpoint", False, str(e))
            return False, []

    def test_hiring_updates(self):
        """Test hiring updates endpoint"""
        try:
            response = requests.get(f"{self.api_url}/hiring-updates", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    details += f", Found {len(data)} hiring updates"
                    # Check structure of first update
                    first_update = data[0]
                    required_fields = ['id', 'company_name', 'position', 'industry', 'requirements', 'posted_date', 'is_active']
                    missing_fields = [field for field in required_fields if field not in first_update]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                else:
                    success = False
                    details += ", No hiring updates returned"
            
            self.log_test("Hiring Updates Endpoint", success, details)
            return success, response.json() if success else []
        except Exception as e:
            self.log_test("Hiring Updates Endpoint", False, str(e))
            return False, []

    def test_upload_resume(self):
        """Test resume upload endpoint with different file types"""
        # Test with a mock PDF file
        try:
            # Create a simple text file to simulate PDF upload
            test_content = b"Mock PDF content for testing"
            files = {'file': ('test_resume.pdf', test_content, 'application/pdf')}
            
            response = requests.post(
                f"{self.api_url}/upload-resume",
                files=files,
                timeout=30
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                required_fields = ['filename', 'original_filename', 'file_size', 'upload_success']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    details += f", Upload successful: {data['original_filename']}"
                    details += f", File size: {data['file_size']} bytes"
                    return success, data['filename']
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test("Resume Upload Endpoint", success, details)
            return success, None
        except Exception as e:
            self.log_test("Resume Upload Endpoint", False, str(e))
            return False, None

    def test_upload_invalid_file(self):
        """Test resume upload with invalid file type"""
        try:
            # Test with invalid file type
            test_content = b"Invalid file content"
            files = {'file': ('test_file.txt', test_content, 'text/plain')}
            
            response = requests.post(
                f"{self.api_url}/upload-resume",
                files=files,
                timeout=30
            )
            
            # Should return error (either 400 or 500 with proper error message)
            success = response.status_code in [400, 500]
            details = f"Status: {response.status_code}"
            
            if success:
                try:
                    error_data = response.json()
                    if "Invalid file type" in str(error_data):
                        details += ", Correctly rejected invalid file type"
                        details += f", Error: {error_data.get('detail', error_data)}"
                    else:
                        success = False
                        details += f", Unexpected error format: {error_data}"
                except:
                    success = False
                    details += ", Could not parse error response"
            else:
                details += ", Should have rejected invalid file type"
                details += f", Response: {response.text[:200]}"
            
            self.log_test("Resume Upload Invalid File Validation", success, details)
            return success
        except Exception as e:
            self.log_test("Resume Upload Invalid File Validation", False, str(e))
            return False

    def test_generate_email_with_formdata(self):
        """Test email generation endpoint with FormData (v2.0 format)"""
        test_data = {
            "name": "Alice Johnson",
            "college": "Harvard University", 
            "degree": "Computer Science",
            "skills": "Python, JavaScript, React, Node.js",
            "job_preference": "Full Stack Developer",
            "personalization_note": "I have 2 years of internship experience and built 5 web applications"
        }
        
        try:
            print(f"🔄 Testing email generation with FormData (this may take 10-30 seconds due to AI processing)...")
            response = requests.post(
                f"{self.api_url}/generate-email", 
                data=test_data,  # Using data instead of json for FormData
                timeout=60
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                # Updated for v2.0 - subject_lines instead of subject_line
                required_fields = ['id', 'student_id', 'email_content', 'subject_lines', 'has_resume', 'generated_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    details += f", Email generated successfully"
                    # Check for multiple subject lines (v2.0 feature)
                    if isinstance(data['subject_lines'], list) and len(data['subject_lines']) >= 3:
                        details += f", Generated {len(data['subject_lines'])} subject lines"
                        details += f", First subject: '{data['subject_lines'][0][:50]}...'"
                    else:
                        success = False
                        details += f", Expected 3+ subject lines, got: {data.get('subject_lines', 'None')}"
                    
                    details += f", Content length: {len(data['email_content'])} chars"
                    details += f", Has resume: {data['has_resume']}"
                    
                    # Check if content looks reasonable
                    if len(data['email_content']) < 50:
                        success = False
                        details += ", Email content too short"
                    elif "Alice Johnson" not in data['email_content']:
                        success = False
                        details += ", Email doesn't contain student name"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test("Email Generation with FormData", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("Email Generation with FormData", False, str(e))
            return False, {}

    def test_generate_email_with_resume(self):
        """Test email generation with resume attachment"""
        # First upload a resume
        upload_success, resume_filename = self.test_upload_resume()
        if not upload_success or not resume_filename:
            self.log_test("Email Generation with Resume", False, "Resume upload failed")
            return False, {}
        
        test_data = {
            "name": "Bob Smith",
            "college": "MIT",
            "degree": "Software Engineering", 
            "skills": "Python, Machine Learning, TensorFlow",
            "job_preference": "ML Engineer",
            "personalization_note": "Passionate about AI and deep learning",
            "resume_filename": resume_filename
        }
        
        try:
            print(f"🔄 Testing email generation with resume attachment...")
            response = requests.post(
                f"{self.api_url}/generate-email",
                data=test_data,
                timeout=60
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if data.get('has_resume') == True:
                    details += ", Resume attachment correctly detected"
                    # Check if resume is mentioned in email content
                    if "resume" in data['email_content'].lower() or "attached" in data['email_content'].lower():
                        details += ", Resume mentioned in email content"
                    else:
                        success = False
                        details += ", Resume not mentioned in email content"
                else:
                    success = False
                    details += ", Resume attachment not detected"
            
            self.log_test("Email Generation with Resume", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("Email Generation with Resume", False, str(e))
            return False, {}

    def test_students_endpoint(self):
        """Test students endpoint"""
        try:
            response = requests.get(f"{self.api_url}/students", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Found {len(data)} students in database"
            
            self.log_test("Students Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Students Endpoint", False, str(e))
            return False

    def test_emails_endpoint(self):
        """Test emails endpoint"""
        try:
            response = requests.get(f"{self.api_url}/emails", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Found {len(data)} generated emails in database"
            
            self.log_test("Generated Emails Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Generated Emails Endpoint", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Cold Email Generator v2.0 API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_api_root():
            print("❌ API root endpoint failed - stopping tests")
            return False
        
        # Test static endpoints
        self.test_hr_contacts()
        self.test_hiring_updates()
        
        # Test database endpoints
        self.test_students_endpoint()
        self.test_emails_endpoint()
        
        # Test new v2.0 features
        print("\n🆕 Testing v2.0 Features:")
        print("-" * 40)
        
        # Test resume upload functionality
        self.test_upload_invalid_file()  # Test validation first
        
        # Test AI integration with new FormData format
        email_success, email_data = self.test_generate_email_with_formdata()
        
        # Test email generation with resume
        self.test_generate_email_with_resume()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        else:
            print("\n✅ All tests passed!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ColdEmailAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
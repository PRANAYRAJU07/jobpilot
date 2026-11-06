from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import uuid

app = FastAPI()

@app.get("/jobs/ai-ml-intern", response_class=HTMLResponse)
def ai_ml_intern_job():
    return """
    <html>
        <head><title>AI/ML Intern - JobPilot Mock Corp</title></head>
        <body>
            <h1>AI/ML Intern</h1>
            <p>Location: Hyderabad, India</p>
            <p>Role: Internship</p>
            <p>Join our team to build cutting edge models!</p>
            <a href="/jobs/ai-ml-intern/apply" id="apply-button">Apply Now</a>
        </body>
    </html>
    """

@app.get("/jobs/ai-ml-intern/apply", response_class=HTMLResponse)
def ai_ml_intern_apply():
    return """
    <html>
        <head><title>Apply - AI/ML Intern</title></head>
        <body>
            <h1>Application for AI/ML Intern</h1>
            <form action="/apply" method="POST" enctype="multipart/form-data">
                <div><label>First Name</label> <input type="text" name="first_name" id="first_name" required /></div>
                <div><label>Last Name</label> <input type="text" name="last_name" id="last_name" required /></div>
                <div><label>Email</label> <input type="email" name="email" id="email" required /></div>
                <div><label>Phone</label> <input type="tel" name="phone" id="phone" /></div>
                <div><label>City</label> <input type="text" name="city" id="city" /></div>
                <div><label>University</label> <input type="text" name="university" id="university" /></div>
                <div><label>Degree</label> <input type="text" name="degree" id="degree" /></div>
                <div><label>Graduation Year</label> <input type="number" name="graduation_year" id="graduation_year" /></div>
                <div><label>CGPA</label> <input type="text" name="cgpa" id="cgpa" /></div>
                <div><label>GitHub</label> <input type="url" name="github" id="github" /></div>
                <div><label>LinkedIn</label> <input type="url" name="linkedin" id="linkedin" /></div>
                <div><label>Resume Upload</label> <input type="file" name="resume" id="resume" required /></div>
                <div><label>Why are you interested?</label> <textarea name="interest" id="interest"></textarea></div>
                
                <button type="submit" id="submit-application">Submit Application</button>
            </form>
        </body>
    </html>
    """

@app.post("/apply", response_class=HTMLResponse)
async def submit_application(request: Request):
    form_data = await request.form()
    # Log the successful application on mock server
    app_id = f"TEST-APP-{uuid.uuid4().hex[:8].upper()}"
    return f"""
    <html>
        <head><title>Application Submitted</title></head>
        <body>
            <h1 id="success-banner">Application submitted successfully.</h1>
            <p>Application ID: <span id="application-id">{app_id}</span></p>
        </body>
    </html>
    """

@app.get("/simple", response_class=HTMLResponse)
def simple_form():
    return """
    <html>
        <body>
            <h1>Apply for Job</h1>
            <form action="/submission-confirmation" method="GET">
                <label>First Name</label>
                <input type="text" name="first_name" id="first_name" />
                <label>Last Name</label>
                <input type="text" name="last_name" id="last_name" />
                <label>Email</label>
                <input type="email" name="email" id="email" />
                <button type="submit">Submit Application</button>
            </form>
        </body>
    </html>
    """

@app.get("/with-captcha", response_class=HTMLResponse)
def captcha_form():
    return """
    <html>
        <body>
            <h1>Apply for Job</h1>
            <div id="h-captcha">Verify you are human</div>
            <button type="submit">Submit Application</button>
        </body>
    </html>
    """
    
@app.get("/with-otp", response_class=HTMLResponse)
def otp_form():
    return """
    <html>
        <body>
            <h1>Verify your identity</h1>
            <p>Enter the code sent to your email.</p>
            <input type="text" name="otp" />
            <button type="submit">Verify</button>
        </body>
    </html>
    """
    
@app.get("/with-unknown-question", response_class=HTMLResponse)
def unknown_form():
    return """
    <html>
        <body>
            <h1>Apply for Job</h1>
            <label>What is your favorite color?</label>
            <input type="text" name="color" id="color" />
            <button type="submit">Submit</button>
        </body>
    </html>
    """

@app.get("/submission-confirmation", response_class=HTMLResponse)
def success_page():
    return """
    <html>
        <body>
            <h1>Application Submitted</h1>
            <p>Thank you for applying.</p>
        </body>
    </html>
    """

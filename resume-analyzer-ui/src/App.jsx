// resume-analyzer-ui/src/App.jsx

import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // Assuming you have App.css for basic styling
import './index.css'; // Assuming this is your Tailwind CSS import

function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [predictedJobRole, setPredictedJobRole] = useState(null);
  const [parsedJdDetails, setParsedJdDetails] = useState(null); // NEW state for parsed JD details

  const BACKEND_URL = 'http://127.0.0.1:8000'; // Ensure this matches your FastAPI URL

  const handleFileChange = (e, type) => {
    if (type === 'resume') {
      setResumeFile(e.target.files[0]);
    } else {
      setJdFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setAnalysisResults(null);
    setPredictedJobRole(null);
    setParsedJdDetails(null); // Clear previous JD details

    if (!resumeFile || !jdFile) {
      setError("Please upload both a resume and a job description.");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append('resume_file', resumeFile);
    formData.append('jd_file', jdFile);

    try {
      // 1. Call the /compare-resume-and-jd/ endpoint
      const comparisonResponse = await axios.post(`${BACKEND_URL}/compare-resume-and-jd/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setAnalysisResults(comparisonResponse.data);
      setParsedJdDetails(comparisonResponse.data.parsed_jd_details); // Store new JD details

      // Extract the full resume text returned by the /compare-resume-and-jd/ endpoint
      const fullResumeText = comparisonResponse.data.resume_info.full_resume_text;

      if (fullResumeText) {
        // 2. Call the /predict-job-role/ endpoint with the full resume text
        const predictResponse = await axios.post(`${BACKEND_URL}/predict-job-role/`, { 
          resume_full_text: fullResumeText 
        });
        setPredictedJobRole(predictResponse.data.predicted_job_role);
      } else {
        console.warn("Full resume text not available for job role prediction.");
        setPredictedJobRole("N/A (Text not available)");
      }

    } catch (err) {
      console.error("Error during analysis:", err);
      setError("An error occurred during analysis. Please try again.");
      if (err.response) {
        console.error("Backend Error:", err.response.data);
        setError(err.response.data.detail || "An error occurred on the server.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-4xl">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">Resume & Job Description Analyzer</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Upload Resume (PDF/DOCX)</label>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => handleFileChange(e, 'resume')}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Upload Job Description (PDF/DOCX)</label>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => handleFileChange(e, 'jd')}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className={`w-full py-3 px-4 rounded-md text-white font-semibold transition duration-300 ${
            loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? 'Analyzing...' : 'Analyze Resume & JD'}
        </button>

        {error && <p className="text-red-500 text-center mt-4">{error}</p>}

        {analysisResults && (
          <div className="mt-8 border-t pt-8 border-gray-200">
            <h2 className="text-2xl font-bold text-center text-gray-800 mb-4">Analysis Results</h2>
            
            {/* Display Predicted Job Role */}
            {predictedJobRole && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-lg font-semibold text-blue-800">
                  <span className="text-blue-600">Predicted Job Role:</span> {predictedJobRole}
                </p>
              </div>
            )}

            {/* Display Parsed JD Details (NEW) */}
            {parsedJdDetails && (
              <div className="mb-6 p-4 bg-purple-50 rounded-lg">
                <h3 className="text-lg font-semibold text-purple-800 mb-2">Parsed Job Description Details (ML-Extracted):</h3>
                {parsedJdDetails.required_skills_ner && parsedJdDetails.required_skills_ner.length > 0 && (
                  <p className="text-purple-700 mb-1">
                    <span className="font-medium">Required Skills:</span> {parsedJdDetails.required_skills_ner.join(', ')}
                  </p>
                )}
                {parsedJdDetails.experience_level_ner && (
                  <p className="text-purple-700 mb-1">
                    <span className="font-medium">Experience Level:</span> {parsedJdDetails.experience_level_ner}
                  </p>
                )}
                {parsedJdDetails.educational_requirements_ner && (
                  <p className="text-purple-700">
                    <span className="font-medium">Educational Requirements:</span> {parsedJdDetails.educational_requirements_ner}
                  </p>
                )}
                {(!parsedJdDetails.required_skills_ner || parsedJdDetails.required_skills_ner.length === 0) &&
                 !parsedJdDetails.experience_level_ner && !parsedJdDetails.educational_requirements_ner && (
                  <p className="text-purple-700">No specific details extracted by NER for this JD.</p>
                )}
              </div>
            )}


            {/* Existing Fit Score Display */}
            <div className="mb-6 p-4 bg-green-50 rounded-lg">
              <p className="text-lg font-semibold text-green-800">
                Overall Job Fit Score: <span className="text-green-600">{analysisResults.comparison_results.fit_score}%</span>
              </p>
            </div>

            {/* Existing Matched Skills */}
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">✅ Matched Skills ({analysisResults.comparison_results.matched_skills.length})</h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 list-disc pl-5">
                {analysisResults.comparison_results.matched_skills.map((skill, index) => (
                  <li key={index} className="text-gray-600">{skill}</li>
                ))}
              </ul>
            </div>

            {/* Existing Missing Skills */}
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">❌ Missing Skills (JD has, Resume lacks) ({analysisResults.comparison_results.missing_skills.length})</h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 list-disc pl-5 text-red-600">
                {analysisResults.comparison_results.missing_skills.map((skill, index) => (
                  <li key={index}>{skill}</li>
                ))}
              </ul>
            </div>

            {/* Existing Extra Skills */}
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">💡 Extra Skills (Resume has, JD doesn't emphasize) ({analysisResults.comparison_results.extra_skills.length})</h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 list-disc pl-5 text-yellow-600">
                {analysisResults.comparison_results.extra_skills.map((skill, index) => (
                  <li key={index}>{skill}</li>
                ))}
              </ul>
            </div>

            {/* Existing Resume Information Display */}
            <div className="mb-6 border-t pt-6 border-gray-200">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">Resume Information</h3>
              <p className="text-gray-600 mb-1">Filename: {analysisResults.resume_info.filename}</p>
              <p className="text-gray-600 mb-1">Email: {analysisResults.resume_info.email}</p>
              <p className="text-gray-600 mb-3">Phone: {analysisResults.resume_info.phone}</p>
              
              <h4 className="font-semibold text-gray-700 mb-2">Education:</h4>
              <ul className="list-disc pl-5 mb-3">
                {analysisResults.resume_info.education.map((edu, index) => (
                  <li key={index} className="text-gray-600">{edu}</li>
                ))}
              </ul>

              <h4 className="font-semibold text-gray-700 mb-2">Experience Highlights:</h4>
              <ul className="list-disc pl-5">
                {analysisResults.resume_info.experience.map((exp, index) => (
                  <li key={index} className="text-gray-600">{exp}</li>
                ))}
              </ul>
            </div>

            {/* Job Description Skills Detected (from backend's initial JD skill extraction, possibly rule-based or older ML) */}
            <div className="mb-6 border-t pt-6 border-gray-200">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">Job Description Skills Detected (For Fit Score)</h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 list-disc pl-5">
                {analysisResults.jd_extracted_skills.map((skill, index) => (
                  <li key={index} className="text-gray-600">{skill}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const AssignmentSubmissions = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [assignmentTitle, setAssignmentTitle] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch assignment title
        const titleResponse = await axios.get(
          `http://localhost:5000/api/assignments/${id}/pdf`,
          { responseType: "blob" } // We just need the headers
        );
        
        const contentDisposition = titleResponse.headers["content-disposition"];
        let filename = "assignment.pdf";
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename=(.+)/);
          if (filenameMatch && filenameMatch.length === 2) {
            filename = filenameMatch[1].replace(/"/g, '');
          }
        }
        setAssignmentTitle(filename.replace('.pdf', ''));

        // Fetch submissions
        const submissionsResponse = await axios.get(
          `http://localhost:5000/api/assignments/${id}/submissions`
        );
        setSubmissions(submissionsResponse.data);
        setLoading(false);
      } catch (err) {
        setError("Failed to fetch submissions");
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleDownload = async (assignmentId, studentId) => {
    try {
      const response = await axios.get(
        `http://localhost:5000/api/submissions/${assignmentId}/${studentId}/pdf`,
        { responseType: "blob" }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      
      // Extract filename from content-disposition header
      const contentDisposition = response.headers["content-disposition"];
      let filename = "submission.pdf";
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch && filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Download failed:", err);
      alert("Failed to download submission");
    }
  };

  const handleGradeSubmit = async (studentId, grade, feedback) => {
    try {
      await axios.post(`http://localhost:5000/api/assignments/${id}/grade`, {
        studentId,
        grade,
        feedback
      });
      
      // Refresh submissions
      const response = await axios.get(
        `http://localhost:5000/api/assignments/${id}/submissions`
      );
      setSubmissions(response.data);
    } catch (err) {
      console.error("Grading failed:", err);
      alert("Failed to submit grade");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <button onClick={() => navigate("/staff/assignments")} style={{ marginBottom: "20px" }}>
        Back to Assignments
      </button>
      <h2>Submissions for: {assignmentTitle}</h2>
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p style={{ color: "red" }}>{error}</p>
      ) : submissions.length === 0 ? (
        <p>No submissions found.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Student</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Email</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Status</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Submitted At</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Grade</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Feedback</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {submissions.map((submission) => (
              <tr key={submission.student_id}>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{submission.username}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{submission.email}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {submission.submitted ? "Submitted" : "Not submitted"}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : "-"}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {submission.grade || "-"}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {submission.feedback || "-"}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {submission.submitted && (
                    <>
                      <button 
                        onClick={() => handleDownload(id, submission.student_id)}
                        style={{ marginRight: "5px" }}
                      >
                        Download
                      </button>
                      <GradeForm 
                        currentGrade={submission.grade}
                        currentFeedback={submission.feedback}
                        onSubmit={(grade, feedback) => 
                          handleGradeSubmit(submission.student_id, grade, feedback)
                        }
                      />
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

const GradeForm = ({ currentGrade, currentFeedback, onSubmit }) => {
  const [grade, setGrade] = useState(currentGrade || "");
  const [feedback, setFeedback] = useState(currentFeedback || "");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(grade, feedback);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "inline-block" }}>
      <input
        type="number"
        min="0"
        max="100"
        value={grade}
        onChange={(e) => setGrade(e.target.value)}
        placeholder="Grade"
        style={{ width: "50px", marginRight: "5px" }}
      />
      <input
        type="text"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Feedback"
        style={{ width: "150px", marginRight: "5px" }}
      />
      <button type="submit">Submit</button>
    </form>
  );
};

export default AssignmentSubmissions;
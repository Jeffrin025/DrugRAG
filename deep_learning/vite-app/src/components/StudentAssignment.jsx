import React, { useState, useEffect } from "react";
import axios from "axios";

const StudentAssignments = () => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAssignments = async () => {
      try {
        const userData = JSON.parse(localStorage.getItem("user"));
        if (!userData || userData.role !== "student") {
          window.location.href = "/";
          return;
        }

        const response = await axios.get(
          `http://localhost:5000/api/assignments/student/${userData.userId}`
        );
        setAssignments(response.data);
        setLoading(false);
      } catch (err) {
        setError("Failed to fetch assignments");
        setLoading(false);
      }
    };

    fetchAssignments();
  }, []);

  const handleDownload = async (assignmentId) => {
    try {
      const response = await axios.get(
        `http://localhost:5000/api/assignments/${assignmentId}/pdf`,
        { responseType: "blob" }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      
      // Extract filename from content-disposition header
      const contentDisposition = response.headers["content-disposition"];
      let filename = "assignment.pdf";
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
      alert("Failed to download assignment");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Your Assignments</h2>
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p style={{ color: "red" }}>{error}</p>
      ) : assignments.length === 0 ? (
        <p>No assignments found.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Title</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Description</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Date Created</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Status</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Grade</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {assignments.map((assignment) => (
              <tr key={assignment.id}>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{assignment.title}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{assignment.description}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {new Date(assignment.created_at).toLocaleDateString()}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {assignment.submitted ? "Submitted" : "Pending"}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {assignment.grade || "Not graded"}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  <button onClick={() => handleDownload(assignment.id)}>
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default StudentAssignments;
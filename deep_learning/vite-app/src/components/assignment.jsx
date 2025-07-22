import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const StaffAssignments = () => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAssignments = async () => {
      try {
        const userData = JSON.parse(localStorage.getItem("user"));
        if (!userData || userData.role !== "staff") {
          navigate("/");
          return;
        }

        const response = await axios.get(
          `http://localhost:5000/api/assignments/staff/${userData.userId}`
        );
        setAssignments(response.data);
        setLoading(false);
      } catch (err) {
        setError("Failed to fetch assignments");
        setLoading(false);
      }
    };

    fetchAssignments();
  }, [navigate]);

  const handleViewSubmissions = (assignmentId) => {
    navigate(`/staff/assignments/${assignmentId}/submissions`);
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
                  <button onClick={() => handleViewSubmissions(assignment.id)}>
                    View Submissions
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

export default StaffAssignments;
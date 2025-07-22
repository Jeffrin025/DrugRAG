import React from "react";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const StudentDashboard = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // In a real app, you would get this from your auth context or localStorage
        const userData = JSON.parse(localStorage.getItem("user"));
        if (userData && userData.role === "student") {
          setUsername(userData.username);
        } else {
          navigate("/");
        }
      } catch (err) {
        navigate("/");
      }
    };

    fetchUserData();
  }, [navigate]);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Welcome, {username}!</h1>
      <div style={{ marginTop: "20px" }}>
        <button 
          onClick={() => navigate("/student/assignments")}
          style={{ padding: "10px 15px" }}
        >
          View Assignments
        </button>
      </div>
    </div>
  );
};

export default StudentDashboard;
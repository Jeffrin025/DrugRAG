import React from "react";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";

const StaffDashboard = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [userId, setUserId] = useState("");

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // In a real app, you would get this from your auth context or localStorage
        const userData = JSON.parse(localStorage.getItem("user"));
        if (userData && userData.role === "staff") {
          setUsername(userData.username);
          setUserId(userData.userId);
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
          onClick={() => navigate("/staff/assignments")}
          style={{ marginRight: "10px", padding: "10px 15px" }}
        >
          View Assignments
        </button>
        <button 
          onClick={() => navigate("/staff/assignments/create")}
          style={{ padding: "10px 15px" }}
        >
          Create New Assignment
        </button>
      </div>
    </div>
  );
};

export default StaffDashboard;
import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const CreateAssignment = () => {
  const [form, setForm] = useState({
    title: "",
    description: "",
    pdf: null
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    setForm({ ...form, pdf: e.target.files[0] });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!form.pdf) {
      setError("Please select a PDF file");
      return;
    }

    try {
      const userData = JSON.parse(localStorage.getItem("user"));
      if (!userData || userData.role !== "staff") {
        navigate("/");
        return;
      }

      const formData = new FormData();
      formData.append("title", form.title);
      formData.append("description", form.description);
      formData.append("pdf", form.pdf);
      formData.append("staffId", userData.userId);

      await axios.post("http://localhost:5000/api/assignments", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      setSuccess("Assignment created and distributed to your students successfully!");
      setForm({
        title: "",
        description: "",
        pdf: null
      });
    } catch (err) {
      setError(err.response?.data?.message || "Failed to create assignment");
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
      <h2>Create New Assignment</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "15px" }}>
          <label style={{ display: "block", marginBottom: "5px" }}>Title:</label>
          <input
            type="text"
            name="title"
            value={form.title}
            onChange={handleChange}
            required
            style={{ width: "100%", padding: "8px" }}
          />
        </div>
        <div style={{ marginBottom: "15px" }}>
          <label style={{ display: "block", marginBottom: "5px" }}>Description:</label>
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            style={{ width: "100%", padding: "8px", minHeight: "100px" }}
          />
        </div>
        <div style={{ marginBottom: "15px" }}>
          <label style={{ display: "block", marginBottom: "5px" }}>PDF File:</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            required
          />
        </div>
        <button type="submit" style={{ padding: "10px 15px" }}>
          Create Assignment
        </button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {success && <p style={{ color: "green" }}>{success}</p>}
    </div>
  );
};

export default CreateAssignment;
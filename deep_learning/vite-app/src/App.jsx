// import { useState, useRef } from 'react';
// import Webcam from 'react-webcam';
// import './App.css';

// function App() {
//     const [name, setName] = useState(''); 
//     const [studentDetails, setStudentDetails] = useState(null); 
//     const [attendanceUpdated, setAttendanceUpdated] = useState(null); 
//     const webcamRef = useRef(null); 

//     const captureImage = async () => {
//         const imageSrc = webcamRef.current.getScreenshot(); 
//         if (imageSrc) {
//             try {
//                 const response = await fetch('http://127.0.0.1:5000/upload', {
//                     method: 'POST',
//                     headers: {
//                         'Content-Type': 'application/json',
//                     },
//                     body: JSON.stringify({ image: imageSrc }), 
//                 });

//                 if (!response.ok) {
//                     throw new Error(`HTTP error! status: ${response.status}`);
//                 }

//                 const data = await response.json();
//                 console.log(data); 
//                 setName(data.name || 'No message returned from the backend'); 
                
                
//                 if (data.name) {
//                     const nameResponse = await fetch('http://localhost:5000/getStudentDetails', {
//                         method: 'POST',
//                         headers: {
//                             'Content-Type': 'application/json',
//                         },
//                         body: JSON.stringify({ name: data.name }), 
//                     });

//                     if (!nameResponse.ok) {
//                         throw new Error(`HTTP error! status: ${nameResponse.status}`);
//                     }

//                     const nameData = await nameResponse.json();
//                     console.log(nameData); 
                    
                    
//                     setStudentDetails(nameData.student);

                    
//                     setAttendanceUpdated(nameData.attend);
//                 }
                
//             } catch (error) {
//                 console.error('Error uploading image:', error);
//                 setName(`Error: ${error.message}`); 
//             }
//         }
//     };

//     return (

//         <div className="App">
            
//             <h2 className='h2'>Attendance tracking system</h2>
//             <div className='flex'>
//             <Webcam 
//                 audio={false} 
//                 ref={webcamRef} 
//                 screenshotFormat="image/jpeg" 
//                 width={400}
//                 className='cam'
//             />

//             <br></br>
//             </div>
//             <button className='btn'  onClick={captureImage}>Mark attendance </button>
//             <br></br>
            
//             <div className='sd'>
//                 <div className='detail'>
                
               
//                 {studentDetails && (
//                     <div>
//                     {studentDetails.name === "jeffrin" ? (
//   <div>
//     <img src='/assets/Jeffrin.jpeg' alt="Jeffrin" style={{width:'200px',height:'200px'}} />
//   </div>
// ) : (
//   <div>
//     <img src='/assets/Prrapti.jpg'style={{width:'200px',height:'200px'}} alt="Default" />
//   </div>
// )}

//                         <h2>Student Details</h2>
//                         <p><strong>Name:</strong> {studentDetails.name}</p>
//                         <p><strong>Department:</strong> {studentDetails.department}</p>
//                         <p><strong>Section:</strong> {studentDetails.section}</p>
//                         <p><strong>Date of Birth:</strong> {new Date(studentDetails.date_of_birth).toLocaleDateString()}</p>
//                         <p><strong>Attendance Count:</strong> {studentDetails.attendance_count}</p>
//                         <p><strong>Academic Performance:</strong> {studentDetails.academic_performance}</p>
//                         <p><strong>Attendance Updated:</strong> {attendanceUpdated}</p> {/* Display if attendance was updated */}
//                     </div>
//                 ) }
//                 </div>
//             </div>
            
//         </div>
//     );
// }

// export default App;



// import React from "react";
// import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
// import Login from "./components/Login";
// import StudentDashboard from "./components/StudentDashboard";
// import StaffDashboard from "./components/StaffDashboard";

// function App() {
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<Login />} />
//         <Route path="/student" element={<StudentDashboard />} />
//         <Route path="/staff" element={<StaffDashboard />} />
//         <Route path="*" element={<Navigate to="/" />} />
//       </Routes>
//     </Router>
//   );
// }

// export default App;


// import React from "react";
// import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
// import Login from "./components/Login";
// import StudentDashboard from "./components/StudentDashboard";
// import StaffDashboard from "./components/StaffDashboard";

// function App() {
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<Login />} />
//         <Route path="/student" element={<StudentDashboard />} />
//         <Route path="/staff" element={<StaffDashboard />} />
//         <Route path="*" element={<Navigate to="/" />} />
//       </Routes>
//     </Router>
//   );
// }

// export default App;



import React from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Login from "./components/Login";
import StudentDashboard from "./components/StudentDashboard";
import StaffDashboard from "./components/StaffDashboard";
import StaffAssignments from "./components/assignment";
import StudentAssignments from "./components/StudentAssignment";
import CreateAssignment from "./components/CreateAssignment";
import AssignmentSubmissions from "./components/assignmentsubmission";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/assignments" element={<StudentAssignments />} />
        <Route path="/staff" element={<StaffDashboard />} />
        <Route path="/staff/assignments" element={<StaffAssignments />} />
        <Route path="/staff/assignments/create" element={<CreateAssignment />} />
        <Route path="/staff/assignments/:id/submissions" element={<AssignmentSubmissions />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;

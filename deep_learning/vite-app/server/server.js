// import express from 'express';
// import cors from 'cors';
// import pg from 'pg';
// import bcrypt from 'bcrypt';
// import multer from 'multer';

// const app = express();
// const port = 5000;
// let attend =""
// app.use(cors());
// app.use(express.json());


// const pool = new pg.Pool({
//     user: 'postgres', 
//     host: 'localhost',
//     database: 'jaff', 
//     password: 'root', 
//     port: 5432,
// });

// const storage = multer.memoryStorage();
// const upload = multer({ storage });

// const lastUpdateTimes = {}; 

// const ONE_MINUTE = 15 * 1000;; 


// app.post("/api/login", async (req, res) => {
//   const { email, password } = req.body;

//   try {
//     const result = await pool.query(
//       "SELECT * FROM userLogin WHERE email = $1",
//       [email]
//     );

//     if (result.rows.length === 0) {
//       return res.status(401).json({ message: "User not found" });
//     }

//     const user = result.rows[0];

//     // 🔐 Compare entered password with hashed password from DB
//     const isMatch = await bcrypt.compare(password, user.password);
//     if (!isMatch) {
//       return res.status(401).json({ message: "Incorrect password" });
//     }

//     // ✅ Successful login
//     return res.status(200).json({ role: user.role, username: user.username });
//   } catch (err) {
//     console.error("Login error", err);
//     res.status(500).json({ message: "Server error" });
//   }
// });

// app.post('/getStudentDetails', async (req, res) => {
//     const name = req.body.name.trim(); 
//     let names;
//     console.log(name);
    
//     if (name === "Jeffrin.") {
//         names = "jeffrin"; 
//     } else {
//         names = "Prrapti"; 
//     }
//     console.log(names);
//     console.log('Request body:', req.body);

//     const currentTime = Date.now(); 

//     try {
       
//         if (lastUpdateTimes[names]) {
//             const lastUpdateTime = lastUpdateTimes[names];
            

            
//             if (currentTime - lastUpdateTime < ONE_MINUTE) {
//                 console.log('Attendance count not updated; last update was within 1 minute');
//                 attend = "already marked"
//             } else {
                
//                 const updateQuery = 'UPDATE students SET attendance_count = attendance_count + 1 WHERE name = $1';
//                 attend = "attendace marked"
//                 await pool.query(updateQuery, [names]); 
//                 lastUpdateTimes[names] = currentTime; 
//                 console.log('Attendance count updated for', names);
//             }
//         } else {
            
//             const updateQuery = 'UPDATE students SET attendance_count = attendance_count + 1 WHERE name = $1';
//             attend = "attendace marked"
//             await pool.query(updateQuery, [names]); 
//             lastUpdateTimes[names] = currentTime; 
//             console.log('Attendance count updated for', names);
//         }

   
//         const selectQuery = 'SELECT * FROM students WHERE name = $1'; 
//         const result = await pool.query(selectQuery, [names]);
//         console.log('Query result:', result.rows);

//         if (result.rows.length > 0) {
//             console.log('Student found:', result.rows[0]);
//             console.log(attend)
//             res.json({
//                 student: result.rows[0],
//                 attend: attend
//             });
//         } else {
//             res.status(404).json({ error: 'Student not found' });
//         }
//     } catch (error) {
//         console.error('Database query error:', error);
//         res.status(500).json({ error: 'Internal Server Error' });
//     }
// });

// app.listen(port, () => {
//     console.log(`Second backend is running on http://localhost:${port}`);
// });



import express from 'express';
import cors from 'cors';
import pg from 'pg';
import bcrypt from 'bcrypt';
import multer from 'multer';

const app = express();
const port = 5000;

app.use(cors());
app.use(express.json());

const pool = new pg.Pool({
    user: 'postgres', 
    host: 'localhost',
    database: 'jaff', 
    password: 'root', 
    port: 5432,
});

const storage = multer.memoryStorage();
const upload = multer({ storage });

// Login endpoint
app.post("/api/login", async (req, res) => {
  const { email, password } = req.body;

  try {
    const result = await pool.query(
      "SELECT * FROM usersLogin WHERE email = $1",
      [email]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ message: "User not found" });
    }

    const user = result.rows[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: "Incorrect password" });
    }

    return res.status(200).json({ 
      role: user.role, 
      username: user.username,
      userId: user.id 
    });
  } catch (err) {
    console.error("Login error", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Get students for staff
app.get("/api/students/:staffId", async (req, res) => {
  try {
    const { staffId } = req.params;
    const result = await pool.query(
      "SELECT id, username, email FROM usersLogin WHERE staff_id = $1 AND role = 'student'",
      [staffId]
    );
    res.status(200).json(result.rows);
  } catch (err) {
    console.error("Error fetching students", err);
    res.status(500).json({ message: "Server error" });
  }
});
app.post("/api/assignments", upload.single('pdf'), async (req, res) => {
  try {
    const { title, description, staffId } = req.body;
    const pdfData = req.file.buffer;
    const pdfName = req.file.originalname;

    // Verify the staff exists
    const staffCheck = await pool.query(
      "SELECT id FROM userslogin WHERE id = $1 AND role = 'staff'",
      [staffId]
    );
    
    if (staffCheck.rows.length === 0) {
      return res.status(400).json({ message: "Invalid staff member" });
    }

    // Insert assignment
    const assignmentResult = await pool.query(
      "INSERT INTO assignments (title, description, pdf_data, pdf_name, staff_id) VALUES ($1, $2, $3, $4, $5) RETURNING id",
      [title, description, pdfData, pdfName, staffId]
    );
    
    const assignmentId = assignmentResult.rows[0].id;

    // Get ONLY students assigned to this specific staff
    const students = await pool.query(
      "SELECT id FROM userslogin WHERE staff_id = $1 AND role = 'student'",
      [staffId]
    );

    // Assign to each of these students
    for (const student of students.rows) {
      await pool.query(
        "INSERT INTO student_assignments (assignment_id, student_id) VALUES ($1, $2)",
        [assignmentId, student.id]
      );
    }

    res.status(201).json({ 
      message: "Assignment created and distributed successfully",
      assignedStudents: students.rows.length
    });
  } catch (err) {
    console.error("Error creating assignment", err);
    res.status(500).json({ message: "Server error" });
  }
});
// Get assignments for staff
app.get("/api/assignments/staff/:staffId", async (req, res) => {
  try {
    const { staffId } = req.params;
    const result = await pool.query(
      "SELECT id, title, description, created_at FROM assignments WHERE staff_id = $1 ORDER BY created_at DESC",
      [staffId]
    );
    res.status(200).json(result.rows);
  } catch (err) {
    console.error("Error fetching assignments", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Get assignments for student
app.get("/api/assignments/student/:studentId", async (req, res) => {
  try {
    const { studentId } = req.params;
    const result = await pool.query(
      `SELECT a.id, a.title, a.description, a.created_at, 
       sa.submitted, sa.grade, sa.feedback
       FROM assignments a
       JOIN student_assignments sa ON a.id = sa.assignment_id
       WHERE sa.student_id = $1
       ORDER BY a.created_at DESC`,
      [studentId]
    );
    res.status(200).json(result.rows);
  } catch (err) {
    console.error("Error fetching student assignments", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Download assignment PDF
app.get("/api/assignments/:id/pdf", async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(
      "SELECT pdf_data, pdf_name FROM assignments WHERE id = $1",
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ message: "Assignment not found" });
    }

    const { pdf_data, pdf_name } = result.rows[0];
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=${pdf_name}`);
    res.send(pdf_data);
  } catch (err) {
    console.error("Error downloading assignment", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Submit assignment (student)
app.post("/api/assignments/:id/submit", upload.single('pdf'), async (req, res) => {
  try {
    const { id } = req.params;
    const { studentId } = req.body;
    const pdfData = req.file.buffer;
    const pdfName = req.file.originalname;

    await pool.query(
      `UPDATE student_assignments 
       SET submitted = TRUE, submission_data = $1, submission_name = $2, submitted_at = NOW()
       WHERE assignment_id = $3 AND student_id = $4`,
      [pdfData, pdfName, id, studentId]
    );

    res.status(200).json({ message: "Assignment submitted successfully" });
  } catch (err) {
    console.error("Error submitting assignment", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Get submissions for an assignment (staff)
app.get("/api/assignments/:id/submissions", async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(
      `SELECT u.id as student_id, u.username, u.email, 
       sa.submitted, sa.submitted_at, sa.grade, sa.feedback
       FROM student_assignments sa
       JOIN usersLogin u ON sa.student_id = u.id
       WHERE sa.assignment_id = $1`,
      [id]
    );
    res.status(200).json(result.rows);
  } catch (err) {
    console.error("Error fetching submissions", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Grade assignment (staff)
app.post("/api/assignments/:id/grade", async (req, res) => {
  try {
    const { id } = req.params;
    const { studentId, grade, feedback } = req.body;

    await pool.query(
      `UPDATE student_assignments 
       SET grade = $1, feedback = $2
       WHERE assignment_id = $3 AND student_id = $4`,
      [grade, feedback, id, studentId]
    );

    res.status(200).json({ message: "Grade submitted successfully" });
  } catch (err) {
    console.error("Error grading assignment", err);
    res.status(500).json({ message: "Server error" });
  }
});

// Download student submission (staff)
app.get("/api/submissions/:assignmentId/:studentId/pdf", async (req, res) => {
  try {
    const { assignmentId, studentId } = req.params;
    const result = await pool.query(
      "SELECT submission_data, submission_name FROM student_assignments WHERE assignment_id = $1 AND student_id = $2",
      [assignmentId, studentId]
    );
    
    if (result.rows.length === 0 || !result.rows[0].submission_data) {
      return res.status(404).json({ message: "Submission not found" });
    }

    const { submission_data, submission_name } = result.rows[0];
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=${submission_name}`);
    res.send(submission_data);
  } catch (err) {
    console.error("Error downloading submission", err);
    res.status(500).json({ message: "Server error" });
  }
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
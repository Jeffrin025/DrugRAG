import express from 'express';
import cors from 'cors';
import pg from 'pg';
import bcrypt from 'bcrypt';
import multer from 'multer';

const app = express();
const port = 5000;
let attend =""
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

const lastUpdateTimes = {}; 

const ONE_MINUTE = 15 * 1000;; 


app.post("/api/login", async (req, res) => {
  const { email, password } = req.body;

  try {
    const result = await pool.query(
      "SELECT * FROM userLogin WHERE email = $1",
      [email]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ message: "User not found" });
    }

    const user = result.rows[0];

    // 🔐 Compare entered password with hashed password from DB
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: "Incorrect password" });
    }

    // ✅ Successful login
    return res.status(200).json({ role: user.role, username: user.username });
  } catch (err) {
    console.error("Login error", err);
    res.status(500).json({ message: "Server error" });
  }
});

app.post('/getStudentDetails', async (req, res) => {
    const name = req.body.name.trim(); 
    let names;
    console.log(name);
    
    if (name === "Jeffrin.") {
        names = "jeffrin"; 
    } else {
        names = "Prrapti"; 
    }
    console.log(names);
    console.log('Request body:', req.body);

    const currentTime = Date.now(); 

    try {
       
        if (lastUpdateTimes[names]) {
            const lastUpdateTime = lastUpdateTimes[names];
            

            
            if (currentTime - lastUpdateTime < ONE_MINUTE) {
                console.log('Attendance count not updated; last update was within 1 minute');
                attend = "already marked"
            } else {
                
                const updateQuery = 'UPDATE students SET attendance_count = attendance_count + 1 WHERE name = $1';
                attend = "attendace marked"
                await pool.query(updateQuery, [names]); 
                lastUpdateTimes[names] = currentTime; 
                console.log('Attendance count updated for', names);
            }
        } else {
            
            const updateQuery = 'UPDATE students SET attendance_count = attendance_count + 1 WHERE name = $1';
            attend = "attendace marked"
            await pool.query(updateQuery, [names]); 
            lastUpdateTimes[names] = currentTime; 
            console.log('Attendance count updated for', names);
        }

   
        const selectQuery = 'SELECT * FROM students WHERE name = $1'; 
        const result = await pool.query(selectQuery, [names]);
        console.log('Query result:', result.rows);

        if (result.rows.length > 0) {
            console.log('Student found:', result.rows[0]);
            console.log(attend)
            res.json({
                student: result.rows[0],
                attend: attend
            });
        } else {
            res.status(404).json({ error: 'Student not found' });
        }
    } catch (error) {
        console.error('Database query error:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.listen(port, () => {
    console.log(`Second backend is running on http://localhost:${port}`);
});

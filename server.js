// server.js
const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const port = 3000;

// Enable CORS for React frontend
app.use(cors({
    origin: 'http://localhost:5173', // Adjust this to match your React app's URL
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type', 'multipart/form-data']
}));

// Configure multer for PDF upload
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const uploadDir = path.join(__dirname, 'uploads');
        if (!fs.existsSync(uploadDir)){
            fs.mkdirSync(uploadDir);
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        // Preserve original filename but make it unique
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.originalname.replace('.pdf', '') + '-' + uniqueSuffix + '.pdf');
    }
});

const upload = multer({
    storage: storage,
    fileFilter: function (req, file, cb) {
        // Validate file type
        if (file.mimetype !== 'application/pdf') {
            return cb(new Error('Only PDF files are allowed'), false);
        }
        cb(null, true);
    },
    limits: {
        fileSize: 10 * 1024 * 1024 // Limit file size to 10MB
    }
});

// Error handling middleware for multer
const uploadMiddleware = (req, res, next) => {
    upload.single('pdf')(req, res, (err) => {
        if (err instanceof multer.MulterError) {
            // Multer error (e.g., file too large)
            return res.status(400).json({
                status: 'error',
                message: 'File upload error',
                details: err.message
            });
        } else if (err) {
            // Other errors (e.g., wrong file type)
            return res.status(400).json({
                status: 'error',
                message: err.message
            });
        }
        next();
    });
};

// Endpoint to handle PDF upload
app.post('/upload', uploadMiddleware, async (req, res) => {
    if (!req.file) {
        return res.status(400).json({
            status: 'error',
            message: 'No file uploaded'
        });
    }

    try {
        const scriptPath = path.join(__dirname, 'scripts', 'pdf_processing.py');
        
        // Create promise to handle Python process
        const processPDF = new Promise((resolve, reject) => {
            const pythonProcess = spawn('python', [scriptPath, req.file.path]);
            
            let dataString = '';
            let errorString = '';

            pythonProcess.stdout.on('data', (data) => {
                dataString += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                errorString += data.toString();
            });

            pythonProcess.on('close', (code) => {
                // Clean up the uploaded file
                fs.unlink(req.file.path, (unlinkError) => {
                    if (unlinkError) {
                        console.error('Error deleting file:', unlinkError);
                    }
                });

                if (code !== 0) {
                    reject(new Error(errorString || 'PDF processing failed'));
                } else {
                    try {
                        const result = JSON.parse(dataString);
                        resolve(result);
                    } catch (e) {
                        resolve({ text: dataString });
                    }
                }
            });
        });

        // Wait for Python processing to complete
        const result = await processPDF;
        res.json({
            status: 'success',
            data: result,
            filename: req.file.originalname
        });

    } catch (error) {
        console.error('Processing error:', error);
        res.status(500).json({
            status: 'error',
            message: 'Failed to process PDF',
            details: error.message
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'Server is running' });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log(`Accepting requests from React app at http://localhost:5173`);
});
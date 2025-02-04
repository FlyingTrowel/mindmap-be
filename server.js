// server.js
const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const cors = require('cors');
const { MongoClient, ObjectId } = require('mongodb');

const app = express();
const port = 3000;

// Middleware to parse JSON request bodies
app.use(express.json());

// Enable CORS for React frontend
app.use(cors({
    origin: 'http://localhost:5173'
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


    const uri = 'mongodb+srv://aieman:aieman@mindmap-cluster.ur2hr.mongodb.net/?retryWrites=true&w=majority&appName=mindmap-cluster'; // Replace with your MongoDB connection string
    const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });

    app.post('/save', async (req, res) => {
        try {
        await client.connect();
        const database = client.db('mindmaps'); // Replace with your database name
        const collection = database.collection('nodes'); // Replace with your collection name

        // console.log(req);
        

        const document = { ...req.body, _id: new ObjectId() };
        const result = await collection.insertOne(document);

        res.json({
            status: 'success',
            data: { _id: result.insertedId, ...req.body }
        });
        } catch (error) {
        console.error('Save error:', error);
        res.status(500).json({
            status: 'error',
            message: 'Failed to save mindmap',
            details: error.message
        });
        } finally {
        await client.close();
        }
    });

    app.get('/mindmap/:id', async (req, res) => {
        try {
            await client.connect();
            const database = client.db('mindmaps'); // Replace with your database name
            const collection = database.collection('nodes'); // Replace with your collection name

            const mindmapId = req.params.id;
            console.log(mindmapId);
            
            const mindmap = await collection.findOne({ _id: new ObjectId(mindmapId) });

            console.log(mindmap);
            

            if (!mindmap) {
                return res.status(404).json({
                    status: 'error',
                    message: 'Mindmap not found'
                });
            }

            res.json({
                status: 'success',
                data: mindmap
            });
        } catch (error) {
            console.error('Fetch error:', error);
            res.status(500).json({
                status: 'error',
                message: 'Failed to fetch mindmap',
                details: error.message
            });
        } finally {
            await client.close();
        }
    });

    app.get('/mindmaps', async (req, res) => {
        try {
            await client.connect();
            const database = client.db('mindmaps'); // Replace with your database name
            const collection = database.collection('nodes'); // Replace with your collection name

            const mindmaps = await collection.find({}).toArray();

            res.json({
                status: 'success',
                data: mindmaps
            });
        } catch (error) {
            console.error('Fetch error:', error);
            res.status(500).json({
                status: 'error',
                message: 'Failed to fetch mindmaps',
                details: error.message
            });
        } finally {
            await client.close();
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
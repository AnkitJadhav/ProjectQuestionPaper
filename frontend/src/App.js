import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Tab,
  Tabs,
  Paper,
  Grid,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
  Divider
} from '@mui/material';
import {
  CloudUpload,
  Description,
  GetApp,
  Refresh,
  PlayArrow,
  CheckCircle,
  Error,
  Pending
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [generateDialog, setGenerateDialog] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    subject_pdfs: [],
    sample_paper_pdf: '',
    grade: '',
    total_marks: 100,
    num_questions: 10,
    subject_query: 'exam questions and topics'
  });

  // Fetch documents on load
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Poll job status
  useEffect(() => {
    const interval = setInterval(() => {
      jobs.forEach(job => {
        if (job.status === 'processing' || job.status === 'pending') {
          checkJobStatus(job.job_id);
        }
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [jobs]);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE}/documents`);
      // Handle both array and object responses
      const docs = Array.isArray(response.data) 
        ? response.data 
        : response.data.documents || [];
      setDocuments(docs);
    } catch (error) {
      showSnackbar('Failed to fetch documents', 'error');
      setDocuments([]); // Set empty array on error
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const updateDocumentType = async (docId, newType) => {
    try {
      // For now, update locally - in a full implementation, this would call the backend
      setDocuments(prev => 
        prev.map(doc => 
          doc.doc_id === docId ? { ...doc, doc_type: newType } : doc
        )
      );
      showSnackbar(`Document type updated to ${newType}`, 'success');
    } catch (error) {
      showSnackbar('Failed to update document type', 'error');
    }
  };

  // File upload with dropzone
  const onDrop = async (acceptedFiles, rejectedFiles, docType) => {
    if (rejectedFiles.length > 0) {
      showSnackbar('Only PDF files are allowed', 'error');
      return;
    }

    setUploading(true);
    
    for (const file of acceptedFiles) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('doc_type', docType);

        await axios.post(`${API_BASE}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        showSnackbar(`${file.name} uploaded successfully`, 'success');
      } catch (error) {
        showSnackbar(`Failed to upload ${file.name}`, 'error');
      }
    }

    setUploading(false);
    fetchDocuments();
  };

  const DropzoneArea = ({ docType, title, description }) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      onDrop: (accepted, rejected) => onDrop(accepted, rejected, docType),
      accept: { 'application/pdf': ['.pdf'] },
      multiple: true
    });

    return (
      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          mb: 2
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>{title}</Typography>
        <Typography variant="body2" color="textSecondary">
          {description}
        </Typography>
      </Paper>
    );
  };

  const DocumentsList = ({ documents, type }) => {
    // Ensure documents is always an array
    const docsArray = Array.isArray(documents) ? documents : [];
    const filteredDocs = docsArray.filter(doc => doc.doc_type === type);

    return (
      <List>
        {filteredDocs.map((doc) => (
          <ListItem key={doc.doc_id}>
            <ListItemIcon>
              <Description />
            </ListItemIcon>
            <ListItemText
              primary={doc.filename}
              secondary={`Uploaded: ${new Date(doc.upload_time).toLocaleDateString()}`}
            />
            <Chip
              label={doc.status}
              color={
                doc.status === 'completed' ? 'success' :
                doc.status === 'processing' ? 'warning' :
                doc.status === 'failed' ? 'error' : 'default'
              }
              size="small"
            />
          </ListItem>
        ))}
      </List>
    );
  };

  const handleGenerateOpen = () => {
    setGenerateDialog(true);
  };

  const handleGenerateClose = () => {
    setGenerateDialog(false);
  };

  const handleGenerateSubmit = async () => {
    try {
      setGenerating(true);
      
      // Debug logging
      console.log('Generate form data:', generateForm);
      
      // Format the request to match the simplified API schema
      const requestData = {
        textbook_ids: generateForm.subject_pdfs,
        sample_paper_id: generateForm.sample_paper_pdf,
        subject_query: generateForm.subject_query || ""
      };
      
      console.log('Sending request:', requestData);
      
      const response = await axios.post(`${API_BASE}/generate`, requestData);
      
      const newJob = {
        job_id: response.data.task_id || response.data.job_id || 'unknown',
        status: 'pending',
        progress: 'Starting...',
        created_at: new Date().toISOString()
      };
      
      setJobs(prev => [newJob, ...prev]);
      showSnackbar('Question paper generation started', 'success');
      setGenerateDialog(false);
      setActiveTab(2); // Switch to Jobs tab
    } catch (error) {
      console.error('Generation error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start generation';
      showSnackbar(`Failed to start generation: ${errorMessage}`, 'error');
    } finally {
      setGenerating(false);
    }
  };

  const checkJobStatus = async (jobId) => {
    try {
      const response = await axios.get(`${API_BASE}/jobs/${jobId}`);
      setJobs(prev => prev.map(job => 
        job.job_id === jobId ? { ...job, ...response.data } : job
      ));
    } catch (error) {
      console.error('Failed to check job status:', error);
    }
  };

  const downloadFile = async (jobId, fileType) => {
    try {
      const response = await axios.get(`${API_BASE}/download/${jobId}?file_type=${fileType}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `question_paper_${jobId}.${fileType === 'json' ? 'json' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      showSnackbar('Download failed', 'error');
    }
  };

  // Ensure documents is always an array before filtering
  const docsArray = Array.isArray(documents) ? documents : [];
  const completedDocs = docsArray.filter(doc => doc.status === 'completed');
  
  // Enhanced filtering to handle potential document type variations
  const textbooks = completedDocs.filter(doc => 
    doc.doc_type === 'textbook' || 
    doc.doc_type === 'book' ||
    (doc.filename && doc.filename.toLowerCase().includes('textbook'))
  );
  
  const samples = completedDocs.filter(doc => 
    doc.doc_type === 'sample' || 
    doc.doc_type === 'sample_paper' ||
    (doc.filename && (
      doc.filename.toLowerCase().includes('sample') ||
      doc.filename.toLowerCase().includes('question') ||
      doc.filename.toLowerCase().includes('exam')
    ))
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        Question Paper Generator
      </Typography>
      <Typography variant="h6" color="textSecondary" align="center" sx={{ mb: 4 }}>
        AI-powered question paper generation from your textbooks and sample papers
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Upload Documents" />
          <Tab label="Dashboard" />
          <Tab label="Generate Papers" />
        </Tabs>
      </Box>

      {/* Upload Tab */}
      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <DropzoneArea
              docType="textbook"
              title="Upload Textbooks"
              description="Drop your textbook PDFs here or click to browse"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <DropzoneArea
              docType="sample"
              title="Upload Sample Papers"
              description="Drop your sample paper PDFs here or click to browse"
            />
          </Grid>
        </Grid>
        
        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="body2" sx={{ mt: 1 }}>Uploading...</Typography>
          </Box>
        )}
      </TabPanel>

      {/* Dashboard Tab */}
      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Textbooks ({textbooks.length})
                </Typography>
                <DocumentsList documents={documents} type="textbook" />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Sample Papers ({samples.length})
                </Typography>
                <DocumentsList documents={documents} type="sample" />
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Document Type Correction Section */}
        {docsArray.length > 0 && (
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📝 Document Type Manager
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                If documents are categorized incorrectly, you can manually assign them to the correct type:
              </Typography>
              
              <List>
                {docsArray.map((doc) => (
                  <ListItem key={doc.doc_id} divider>
                    <ListItemIcon>
                      <Description />
                    </ListItemIcon>
                    <ListItemText
                      primary={doc.filename}
                      secondary={`Current: ${doc.doc_type} | Status: ${doc.status}`}
                    />
                    <Box sx={{ ml: 2 }}>
                      <Button
                        size="small"
                        variant={doc.doc_type === 'textbook' ? 'contained' : 'outlined'}
                        onClick={() => updateDocumentType(doc.doc_id, 'textbook')}
                        sx={{ mr: 1 }}
                      >
                        Textbook
                      </Button>
                      <Button
                        size="small"
                        variant={doc.doc_type === 'sample' ? 'contained' : 'outlined'}
                        onClick={() => updateDocumentType(doc.doc_id, 'sample')}
                      >
                        Sample
                      </Button>
                    </Box>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        )}

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchDocuments}
          >
            Refresh
          </Button>
        </Box>
      </TabPanel>

      {/* Generate Tab */}
      <TabPanel value={activeTab} index={2}>
        <Box sx={{ mb: 3 }}>
          {/* Debug Information */}
          <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              📊 Document Status:
            </Typography>
            <Typography variant="body2">
              • Total Documents: {docsArray.length}
            </Typography>
            <Typography variant="body2">
              • Completed Documents: {completedDocs.length}
            </Typography>
            <Typography variant="body2" color={textbooks.length > 0 ? 'success.main' : 'error.main'}>
              • Textbooks Ready: {textbooks.length} (Types: {docsArray.filter(d => d.doc_type === 'textbook').map(d => d.status).join(', ')})
            </Typography>
            <Typography variant="body2" color={samples.length > 0 ? 'success.main' : 'error.main'}>
              • Sample Papers Ready: {samples.length} (Types: {docsArray.filter(d => d.doc_type === 'sample').map(d => d.status).join(', ')})
            </Typography>
            {docsArray.length > 0 && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                📋 All Document Types: {[...new Set(docsArray.map(d => d.doc_type))].join(', ')}
              </Typography>
            )}
          </Box>

          <Button
            variant="contained"
            size="large"
            startIcon={<PlayArrow />}
            onClick={handleGenerateOpen}
            disabled={textbooks.length === 0 || samples.length === 0}
          >
            Generate Question Paper
          </Button>
          {(textbooks.length === 0 || samples.length === 0) && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              You need at least one textbook and one sample paper to generate questions
              {textbooks.length === 0 && ' (No completed textbooks found)'}
              {samples.length === 0 && ' (No completed sample papers found)'}
            </Typography>
          )}
        </Box>

        <Typography variant="h6" gutterBottom>Recent Jobs</Typography>
        <List>
          {(jobs || []).filter(job => job && job.job_id).map((job) => (
            <ListItem key={job.job_id}>
              <ListItemIcon>
                {job.status === 'completed' ? (
                  <CheckCircle color="success" />
                ) : job.status === 'failed' ? (
                  <Error color="error" />
                ) : (
                  <Pending color="warning" />
                )}
              </ListItemIcon>
              <ListItemText
                primary={`Job ${job.job_id.slice(0, 8)}...`}
                secondary={
                  <Box>
                    <Typography variant="body2">
                      Status: {job.status}
                    </Typography>
                    {job.progress && (
                      <Typography variant="body2" color="textSecondary">
                        {job.progress}
                      </Typography>
                    )}
                    {job.status === 'processing' && <LinearProgress sx={{ mt: 1 }} />}
                  </Box>
                }
              />
              {job.status === 'completed' && (
                <Box>
                  <Button
                    size="small"
                    startIcon={<GetApp />}
                    onClick={() => downloadFile(job.job_id, 'pdf')}
                    sx={{ mr: 1 }}
                  >
                    PDF
                  </Button>
                  <Button
                    size="small"
                    startIcon={<GetApp />}
                    onClick={() => downloadFile(job.job_id, 'json')}
                  >
                    JSON
                  </Button>
                </Box>
              )}
            </ListItem>
          ))}
          {(!jobs || jobs.length === 0) && (
            <ListItem>
              <ListItemText
                primary="No jobs yet"
                secondary="Generate your first question paper to see job history"
              />
            </ListItem>
          )}
        </List>
      </TabPanel>

      {/* Generate Dialog */}
      <Dialog open={generateDialog} onClose={handleGenerateClose} maxWidth="md" fullWidth>
        <DialogTitle>Generate Question Paper</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Subject Textbooks</InputLabel>
              <Select
                multiple
                value={generateForm.subject_pdfs}
                onChange={(e) => setGenerateForm({ ...generateForm, subject_pdfs: e.target.value })}
                input={<OutlinedInput label="Subject Textbooks" />}
              >
                {textbooks.map((doc) => (
                  <MenuItem key={doc.doc_id} value={doc.doc_id}>
                    {doc.filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Sample Paper</InputLabel>
              <Select
                value={generateForm.sample_paper_pdf}
                onChange={(e) => setGenerateForm({ ...generateForm, sample_paper_pdf: e.target.value })}
                label="Sample Paper"
              >
                {samples.map((doc) => (
                  <MenuItem key={doc.doc_id} value={doc.doc_id}>
                    {doc.filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Special Instructions (Optional)"
              multiline
              rows={3}
              value={generateForm.subject_query}
              onChange={(e) => setGenerateForm({ ...generateForm, subject_query: e.target.value })}
              placeholder="e.g., Focus on organic chemistry, include more numerical problems, emphasize practical applications, avoid questions from Chapter 5, etc."
              helperText="Provide any specific instructions for question selection, topics to focus on, or areas to avoid"
              sx={{ mb: 2 }}
            />

            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.main', color: 'info.contrastText', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                📋 How It Works:
              </Typography>
              <Typography variant="body2">
                • The system will automatically copy the structure (marks, time, format) from your selected sample paper
              </Typography>
              <Typography variant="body2">
                • New questions will be generated from the textbook content while preserving the exact paper format
              </Typography>
              <Typography variant="body2">
                • Question difficulty and types will match the original sample paper's distribution
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleGenerateClose}>Cancel</Button>
          <Button
            onClick={handleGenerateSubmit}
            variant="contained"
            disabled={generating || !generateForm.subject_pdfs?.length || !generateForm.sample_paper_pdf}
          >
            {generating ? 'Generating Question Paper...' : 'Generate Question Paper'}
          </Button>
          {(!generateForm.subject_pdfs?.length || !generateForm.sample_paper_pdf) && (
            <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
              Please select at least one textbook and one sample paper
            </Typography>
          )}
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default App; 
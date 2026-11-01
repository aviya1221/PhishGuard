const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {

  async uploadFile(endpoint, file, language = 'en', signal) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      body: formData,
      signal,
    });
    if (!response.ok) {
      const error = new Error(`HTTP error! status: ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return response.json();
  }

  // Add other methods as needed (GET, POST, PUT, DELETE, etc.)
}

export default new ApiService();
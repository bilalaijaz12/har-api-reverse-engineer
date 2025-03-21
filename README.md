# HAR API Reverse Engineer

A tool to analyze HAR files and extract API requests with the help of LLMs.

## Features

- Upload HAR files (HTTP Archive format)
- Find specific API requests using natural language descriptions
- Generate curl commands for the identified API requests
- Test API requests directly from the UI
- Generate equivalent Python and JavaScript code
- Get detailed API documentation including parameters and authentication

## Project Structure

- `/backend` - FastAPI backend server
- `/frontend` - Next.js frontend application with Tailwind CSS and shadcn/ui

## Requirements

### Backend
- Python 3.11+
- FastAPI
- OpenAI API key

### Frontend
- Node.js 18+
- Next.js 15+
- React 19+

## Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend

2. Create a Conda environment from the environment.yml file:
    ```bash
    conda env create -f environment.yml

3. Activate the environment:
    ```bash
    conda activate har-api-env

4. Create a .env file based on the .env.template

5. Add your OpenAI API key to the .env file

6. Start the backend server via "python main.py" or "make run"

### Frontend Setup

1. Navigate to the frontend directory:
   cd frontend

2. Install yarn dependencies:
   yarn

3. Start development server:
   yarn dev

##Usage

-Upload a HAR file: Drag and drop or select a HAR file to upload
-Describe the API: Enter a natural language description of the API you're looking for
-View results: See the generated curl command and API details
-Test API: Execute the API request directly from the UI
-View code: Switch between curl, Python, and JavaScript code formats

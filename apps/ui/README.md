# FileCherry UI

Next.js web interface for FileCherry appliance.

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The UI runs on `http://localhost:3000` and communicates with the orchestrator on `http://localhost:8000`.

## Environment Variables

- `ORCHESTRATOR_URL` - URL of the orchestrator API (default: `http://localhost:8000`)

## Features

- **Intro Screen**: File inventory display and intent input
- **Plan Preview**: Review and edit LLM-generated plans
- **Job Progress**: Real-time job execution monitoring
- **Completion Screen**: Results summary and file browser


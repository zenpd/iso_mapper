# ISO 20022 Migration Platform - Frontend

Modern React + TypeScript frontend for the ISO 20022 GenAI Migration Platform.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Icons**: Lucide React

## Structure

```
src/
├── components/
│   ├── common/           # Reusable components (Button, Card, etc.)
│   ├── layout/          # Layout components (Header, AppShell)
│   ├── forms/           # Form components (MTInputForm, etc.)
│   └── results/         # Result display components
├── pages/               # Page components (TransformPage, etc.)
├── services/            # API client service
├── store/               # Zustand state management
├── types/               # TypeScript type definitions
├── hooks/               # Custom React hooks
├── App.tsx              # Main App component
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Build

```bash
npm run build
npm run preview
```

## Architecture

### Components

Components are organized by feature:

- **Common Components**: Button, Card, LoadingSpinner - used across pages
- **Layout Components**: Header, AppShell - shared layout
- **Form Components**: Input forms for user interaction
- **Result Components**: Display transformation results

### State Management

Zustand store for transformation state:
- Input MT message
- Selected approach
- Loading state
- Results
- Errors

### API Integration

Axios-based API client (`src/services/api.ts`):
- `transform()` - Transform MT to MX
- `getSamples()` - Get sample messages
- `getHealth()` - Health check
- `getConfig()` - Get configuration

## Environment Variables

```
VITE_API_URL=http://localhost:8000
```

## Styling

Uses Tailwind CSS with custom configuration:
- Responsive design (mobile-first)
- Dark mode ready (configurable)
- Custom color palette
- Smooth animations

## Pages

### Transform Page
- Input MT message
- Select transformation approach
- Display results with statistics
- Copy XML output

### Samples Page
- Browse sample MT messages
- Use samples for testing
- Copy sample messages

### Analytics Page
- View platform configuration
- Display system statistics
- About information

## Features

- ✅ Real-time transformation with live feedback
- ✅ Sample messages for testing
- ✅ Result statistics and metrics
- ✅ XML and JSON output display
- ✅ Copy-to-clipboard functionality
- ✅ Responsive design
- ✅ Error handling with user-friendly messages
- ✅ Loading states and animations

## Testing

```bash
# Type checking
npm run type-check

# Linting (when configured)
npm run lint
```

## Building for Production

```bash
npm run build
```

Build output is in `dist/` directory.

## Deployment

The built frontend can be served by:
- Any static file server (Nginx, Apache)
- Node.js static server
- CDN (CloudFront, CloudFlare)
- Docker container

Example Docker deployment:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## Integration with Backend

The frontend proxies API requests to the backend during development via Vite configuration:
- `/api/*` → `http://localhost:8000`
- `/health` → `http://localhost:8000`
- `/config` → `http://localhost:8000`

For production, update the `VITE_API_URL` environment variable.

## References

- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Vite Guide](https://vitejs.dev/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [Zustand Docs](https://github.com/pmndrs/zustand)

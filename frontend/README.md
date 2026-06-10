# Frontend - React + TypeScript Application

## 📁 Folder Structure

```
frontend/
├── src/                    # Source code
│   ├── components/        # Reusable UI components
│   │   ├── __tests__/     # Component unit tests
│   │   │   ├── Badge.test.tsx
│   │   │   ├── EmptyState.test.tsx
│   │   │   ├── FormattedCurrency.test.tsx
│   │   │   ├── StatsCard.test.tsx
│   │   │   └── StatusBadge.test.tsx
│   │   ├── Badge.tsx              # Badge component for status indicators
│   │   ├── ConfirmModal.tsx       # Confirmation modal dialog
│   │   ├── EmptyState.tsx         # Empty state placeholder
│   │   ├── ErrorBoundary.tsx      # Error boundary wrapper
│   │   ├── FormattedCurrency.tsx  # Currency formatting component
│   │   ├── FormattedDate.tsx      # Date formatting component
│   │   ├── KeyboardShortcut.tsx   # Keyboard shortcut helper
│   │   ├── Layout.tsx             # Main application layout
│   │   ├── LazyImage.tsx          # Lazy-loaded image component
│   │   ├── ProtectedRoute.tsx     # Route protection wrapper
│   │   ├── StatsCard.tsx          # Statistics card component
│   │   ├── StatusBadge.tsx        # Status badge component
│   │   └── Tooltip.tsx            # Tooltip component
│   ├── contexts/          # React Context providers
│   │   ├── AuthContext.tsx          # Authentication context
│   │   ├── ProcurementContext.tsx   # Procurement data context
│   │   └── ToastContext.tsx         # Toast notification context
│   ├── hooks/             # Custom React hooks
│   │   ├── index.ts               # Hook exports
│   │   ├── useDebounce.ts         # Debounce hook
│   │   ├── useKeyboardShortcut.ts # Keyboard shortcut hook
│   │   └── useLocalStorage.ts     # LocalStorage hook
│   ├── pages/             # Page components (route-level)
│   │   ├── admin/                 # Admin-specific pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── PODetail.tsx       # Purchase Order detail
│   │   │   └── PRDetail.tsx       # Purchase Requisition detail
│   │   ├── requester/             # Requester-specific pages
│   │   │   └── ... (requester pages)
│   │   ├── Login.tsx              # Login page
│   │   └── Register.tsx           # Registration page
│   ├── services/          # API service layer
│   │   ├── api.ts                 # API client configuration
│   │   └── auth.ts                # Authentication service
│   ├── styles/            # CSS stylesheets (modular)
│   │   ├── base.css               # Base styles
│   │   ├── buttons.css            # Button styles
│   │   ├── cards.css              # Card component styles
│   │   ├── feedback.css           # Feedback/notification styles
│   │   ├── forms.css              # Form styles
│   │   ├── layout.css             # Layout styles
│   │   ├── navbar.css             # Navigation bar styles
│   │   ├── responsive.css         # Responsive design styles
│   │   ├── tables.css             # Table styles
│   │   └── utilities.css          # Utility classes
│   ├── types/             # TypeScript type definitions
│   │   └── index.ts               # Shared type definitions
│   ├── assets/            # Static assets
│   │   ├── hero.png               # Hero image
│   │   ├── react.svg              # React logo
│   │   └── vite.svg               # Vite logo
│   ├── test/              # Test configuration
│   │   └── setup.ts               # Vitest setup file
│   ├── App.tsx            # Main application component
│   ├── App.css            # App-specific styles
│   ├── main.tsx           # Application entry point
│   └── index.css          # Global styles
├── public/                # Public static files
│   ├── favicon.svg        # Favicon
│   └── icons.svg          # Icon sprites
├── coverage/              # Test coverage reports (not tracked by git)
├── dist/                  # Production build output (not tracked by git)
├── node_modules/          # Dependencies (not tracked by git)
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore rules for frontend
├── Dockerfile             # Production Docker build
├── Dockerfile.dev         # Development Docker build
├── eslint.config.js       # ESLint configuration
├── index.html             # HTML entry point
├── nginx.conf             # Nginx configuration for production
├── package.json           # Project dependencies and scripts
├── package-lock.json      # Dependency lock file
├── tsconfig.json          # TypeScript configuration
├── tsconfig.app.json      # TypeScript app configuration
├── tsconfig.node.json     # TypeScript node configuration
├── vite.config.ts         # Vite build configuration
└── vitest.config.ts       # Vitest test configuration
```

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to `http://localhost:5173`

### Building for Production

```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

### Running Tests

```bash
# Run all tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Linting

```bash
# Check for linting issues
npm run lint

# Fix auto-fixable issues
npm run lint:fix
```

## 📋 Key Technologies

- **React 18**: UI library with hooks and functional components
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Vitest**: Fast unit testing framework
- **Testing Library**: React component testing utilities
- **ESLint**: Code linting and quality
- **Tailwind-like CSS**: Modular CSS architecture

## 🎨 Architecture Patterns

### Component Organization
- **Components**: Small, reusable UI elements
- **Pages**: Route-level components that compose multiple components
- **Contexts**: Global state management using React Context API
- **Hooks**: Reusable logic extracted from components
- **Services**: API communication layer

### State Management
- **Local State**: `useState` for component-specific state
- **Context API**: `AuthContext`, `ProcurementContext`, `ToastContext` for global state
- **Custom Hooks**: Encapsulate reusable stateful logic

### Styling Approach
- Modular CSS files organized by component/purpose
- No CSS-in-JS or preprocessors (plain CSS)
- Responsive design with mobile-first approach

## 🔐 Environment Variables

Required environment variables (see `.env.example`):

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Procurement System
```

**Note:** All environment variables must be prefixed with `VITE_` to be accessible in the client.

## 🧪 Testing Strategy

### Unit Tests
- Test individual components in isolation
- Use Vitest + Testing Library
- Mock API calls and external dependencies
- Focus on user interactions and rendering

### Test File Location
- Tests are colocated with components in `__tests__/` folders
- Test files follow naming convention: `ComponentName.test.tsx`

### Coverage Goals
- Maintain test coverage above 80%
- Focus on critical paths and user-facing features

## 📝 Code Conventions

- Use TypeScript for all new files
- Follow functional component pattern with hooks
- Use meaningful, descriptive names for components and functions
- Keep components small and focused (single responsibility)
- Write JSDoc comments for complex functions
- Use async/await for asynchronous operations
- Implement proper error handling

## 🐳 Docker

### Development
```bash
docker build -f Dockerfile.dev -t frontend-dev .
docker run -p 5173:5173 frontend-dev
```

### Production
```bash
docker build -t frontend-prod .
docker run -p 80:80 frontend-prod
```

## 🚦 CI/CD Integration

The frontend is tested and built automatically via GitHub Actions:
- Linting checks
- Type checking
- Unit tests with coverage
- Production build verification

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Vitest Documentation](https://vitest.dev/)
